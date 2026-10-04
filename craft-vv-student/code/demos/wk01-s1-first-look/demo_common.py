"""Shared helpers for the Week 1 Session 1 demo. Keeps each step file short
enough to read on a projector -- the step files hold only what the demo is
about.
"""
import os
import random

import cocotb
from cocotb.triggers import Timer

WIDTH = 8
MASK = (1 << WIDTH) - 1


def seed(default=5):
    """Pin any randomness so the room sees the run we rehearsed.
    Override from the shell:  make STEP=0 DEMO_SEED=7
    """
    s = int(os.environ.get("DEMO_SEED", default))
    random.seed(s)
    cocotb.log.info(f"demo seed = {s}")
    return s


def gold(a, b):
    """The specification, executable: a 9-bit add, split into sum and carry.
    Eight lines of RTL deserve one line of model.
    """
    ext = (a & MASK) + (b & MASK)
    return ext & MASK, ext >> WIDTH


async def drive(dut, a, b):
    """Apply one vector to the combinational block, let it settle, read back."""
    dut.a.value = a
    dut.b.value = b
    await Timer(1, units="ns")
    return int(dut.sum.value), int(dut.carry_out.value)


def table(rows):
    """The eyeball view: what a waveform window would show, as text."""
    out = ["", "     a     b       sum   carry_out",
           "  ----  ----      ----   ---------"]
    for a, b, s, c in rows:
        es, ec = gold(a, b)
        flag = "" if (s, c) == (es, ec) else "   <-- WRONG (model says "\
               f"sum={es:#04x} carry_out={ec})"
        out.append(f"  {a:#04x}  {b:#04x}      {s:#04x}   {c}{flag}")
    cocotb.log.info("\n".join(out))
