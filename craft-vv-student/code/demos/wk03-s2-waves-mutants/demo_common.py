"""Shared helpers for the Week 3 demos. Keeps each step file short enough to
read on a projector -- the step files hold only what the demo is about.

Week 3 stimulus is directed, so DEMO_SEED changes nothing yet. seed() is here
because pin-it-and-print-it is a habit worth setting now, two weeks before the
seed becomes load-bearing.
"""
import os
import random

import cocotb

from models.alu_model import (OP_ADD, OP_SUB, OP_AND, OP_OR, OP_XOR,
                              OP_SLT, OP_SLL, OP_SRL, OP_NAMES)

WIDTH = 8

# One vector per op plus the corners this week cares about. Every step drives
# this same list -- what changes between steps is WHEN we sample and WHAT we
# check, never the stimulus.
VECTORS = [
    (0x03, 0x04, OP_ADD),   # the starter's smoke vector
    (0x7F, 0x01, OP_ADD),   # sign boundary: signed overflow, no carry-out
    (0x2A, 0x2A, OP_SUB),   # equal operands -> zero
    (0x03, 0x05, OP_SUB),   # a < b -> borrow (carry flag on SUB)
    (0xF0, 0x0F, OP_AND),   # disjoint masks -> 0x00
    (0xF0, 0x0F, OP_OR),    # same masks     -> 0xff
    (0xFF, 0x0F, OP_XOR),
    (0x80, 0x01, OP_SLT),   # signed: -128 < 1, unsigned: 0x80 > 0x01
    (0x01, 0x03, OP_SLL),
    (0x80, 0x02, OP_SRL),
]


def seed(default=5):
    """Pin the stream and say so. Override from the shell:
    make STEP=2 DEMO_SEED=7
    """
    s = int(os.environ.get("DEMO_SEED", default))
    random.seed(s)
    cocotb.log.info(f"demo seed = {s}")
    return s


def drive(dut, a, b, op):
    """Assign one vector. Assignments are *scheduled*, not applied -- nothing
    in the design moves until the simulator next advances time."""
    dut.a.value = a
    dut.b.value = b
    dut.op.value = op


def label(a, b, op):
    return f"{OP_NAMES[op]} a={a:#04x} b={b:#04x}"
