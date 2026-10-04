"""Shared helpers for the Week 7 Session 1 demo. Keeps each step file short
enough to read on a projector -- the step files hold only what the demo is
about. seed/reset/apply/check/histogram are the Week 5 helpers carried
forward unchanged; count_sva is new.
"""
import os
import random
import re

import cocotb
from cocotb.triggers import RisingEdge, FallingEdge, Timer

WIDTH, DEPTH = 8, 8


def seed(default=5):
    """Pin the stream so the room sees the run we rehearsed.
    Override from the shell:  make STEP=2 DEMO_SEED=8
    """
    s = int(os.environ.get("DEMO_SEED", default))
    random.seed(s)
    cocotb.log.info(f"demo seed = {s}")
    return s


async def reset(dut):
    """Drive a clean reset and leave us parked on a falling edge."""
    dut.wr_en.value = 0
    dut.rd_en.value = 0
    dut.wr_data.value = 0
    dut.rst_n.value = 0
    for _ in range(3):
        await RisingEdge(dut.clk)
    dut.rst_n.value = 1
    await FallingEdge(dut.clk)


async def apply(dut, wr, rd, data=0):
    """Drive one transaction, advance one clock, settle."""
    dut.wr_en.value = wr
    dut.rd_en.value = rd
    dut.wr_data.value = data
    await RisingEdge(dut.clk)
    await Timer(1, units="ns")


def check(dut, model):
    """The Week 5 scoreboard, carried forward unchanged. This is the
    IMMEDIATE layer: a Python assert checks the instant this call runs, and
    only then. Between calls nobody is looking -- that gap is what the bound
    concurrent properties close.
    """
    assert int(dut.count.value) == model.count, \
        f"count {int(dut.count.value)} != model {model.count}"
    assert bool(dut.full.value) == model.full, \
        f"full {bool(dut.full.value)} != model {model.full}"
    assert bool(dut.empty.value) == model.empty, \
        f"empty {bool(dut.empty.value)} != model {model.empty}"
    if not model.empty:                       # FWFT: head valid only when !empty
        assert int(dut.rd_data.value) == model.head, \
            f"rd_data {int(dut.rd_data.value):#04x} != head {model.head:#04x}"


def histogram(counts, depth=DEPTH):
    """An occupancy histogram you can read from the back row."""
    bins = [0] * (depth + 1)
    for c in counts:
        bins[c] += 1
    peak = max(bins) or 1
    out = ["", "  occupancy   cycles", "  ---------   ------"]
    for i, n in enumerate(bins):
        bar = "#" * round(20 * n / peak)
        tag = " <- EMPTY" if i == 0 else (" <- FULL" if i == depth else "")
        out.append(f"  {i:>9}   {n:>6}  {bar}{tag}")
    reach = sum(1 for i in (0, depth) if bins[i] > 0)
    out.append(f"  boundaries reached: {reach}/2   "
               f"(empty={bins[0]} cycles, full={bins[depth]} cycles)")
    return "\n".join(out)


def report(dut, counts):
    cocotb.log.info(histogram(counts))


def sva_path(name="fifo_sva.sv"):
    """Find dut/<name> by walking up from this file. Works from the demo dir
    (two levels below code/) and from a scoring scratch copy parked anywhere
    with a dut/ dir somewhere above it."""
    d = os.path.dirname(os.path.abspath(__file__))
    while True:
        cand = os.path.join(d, "dut", name)
        if os.path.exists(cand):
            return cand
        parent = os.path.dirname(d)
        if parent == d:
            raise FileNotFoundError(f"no dut/{name} above {__file__}")
        d = parent


def count_sva(path):
    """Count the (assert, cover) properties a checker file arms -- read from
    the source at run time, so the number on the projector is measured, not
    asserted."""
    with open(path) as f:
        text = f.read()
    return (len(re.findall(r":\s*assert\s+property", text)),
            len(re.findall(r":\s*cover\s+property", text)))
