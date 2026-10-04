"""Shared helpers for the Week 5 demos. Keeps each step file short enough to
read on a projector -- the step files hold only what the demo is about.
"""
import os
import random

import cocotb
from cocotb.triggers import RisingEdge, FallingEdge, Timer

WIDTH, DEPTH = 8, 8


def seed(default=5):
    """Pin the stream so the room sees the same histogram we rehearsed.
    Override from the shell:  make STEP=1 DEMO_SEED=7
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


async def apply(dut, wr, rd, data):
    """Drive one transaction, advance one clock, settle. Returns nothing."""
    dut.wr_en.value = wr
    dut.rd_en.value = rd
    dut.wr_data.value = data
    await RisingEdge(dut.clk)
    await Timer(1, units="ns")


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
