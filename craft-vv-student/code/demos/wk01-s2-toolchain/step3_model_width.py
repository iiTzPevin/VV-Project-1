"""STEP 3 -- the fix: the expectation moves into the golden model.

288 does not fit in eight bits. The design was never wrong -- the expectation
was computed in unbounded Python integers while the DUT lives in logic [7:0].
The fix is not `& 0xFF` pasted into the assert; it is asking the model, which
owns the width. And the model also hands back the bit that 288 was trying to
smuggle out: carry. Check it -- that one extra line is what moves the mutation
score.
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
    seed()
    a = b = 0x90                       # Tuesday's vector: a == b, top bit set
    dut.a.value = a
    dut.b.value = b
    dut.op.value = 0                   # ADD
    await Timer(1, units="ns")
    exp = alu_model(a, b, 0, WIDTH)    # the model owns the width
    assert int(dut.result.value) == exp.result, \
        f"ADD a={a:#04x} b={b:#04x}: result {int(dut.result.value):#04x} " \
        f"!= {exp.result:#04x}"
    assert int(dut.carry.value) == exp.carry, \
        f"ADD a={a:#04x} b={b:#04x}: carry {int(dut.carry.value)} != {exp.carry}"
