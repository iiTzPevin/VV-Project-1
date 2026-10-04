"""Tuesday's product, carried in whole: the pyuvm agent for axil_regfile.

Session 2 does not edit anything in this file -- that is the point. The step
files add only sequences, one driver subclass, and one factory override. If
you find yourself editing the env mid-demo, stop; the lesson is that you
should not have to.

Same classes as demos/wk09-s1-agent/step3_agent.py, with two changes made for
reuse: the driver's wire-wiggling lives in its own `_drive` method (so a
subclass can intercept it), and the scoreboard counts writes as well as reads.
"""
import os

import cocotb
from cocotb.triggers import RisingEdge, FallingEdge, Timer
from pyuvm import (uvm_sequence_item, uvm_driver, uvm_monitor, uvm_subscriber,
                   uvm_agent, uvm_env, uvm_sequencer, uvm_analysis_port,
                   ConfigDB)

from models.regfile_model import RegfileModel

# word addresses (dut/specs/axil_regfile.md)
A_CTRL, A_STATUS, A_SCRATCH, A_INTR, A_LOCK, A_SECURE = 0, 1, 2, 3, 4, 5
MASK = 0xFFFFFFFF


def seed(default=5):
    """Pin the random-burst stream. Override:  make STEP=0 DEMO_SEED=7"""
    s = int(os.environ.get("DEMO_SEED", default))
    cocotb.log.info(f"demo seed = {s}")
    return s


async def reset(dut):
    dut.req.value = 0
    dut.we.value = 0
    dut.addr.value = 0
    dut.wdata.value = 0
    dut.rst_n.value = 0
    for _ in range(3):
        await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.rst_n.value = 1


class RegItem(uvm_sequence_item):
    def __init__(self, name="RegItem"):
        super().__init__(name)
        self.we = 0          # 1 = write, 0 = read
        self.addr = 0
        self.data = 0        # wdata on a write; back-annotated rdata on a read
        self.rvalid = 0

    def __str__(self):
        op = "WR" if self.we else "RD"
        return f"{op} a={self.addr:#x} d={self.data:#010x}"


class RegDriver(uvm_driver):
    def build_phase(self):
        self.dut = ConfigDB().get(self, "", "DUT")

    async def run_phase(self):
        self.dut.req.value = 0
        while True:
            item = await self.seq_item_port.get_next_item()
            await self._drive(item)
            self.seq_item_port.item_done()

    async def _drive(self, item):
        """One bus transaction. Subclasses override THIS, nothing else."""
        d = self.dut
        await FallingEdge(d.clk)
        d.req.value = 1
        d.we.value = item.we & 1
        d.addr.value = item.addr & 0xF
        d.wdata.value = (item.data & MASK) if item.we else 0
        await RisingEdge(d.clk)              # transaction commits here
        if not item.we:
            await Timer(1, units="ns")       # registered read data settled
            item.data = int(d.rdata.value)
            item.rvalid = int(d.rvalid.value)
        await FallingEdge(d.clk)
        d.req.value = 0
        d.we.value = 0


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
    """Replays the observed stream through RegfileModel; checks every read.
    Note what it trusts: the monitor's view of the wires -- not the sequence's
    intent, and not the driver."""
    def build_phase(self):
        self.model = RegfileModel()
        self.errors = 0
        self.n_checked = 0
        self.n_writes = 0

    def write(self, tr):
        if tr.we:
            self.model.write(tr.addr, tr.data)
            self.n_writes += 1
            return
        exp = self.model.read(tr.addr)
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
