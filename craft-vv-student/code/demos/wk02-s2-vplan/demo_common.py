"""Shared helpers for the Week 2 demos. Keeps each step file short enough to
read on a projector -- the step files hold only what the demo is about.
"""
import os
import random

import cocotb
from cocotb.triggers import Timer

WIDTH = 8
MASK = (1 << WIDTH) - 1
OP_ADD, OP_SUB, OP_AND, OP_OR, OP_XOR, OP_SLT, OP_SLL, OP_SRL = range(8)


def seed(default=5):
    """Pin the stream so the room sees the run we rehearsed.
    Override from the shell:  make STEP=1 DEMO_SEED=7
    """
    s = int(os.environ.get("DEMO_SEED", default))
    random.seed(s)
    cocotb.log.info(f"demo seed = {s}")
    return s


async def drive(dut, a, b, op):
    """Drive one vector into the combinational ALU and let it settle."""
    dut.a.value = a
    dut.b.value = b
    dut.op.value = op
    await Timer(1, units="ns")
