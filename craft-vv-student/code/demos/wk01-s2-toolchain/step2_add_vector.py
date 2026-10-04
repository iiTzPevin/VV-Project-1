"""STEP 2 -- the first edit, and the classic first failure. Expect a FAIL.

This file is tb/alu/test_alu.py plus the one thing everyone adds first: a new
vector with a hand-written expectation. The vector is Tuesday's -- equal
operands, top bit set. The expectation is written the way a calculator
thinks, and the calculator is not eight bits wide.

Read the traceback with the room before touching anything, then put the
question to them: which is wrong here, the design or the test?
"""
import cocotb
from cocotb.triggers import Timer
from models.alu_model import alu_model, OP_NAMES

from demo_common import seed

WIDTH = 8
MASK = (1 << WIDTH) - 1


async def check(dut, a, b, op):
    dut.a.value = a
    dut.b.value = b
    dut.op.value = op
    await Timer(1, units="ns")
    exp = alu_model(a, b, op, WIDTH)
    assert int(dut.result.value) == exp.result, \
        f"{OP_NAMES[op]} a={a:#04x} b={b:#04x}: result mismatch"


@cocotb.test()
async def test_smoke(dut):
    await check(dut, 3, 4, 0)          # 3 + 4  (the provided sanity vector)


@cocotb.test()
async def test_equal_operands(dut):
    """The edit as first written: the expectation comes from arithmetic on
    Python ints, not from the model. 0x90 + 0x90 = 288. Nothing eight bits
    wide can ever equal 288.
    """
    seed()
    a = b = 0x90                       # Tuesday's vector: a == b, top bit set
    dut.a.value = a
    dut.b.value = b
    dut.op.value = 0                   # ADD
    await Timer(1, units="ns")
    assert int(dut.result.value) == a + b, \
        f"ADD a={a:#04x} b={b:#04x}: result {int(dut.result.value)} != {a + b}"
