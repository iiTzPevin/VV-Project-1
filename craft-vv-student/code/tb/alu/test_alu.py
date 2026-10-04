"""STUDENT STARTER -- Week 3 ALU testbench.

Goal: build a self-checking testbench that compares the DUT to the golden
model (models.alu_model) on enough vectors to *find* the mutants.

Run it:            make                 # Verilator (or: make SIM=icarus)
Score your suite:  cd code && just mutate alu     # reports found/total

Right now this only drives one vector. That is deliberate -- your job is to
raise the found/total by exercising every operation and its corner cases
(zero, max, the sign boundary, and *equal operands*). Fill in the TODOs.
"""
import cocotb
from cocotb.triggers import Timer
from models.alu_model import alu_model, OP_NAMES

WIDTH = 8
MASK = (1 << WIDTH) - 1


async def check(dut, a, b, op):
    dut.a.value = a
    dut.b.value = b
    dut.op.value = op
    await Timer(1, units="ns")
    exp = alu_model(a, b, op, WIDTH)
    # TODO: also compare zero, carry, and overflow -- not just result.
    assert int(dut.result.value) == exp.result, \
        f"{OP_NAMES[op]} a={a:#04x} b={b:#04x}: result mismatch"


@cocotb.test()
async def test_smoke(dut):
    await check(dut, 3, 4, 0)          # 3 + 4
    # TODO: cover every op (0..7); add corners (0, MASK, sign boundary);
    # TODO: add equal-operand cases; add a seeded random loop.
