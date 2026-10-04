"""STEP 3 -- the same tests, rerun through the layers.

Nothing below the test function is new: FifoTxn, FifoDriver, FifoMonitor,
and FifoScoreboard are step 2's classes, verbatim. What changed is the test
body -- it now reads as intent: five named sequences through one stack.
Adding a scenario is adding a list. This file is the seed of HW4 and of
Project 1, and Thursday's debug session reuses it unchanged.

Same vectors, same checks -- the digest and the mutation score are the proof
that the refactor changed structure and nothing else.
"""
from dataclasses import dataclass
from typing import Optional

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge, Timer

from models.fifo_model import FifoModel
from demo_common import SEQUENCES, seed, report, WIDTH, DEPTH


@dataclass
class FifoTxn:
    """One operation the FIFO performs, named -- not four wires, an intent."""
    wr_en: int
    rd_en: int
    wr_data: int = 0


class FifoDriver:
    """Turns transactions into pin wiggles. Owns the clock and the reset --
    the two things every monolithic test re-implements."""

    def __init__(self, dut, period_ns=10):
        self.dut = dut
        cocotb.start_soon(Clock(dut.clk, period_ns, units="ns").start())

    async def reset(self):
        d = self.dut
        d.wr_en.value = 0
        d.rd_en.value = 0
        d.wr_data.value = 0
        d.rst_n.value = 0
        for _ in range(3):
            await RisingEdge(d.clk)
        d.rst_n.value = 1
        await FallingEdge(d.clk)

    async def drive(self, txn):
        d = self.dut
        d.wr_en.value = txn.wr_en
        d.rd_en.value = txn.rd_en
        d.wr_data.value = txn.wr_data
        await RisingEdge(d.clk)
        await Timer(1, units="ns")


@dataclass
class Observed:
    """What one clock cycle looked like from the pins alone."""
    cycle: int
    wr_en: int
    rd_en: int
    wr_data: int
    count: int
    full: bool
    empty: bool
    rd_data: Optional[int]     # FWFT head; None while the DUT claims empty


class FifoMonitor:
    """Watches the pins and reconstructs what happened -- independently of
    the driver. If it trusted the driver, a driver bug would hide itself."""

    def __init__(self, dut):
        self.dut = dut
        self.cycle = 0

    def capture(self):
        d = self.dut
        self.cycle += 1
        empty = bool(d.empty.value)
        return Observed(self.cycle,
                        int(d.wr_en.value), int(d.rd_en.value),
                        int(d.wr_data.value), int(d.count.value),
                        bool(d.full.value), empty,
                        None if empty else int(d.rd_data.value))


class FifoScoreboard:
    """Predicts with the reference queue, compares with what the monitor saw.
    The first divergence is logged with the cycle number before it raises --
    that line is where every debug session starts."""

    def __init__(self):
        self.model = FifoModel(WIDTH, DEPTH)
        self.checked = 0

    def update(self, obs):
        m = self.model
        m.step(obs.wr_en, obs.wr_data, obs.rd_en)
        ok = (obs.count == m.count and obs.full == m.full
              and obs.empty == m.empty
              and (m.empty or obs.rd_data == m.head))
        if not ok:
            def hx(v):
                return "--" if v is None else f"0x{v:02X}"
            cocotb.log.error(
                f"first divergence: cycle {obs.cycle} -- "
                f"count {obs.count} vs model {m.count}, "
                f"full {int(obs.full)} vs {int(m.full)}, "
                f"empty {int(obs.empty)} vs {int(m.empty)}, "
                f"rd_data {hx(obs.rd_data)} vs head {hx(m.head)} | "
                f"pins that cycle: wr_en={obs.wr_en} rd_en={obs.rd_en} "
                f"wr_data=0x{obs.wr_data:02X}")
        assert obs.count == m.count, \
            f"cycle {obs.cycle}: count {obs.count} != model {m.count}"
        assert obs.full == m.full, \
            f"cycle {obs.cycle}: full {obs.full} != model {m.full}"
        assert obs.empty == m.empty, \
            f"cycle {obs.cycle}: empty {obs.empty} != model {m.empty}"
        if not m.empty:  # FWFT: head valid only when not empty
            assert obs.rd_data == m.head, \
                f"cycle {obs.cycle}: rd_data {obs.rd_data:#04x} != head {m.head:#04x}"
        self.checked += 1


async def run_sequence(drv, mon, sb, name, seq, applied):
    for wr, rd, data in seq:
        await drv.drive(FifoTxn(wr, rd, data))
        sb.update(mon.capture())
        applied.append((wr, rd, data))
    cocotb.log.info(f"  sequence clean: {name}  "
                    f"({len(seq)} txns, {sb.checked} judged so far)")


@cocotb.test()
async def test_layered(dut):
    seed()
    drv = FifoDriver(dut)
    await drv.reset()
    mon, sb = FifoMonitor(dut), FifoScoreboard()

    applied = []
    for name, seq in SEQUENCES:
        await run_sequence(drv, mon, sb, name, seq, applied)

    report(applied)
