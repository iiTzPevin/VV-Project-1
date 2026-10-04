"""STUDENT STARTER -- Week 9 pyuvm environment for axil_regfile.

This is the scaffolding for a UVM environment: a sequence item, a working
driver and monitor, a sequencer/agent/env, and a *stub* scoreboard.  The bus
plumbing runs, but the checking is intentionally missing -- so this starter
passes on the golden RTL yet catches almost none of the register-policy
mutants.  Your job (Week 9 lab) is to turn the stub scoreboard into a real one:

  TODO(1): give RegScoreboard a golden reference (models.regfile_model.RegfileModel),
           replay writes into it, and compare EVERY read's data against it.
  TODO(2): write sequences that actually exercise the access policies
           (RO / W1C / LOCK / SECURE) and read every register back.

There is more than one complete answer. Yours is graded on what it finds,
not on how closely it matches anyone else's.
"""
import random

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, Timer

from pyuvm import (uvm_sequence_item, uvm_sequence, uvm_driver, uvm_monitor,
                   uvm_subscriber, uvm_agent, uvm_env, uvm_test, uvm_sequencer,
                   uvm_analysis_port, ConfigDB, uvm_root)

A_CTRL, A_STATUS, A_SCRATCH, A_INTR, A_LOCK, A_SECURE = 0, 1, 2, 3, 4, 5
MASK = 0xFFFFFFFF


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
        self.dut.req.value = 0
        self.dut.we.value = 0
        self.dut.addr.value = 0
        self.dut.wdata.value = 0
        while True:
            item = await self.seq_item_port.get_next_item()
            await self._drive(item)
            self.seq_item_port.item_done()

    async def _drive(self, item):
        d = self.dut
        await FallingEdge(d.clk)
        d.req.value = 1
        d.we.value = item.we & 1
        d.addr.value = item.addr & 0xF
        d.wdata.value = (item.data & MASK) if item.we else 0
        await RisingEdge(d.clk)
        if not item.we:
            await Timer(1, units="ns")
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
                tr.rvalid = 0
            else:
                tr.data = int(d.rdata.value)
                tr.rvalid = int(d.rvalid.value)
            self.ap.write(tr)


class RegScoreboard(uvm_subscriber):
    """STUB scoreboard -- only checks that reads assert rvalid.

    TODO(1): compare read data against a RegfileModel here instead of just
    counting transactions.  Right now data/policy bugs go undetected.
    """
    def build_phase(self):
        self.errors = 0
        self.n_checked = 0
        self.n_writes = 0

    def write(self, tr):
        if tr.we:
            self.n_writes += 1
        else:
            self.n_checked += 1
            if tr.rvalid != 1:                  # minimal placeholder check
                self.errors += 1
            # TODO(1): expected = model.read(tr.addr); compare tr.data


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


class BasicSeq(uvm_sequence):
    """A few writes and reads -- does NOT target the access policies.

    TODO(2): add sequences that cover RO/W1C/LOCK/SECURE and read back.
    """
    async def body(self):
        rnd = random.Random(0x1234)
        for _ in range(20):
            it = RegItem("it")
            await self.start_item(it)
            it.we = rnd.randint(0, 1)
            it.addr = rnd.choice([A_CTRL, A_SCRATCH])   # only the easy RW regs
            it.data = rnd.getrandbits(32)
            await self.finish_item(it)


class RegfileTest(uvm_test):
    def build_phase(self):
        self.env = RegEnv.create("env", self)

    async def run_phase(self):
        self.raise_objection()
        await BasicSeq("basic").start(self.env.agent.seqr)
        self.drop_objection()
        # weak sign-off: only the placeholder rvalid check contributes
        assert self.env.sb.errors == 0, f"{self.env.sb.errors} errors"


async def _reset(dut):
    dut.req.value = 0
    dut.we.value = 0
    dut.addr.value = 0
    dut.wdata.value = 0
    dut.rst_n.value = 0
    for _ in range(3):
        await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.rst_n.value = 1


@cocotb.test()
async def test_axil_uvm(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await _reset(dut)
    ConfigDB().set(None, "*", "DUT", dut)
    await uvm_root().run_test("RegfileTest", keep_singletons=True)
