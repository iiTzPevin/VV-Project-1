"""Shared helpers for the Week 4 Session 2 demo -- and Tuesday's layers.

FifoTxn, FifoDriver, FifoMonitor, FifoScoreboard, and run_sequence are
carried over VERBATIM from demos/wk04-s1-layered-tb/step3_layers.py. That is
the point: Thursday's debug session does not rebuild the testbench, it
imports it. So are the five sequences -- the regression that failed is the
regression we ship.
"""
import hashlib
import os
import random
from dataclasses import dataclass
from typing import Optional

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge, Timer

from models.fifo_model import FifoModel

WIDTH, DEPTH = 8, 8


def seed(default=5):
    """Pin the stream so every step logs the same numbers we rehearsed.
    Override from the shell:  make STEP=3 DEMO_SEED=7
    (This week's stimulus is directed, so the seed only matters if you add
    random traffic -- but pin it anyway; Week 5 inherits the habit.)
    """
    s = int(os.environ.get("DEMO_SEED", default))
    random.seed(s)
    cocotb.log.info(f"demo seed = {s}")
    return s


# Tuesday's five sequences, (wr_en, rd_en, wr_data) per cycle -- the same
# vectors, so the digest in the report matches Session 1's ae8971e8. Same
# tests, different DUT: that is what "reproduce" costs when the testbench
# is reusable.
SEQUENCES = [
    ("first in, first out", [
        (1, 0, 0xA0), (1, 0, 0xA1), (1, 0, 0xA2), (0, 1, 0x00),
        (1, 1, 0xA3), (0, 1, 0x00), (0, 1, 0x00),
    ]),
    ("fill to full, knock twice", [
        (1, 0, 0xB0), (1, 0, 0xB1), (1, 0, 0xB2), (1, 0, 0xB3),
        (1, 0, 0xB4), (1, 0, 0xB5), (1, 0, 0xB6), (1, 0, 0xB7),
        (1, 0, 0xE0), (1, 0, 0xE1),
    ]),
    ("drain to empty, knock twice", [
        (0, 1, 0x00), (0, 1, 0x00), (0, 1, 0x00), (0, 1, 0x00),
        (0, 1, 0x00), (0, 1, 0x00), (0, 1, 0x00), (0, 1, 0x00),
        (0, 1, 0x00), (0, 1, 0x00),
    ]),
    ("both boundaries, simultaneous", [
        (1, 1, 0xC0),
        (1, 0, 0xC1), (1, 0, 0xC2), (1, 0, 0xC3), (1, 0, 0xC4),
        (1, 0, 0xC5), (1, 0, 0xC6), (1, 0, 0xC7),
        (1, 1, 0xE2),
        (0, 1, 0x00), (0, 1, 0x00), (0, 1, 0x00),
    ]),
    ("mixed traffic across the wrap", [
        (1, 1, 0xD0), (1, 1, 0xD1), (0, 1, 0x00), (1, 0, 0xD2),
        (0, 1, 0x00), (0, 1, 0x00), (0, 1, 0x00), (0, 1, 0x00),
    ]),
]

SCENARIO = [v for _name, _seq in SEQUENCES for v in _seq]


def digest(applied):
    """Eight hex characters over the vectors as driven, not as declared."""
    return hashlib.md5(repr(list(applied)).encode()).hexdigest()[:8]


def corner_report(applied):
    """The HW4 corner-case checklist, measured from the driven vectors.
    Identical stimulus gives an identical table -- diff against Tuesday's.
    """
    m = FifoModel(WIDTH, DEPTH)
    full_c = empty_c = writes = 0
    wr_full = wr_full_sim = rd_empty = rd_empty_sim = simul_mid = 0
    for wr, rd, data in applied:
        if wr and m.full:
            wr_full += 1
            wr_full_sim += int(bool(rd))
        if rd and m.empty:
            rd_empty += 1
            rd_empty_sim += int(bool(wr))
        if wr and rd and not m.full and not m.empty:
            simul_mid += 1
        do_wr, _do_rd = m.step(wr, data, rd)
        writes += int(do_wr)
        full_c += int(m.full)
        empty_c += int(m.empty)

    def mark(n):
        return "[x]" if n else "[ ]"

    lines = [
        "",
        "  corner-case checklist -- measured from what was driven",
        f"  {mark(full_c)} full reached              "
        f"{full_c} cycles at count=={DEPTH}",
        f"  {mark(wr_full)} write-while-full refused  "
        f"{wr_full} attempts ({wr_full_sim} simultaneous)",
        f"  {mark(empty_c)} empty re-reached          "
        f"{empty_c} cycles at count==0",
        f"  {mark(rd_empty)} read-while-empty ignored  "
        f"{rd_empty} attempts ({rd_empty_sim} simultaneous)",
        f"  {mark(simul_mid)} simultaneous read+write   "
        f"{simul_mid} mid-stream, count unchanged",
        f"  {mark(writes > DEPTH)} pointer wrap              "
        f"{writes} accepted writes, depth {DEPTH} ({writes // DEPTH} wraps)",
        f"  stimulus: {len(applied)} cycles, digest {digest(applied)}"
        "   (same digest = same vectors)",
    ]
    return "\n".join(lines)


def report(applied):
    cocotb.log.info(corner_report(applied))


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
