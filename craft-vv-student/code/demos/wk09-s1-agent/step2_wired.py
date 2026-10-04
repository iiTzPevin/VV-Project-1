"""STEP 2 -- wire the agent: driver, monitor, sequencer, analysis port.

The driver pulls items from the sequencer (get_next_item / item_done) and
drives the bus. The monitor watches the same wires from the outside and
publishes what it sees on an analysis port. A subscriber prints every
transaction that arrives -- proof the plumbing carries data before one line
of checking exists. The DUT handle travels through ConfigDB; no component
holds a hard-coded reference to anything.
"""
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, Timer
from pyuvm import (uvm_sequence_item, uvm_sequence, uvm_driver, uvm_monitor,
                   uvm_subscriber, uvm_agent, uvm_env, uvm_test, uvm_sequencer,
                   uvm_analysis_port, ConfigDB, uvm_root)

from demo_common import A_CTRL, A_STATUS, A_SCRATCH, reset, MASK


class RegItem(uvm_sequence_item):
    def __init__(self, name="RegItem"):
        super().__init__(name)
        self.we = 0          # 1 = write, 0 = read
        self.addr = 0
        self.data = 0        # wdata on a write; observed rdata on a read
        self.rvalid = 0

    def __str__(self):
        op = "WR" if self.we else "RD"
        return f"{op} a={self.addr:#x} d={self.data:#010x} rvalid={self.rvalid}"


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
            await RisingEdge(d.clk)          # transaction commits here
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
            await Timer(1, units="ns")       # settle; registered rdata valid now
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


class EchoSub(uvm_subscriber):
    """Stands where the scoreboard will: prints whatever the monitor saw."""
    def build_phase(self):
        self.n = 0

    def write(self, tr):
        self.n += 1
        cocotb.log.info(f"subscriber got #{self.n}: {tr}")


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
        self.echo = EchoSub.create("echo", self)

    def connect_phase(self):
        self.agent.monitor.ap.connect(self.echo.analysis_export)


class HelloSeq(uvm_sequence):
    """Five directed transactions -- enough to see the plumbing carry data."""
    async def body(self):
        for we, addr, data in [(1, A_CTRL, 0x11), (1, A_SCRATCH, 0x22),
                               (0, A_CTRL, 0), (0, A_SCRATCH, 0),
                               (0, A_STATUS, 0)]:
            it = RegItem("it")
            await self.start_item(it)
            it.we, it.addr, it.data = we, addr, data
            await self.finish_item(it)


class WiredTest(uvm_test):
    def build_phase(self):
        self.env = RegEnv.create("env", self)

    async def run_phase(self):
        self.raise_objection()
        await HelloSeq("hello").start(self.env.agent.seqr)
        self.drop_objection()
        cocotb.log.info(f"transactions that reached the subscriber: "
                        f"{self.env.echo.n} of 5 sent")


@cocotb.test()
async def test_wired(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset(dut)
    ConfigDB().set(None, "*", "DUT", dut)
    await uvm_root().run_test("WiredTest", keep_singletons=True)
