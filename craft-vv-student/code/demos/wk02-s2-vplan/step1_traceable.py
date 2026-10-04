"""STEP 1 -- three plan rows become three traceable tests.

Each test names the vplan.md row it implements. The link reads both ways:
delete a test and its row loses coverage (forward); a test with no row has no
reason to exist (backward). Every expected value below is written by hand
from the sharpened requirement -- if you cannot write the expected value, the
requirement is not sharp enough to test. That was Tuesday's lesson.

Score this suite against the released pool and read the survivor list next to
vplan.md: the mutants it misses live exactly in the rows nobody wrote yet.
"""
import cocotb

from demo_common import drive, seed, OP_ADD, OP_SUB, OP_AND, OP_OR, OP_XOR, OP_SLT


@cocotb.test()
async def test_vp1_add_flags(dut):
    """traces: vplan.md VP-1 -- ADD result + overflow (signed) + carry (unsigned)"""
    seed()
    #          a     b    result ovf carry
    vectors = [
        (0x7F, 0x01,  0x80,  1,  0),   # exactly at the signed wrap boundary
        (0x7E, 0x01,  0x7F,  0,  0),   # one below it
        (0xFF, 0x01,  0x00,  0,  1),   # exactly at the unsigned wrap boundary
        (0x40, 0x40,  0x80,  1,  0),   # equal operands, overflow without carry
        (0x80, 0x80,  0x00,  1,  1),   # equal operands, both flags at once
        (0x03, 0x04,  0x07,  0,  0),   # interior point, neither flag
    ]
    for a, b, exp_r, exp_v, exp_c in vectors:
        await drive(dut, a, b, OP_ADD)
        got = (int(dut.result.value), int(dut.overflow.value),
               int(dut.carry.value))
        assert got == (exp_r, exp_v, exp_c), (
            f"VP-1: ADD a={a:#04x} b={b:#04x} got (result,ovf,carry)={got} "
            f"want ({exp_r:#04x},{exp_v},{exp_c})")
    cocotb.log.info("VP-1 pass: 6 wrap-boundary and equal-operand vectors")


@cocotb.test()
async def test_vp2_slt_signed(dut):
    """traces: vplan.md VP-2 -- SLT compares as SIGNED two's-complement"""
    #          a     b    slt        the reading that decides it
    vectors = [
        (0x01, 0xFF,  0),   # 1 < -1 is false; unsigned 1 < 255 would say true
        (0xFF, 0x01,  1),   # -1 < 1 is true;  unsigned says false
        (0x80, 0x7F,  1),   # most negative < most positive
        (0x7F, 0x80,  0),   # ...and not the other way around
        (0x05, 0x05,  0),   # equal operands
    ]
    for a, b, exp in vectors:
        await drive(dut, a, b, OP_SLT)
        got = int(dut.result.value)
        assert got == exp, (
            f"VP-2: SLT a={a:#04x} b={b:#04x} got {got} want {exp} "
            f"-- is the comparison signed?")
    cocotb.log.info("VP-2 pass: 5 one-negative / sign-corner comparisons")


@cocotb.test()
async def test_vp3_zero_flag(dut):
    """traces: vplan.md VP-3 -- zero iff result all zeros, under every op"""
    # The requirement is a relation between two outputs, so the check needs
    # no predicted result: zero must equal (result == 0), always.
    vectors = [
        (0x55, 0x55, OP_SUB),   # a - a == 0        -> zero asserted
        (0xF0, 0x0F, OP_AND),   # disjoint masks    -> zero asserted
        (0x3C, 0x3C, OP_XOR),   # a ^ a == 0        -> zero asserted
        (0x00, 0x00, OP_OR),    # nothing | nothing -> zero asserted
        (0x05, 0x03, OP_SLT),   # false compare     -> zero asserted
        (0x01, 0x02, OP_ADD),   # 3                 -> zero deasserted
        (0xF0, 0x0F, OP_OR),    # 0xFF              -> zero deasserted
    ]
    for a, b, op in vectors:
        await drive(dut, a, b, op)
        r, z = int(dut.result.value), int(dut.zero.value)
        assert z == int(r == 0), (
            f"VP-3: op={op} a={a:#04x} b={b:#04x} result={r:#04x} "
            f"but zero={z}")
    cocotb.log.info("VP-3 pass: zero asserted under 5 ops, deasserted under 2")
