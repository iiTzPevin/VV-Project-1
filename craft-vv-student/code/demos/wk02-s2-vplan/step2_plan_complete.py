"""STEP 2 -- the class's two rows land, and the plan predicts the score.

Step 1 scored 5/8, and the survivor list read like an accusation: every
surviving mutant lived in a row vplan.md did not have. The We Do adds those
rows -- logical ops (VP-4) and shifts (VP-5) -- and this file adds their
tests. VP-1..VP-3 are imported unchanged: growing a plan does not mean
rewriting it.

Score this suite against the released pool for the found/total preview HW2
asks you to report in FINDINGS.md. Found, never "killed".
"""
import cocotb

from demo_common import drive, OP_AND, OP_OR, OP_XOR, OP_SLL, OP_SRL
from step1_traceable import (          # rows VP-1..VP-3, byte for byte
    test_vp1_add_flags,
    test_vp2_slt_signed,
    test_vp3_zero_flag,
)


@cocotb.test()
async def test_vp4_logical_ops(dut):
    """traces: vplan.md VP-4 -- AND/OR/XOR, bitwise, no flag side effects"""
    #          a     b    op      result
    vectors = [
        (0x0F, 0x33, OP_AND,  0x03),   # overlapping masks
        (0xF0, 0x0F, OP_AND,  0x00),   # disjoint masks
        (0x0F, 0x30, OP_OR,   0x3F),   # disjoint union
        (0x00, 0x00, OP_OR,   0x00),   # nothing from nothing
        (0xFF, 0x0F, OP_XOR,  0xF0),   # mask inversion
        (0xAA, 0xAA, OP_XOR,  0x00),   # equal operands cancel
    ]
    for a, b, op, exp in vectors:
        await drive(dut, a, b, op)
        got = int(dut.result.value)
        assert got == exp, (
            f"VP-4: op={op} a={a:#04x} b={b:#04x} got {got:#04x} want {exp:#04x}")
    cocotb.log.info("VP-4 pass: 6 truth-table vectors across AND/OR/XOR")


@cocotb.test()
async def test_vp5_shifts(dut):
    """traces: vplan.md VP-5 -- SLL/SRL use only b[2:0]; vacated bits are 0"""
    #          a     b    op      result
    vectors = [
        (0x01, 0x07, OP_SLL,  0x80),   # by WIDTH-1, all the way across
        (0x81, 0x00, OP_SLL,  0x81),   # by zero: unchanged
        (0x01, 0x09, OP_SLL,  0x02),   # b=9 shifts by 1, not by 9 (spec: b[2:0])
        (0x80, 0x07, OP_SRL,  0x01),   # back across the other way
        (0xFF, 0x08, OP_SRL,  0xFF),   # b=8 shifts by 0 -- upper bits ignored
        (0xFF, 0x01, OP_SRL,  0x7F),   # logical shift: zero fills the top
    ]
    for a, b, op, exp in vectors:
        await drive(dut, a, b, op)
        got = int(dut.result.value)
        assert got == exp, (
            f"VP-5: op={op} a={a:#04x} b={b:#04x} got {got:#04x} want {exp:#04x}")
    cocotb.log.info("VP-5 pass: 6 shift vectors incl. b >= WIDTH")
