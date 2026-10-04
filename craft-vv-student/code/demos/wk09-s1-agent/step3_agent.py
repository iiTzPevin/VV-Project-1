"""STEP 3 -- the same stimulus as step 0, through the agent.

The subscriber grows into a scoreboard: RegfileModel as the reference, every
read compared, and the same stream digest step 0 printed. The sequence replays
step 0's exact transaction list. If the digest and the check tally match
step 0, the agent drove and observed identical traffic -- the behavior did
not change, only the structure did. That is the whole claim of UVM week.
"""
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, Timer
from pyuvm import (uvm_sequence_item, uvm_sequence, uvm_driver, uvm_monitor,
                   uvm_subscriber, uvm_agent, uvm_env, uvm_test, uvm_sequencer,
                   uvm_analysis_port, ConfigDB, uvm_root)

from models.regfile_model import RegfileModel
from demo_common import reset, seed, gen_stimulus, StreamDigest, MASK


class RegItem(uvm_sequence_item):
    def __init__(self, name="RegItem"):
        super().__init__(name)
        self.we = 0
        self.addr = 0
        self.data = 0
        self.rvalid = 0


class RegDriver(uvm_driver):
    def build_phase(self):
        self.dut = ConfigDB().get(self, "", "DUT")

    async def run_phase(self):
        d = self.dut
        d.req.value = 0
        while True:
            item = await self.seq_item_port.get_next_item()
            await FallingEdge(d.clk)
            d.req.value = 1
            d.we.value = item.we & 1
            d.addr.value = item.addr & 0xF
            d.wdata.value = (item.data & MASK) if item.we else 0
            await RisingEdge(d.clk)
            await FallingEdge(d.clk)
            d.req.value = 0
            d.we.value = 0
            self.seq_item_port.item_done()


class RegMonitor(uvm_monitor):
    def build_phase(self):
        self.dut = ConfigDB().get(self, "", "DUT")
        self.ap = uvm_analysis_port("ap", self)

    async def run_phase(self):
        d = self.dut
        while True:
            await RisingEdge(d.clk)
            await Timer(1, units="ns")
            if int(d.req.value) != 1:
                continue
            tr = RegItem("mon")
            tr.we = int(d.we.value)
            tr.addr = int(d.addr.value)
            if tr.we:
                tr.data = int(d.wdata.value)
            else:
                tr.data = int(d.rdata.value)
                tr.rvalid = int(d.rvalid.value)
            self.ap.write(tr)


class RegScoreboard(uvm_subscriber):
    """Step 2's subscriber, grown up: replay writes into the model, check
    every read, and fingerprint the observed stream."""
    def build_phase(self):
        self.model = RegfileModel()
        self.digest = StreamDigest()
        self.errors = 0
        self.n_checked = 0

    def write(self, tr):
        if tr.we:
            self.model.write(tr.addr, tr.data)
            self.digest.update(1, tr.addr, tr.data)
            return
        exp = self.model.read(tr.addr)
        self.digest.update(0, tr.addr, tr.data)
        self.n_checked += 1
        if tr.rvalid != 1:
            self.errors += 1
            self.logger.error(f"read a={tr.addr:#x}: rvalid not asserted")
        elif tr.data != exp:
            self.errors += 1
            self.logger.error(f"read a={tr.addr:#x}: "
                              f"dut={tr.data:#010x} model={exp:#010x}")


class RegAgent(uvm_agent):
    def build_phase(self):
        self.seqr = uvm_sequencer("seqr", self)
        self.driver = RegDriver.create("driver", self)
        self.monitor = RegMonitor.create("monitor", self)

    def connect_phase(self):
        self.driver.seq_item_port.connect(self.seqr.seq_item_export)


class RegEnv(uvm_env):
    def build_phase(self):
        self.agent = RegAgent.create("agent", self)
        self.sb = RegScoreboard.create("sb", self)

    def connect_phase(self):
        self.agent.monitor.ap.connect(self.sb.analysis_export)


class ReplaySeq(uvm_sequence):
    """The exact stream step 0 drove flat, expressed as a sequence."""
    async def body(self):
        for we, addr, data in gen_stimulus(ConfigDB().get(None, "", "SEED")):
            it = RegItem("it")
            await self.start_item(it)
            it.we, it.addr, it.data = we, addr, data
            await self.finish_item(it)


class AgentTest(uvm_test):
    def build_phase(self):
        self.env = RegEnv.create("env", self)

    async def run_phase(self):
        self.raise_objection()
        await ReplaySeq("replay").start(self.env.agent.seqr)
        self.drop_objection()
        sb = self.env.sb
        cocotb.log.info(f"reads checked against the model: {sb.n_checked}, "
                        f"mismatches: {sb.errors}")
        cocotb.log.info(f"stream digest = {sb.digest.hex}  "
                        f"over {sb.digest.count} transactions")
        assert sb.n_checked > 0, "scoreboard checked no reads"
        assert sb.errors == 0, f"scoreboard found {sb.errors} mismatch(es)"


@cocotb.test()
async def test_agent(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset(dut)
    ConfigDB().set(None, "*", "DUT", dut)
    ConfigDB().set(None, "*", "SEED", seed())
    await uvm_root().run_test("AgentTest", keep_singletons=True)
