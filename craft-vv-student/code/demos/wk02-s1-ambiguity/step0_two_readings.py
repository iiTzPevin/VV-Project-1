"""STEP 0 -- the overflow test you write from the sentence as it stands.

The spec says: "overflow -- set when the mathematical result ... does not fit
in WIDTH bits." Fine. Test it: a case that fits, a case that does not, done.
The vectors below are the ones that come to mind first -- and on every one of
them, Engineer A's signed reading and Engineer B's unsigned reading happen to
AGREE. Two contradictory parts, one test, both pass. The test is not wrong;
it is toothless, and nothing on the screen says so.
"""
import cocotb

from demo_common import drive, seed, OP_ADD

#          a     b    exp_ovf   why we believed the expectation
VECTORS = [
    (0x03, 0x04,  0,  "3+4=7, fits any reading of anything"),
    (0x00, 0x00,  0,  "the floor"),
    (0x80, 0x80,  1,  "biggest blow-up we could think of"),
    (0x80, 0xFF,  1,  "very negative plus negative"),
]


@cocotb.test()
async def test_vague_overflow(dut):
    seed()
    rows = ["", "      a      b   ovf(A: signed)  ovf(B: carry)  expected",
            "   ----   ----   -------------  -------------  --------"]
    for a, b, exp, _why in VECTORS:
        await drive(dut, a, b, OP_ADD)
        sa, sb = int(dut.ovf_s.value), int(dut.ovf_c.value)
        rows.append(f"   {a:#04x}   {b:#04x}   {sa:>13}  {sb:>13}  {exp:>8}")
        assert sa == exp, f"Engineer A fails at a={a:#04x} b={b:#04x}"
        assert sb == exp, f"Engineer B fails at a={a:#04x} b={b:#04x}"
    rows.append("   two contradictory implementations, one test: BOTH PASS")
    cocotb.log.info("\n".join(rows))
