"""Shared helpers for the Week 2 demos. Keeps each step file short enough to
read on a projector -- the step files hold only what the demo is about.
"""
import os
import random

import cocotb
from cocotb.triggers import Timer

WIDTH = 8
MASK = (1 << WIDTH) - 1
OP_ADD, OP_SUB = 0, 1


def seed(default=5):
    """Pin the stream so the room sees the same table we rehearsed.
    Override from the shell:  make STEP=1 DEMO_SEED=7
    """
    s = int(os.environ.get("DEMO_SEED", default))
    random.seed(s)
    cocotb.log.info(f"demo seed = {s}")
    return s


async def drive(dut, a, b, op=OP_ADD):
    """Drive one vector into a combinational DUT and let it settle."""
    dut.a.value = a
    dut.b.value = b
    dut.op.value = op
    await Timer(1, units="ns")


# The spec's own corner sentence, as data (dut/specs/alu.md, last section):
# "Add and subtract at the wrap boundaries (exactly at, and one either side);
#  ... the sign corners 8'h7F/8'h80 and the extremes 8'h00/8'hFF".
WRAP_PROBES = [                      # directed (a, b) pairs for ADD
    (0x7F, 0x01),  # exactly at the signed wrap boundary
    (0x7E, 0x01),  # one below it
    (0x7F, 0x00),  # at the sign corner, no push
    (0xFF, 0x01),  # exactly at the unsigned wrap boundary
    (0xFF, 0x00),  # one below it
    (0x80, 0x01),  # the other sign corner, pushed up
    (0x80, 0xFF),  # pushed down past -128
    (0x00, 0x00),  # the do-nothing floor
]
CORNERS = [0x00, 0x01, 0x7E, 0x7F, 0x80, 0x81, 0xFE, 0xFF]
