"""STEP 2 -- the requirement, sharpened until it has a definite expected value.

The false start: "the ALU handles overflow correctly" cannot be tested --
step 1 showed two parts that both "handle overflow" and disagree. Sharpened:

    R-ADD-OVF: For ADD, `result` = (a + b) mod 2^WIDTH. `overflow` = 1 iff
    the SIGNED (two's-complement) sum of a and b lies outside
    [-2^(WIDTH-1), 2^(WIDTH-1)-1]. The unsigned does-not-fit fact is a
    different flag: `carry` = 1 iff a + b >= 2^WIDTH.

Two facts were hiding in one vague sentence, so the contract needs two flags
-- and dut/specs/alu.md has both. Every vector below now carries a definite
expected triple (result, overflow, carry). Runs against the course ALU,
dut/alu.sv. It would fail on Engineer B's part; a requirement that can fail
is the first requirement worth putting in a plan.
"""
import cocotb

from demo_common import drive, seed, OP_ADD

#          a     b    result ovf carry   which reading decides it
VECTORS = [
    (0x7F, 0x01,  0x80,  1,  0),   # signed wrap:   +127 + 1 -> overflow, NO carry
    (0x7E, 0x01,  0x7F,  0,  0),   # one below the boundary: neither
    (0xFF, 0x01,  0x00,  0,  1),   # unsigned wrap: -1 + 1   -> carry, NO overflow
    (0x80, 0xFF,  0x7F,  1,  1),   # -128 + -1: both flags, different reasons
    (0x80, 0x80,  0x00,  1,  1),   # step 0's "biggest blow-up" -- both, again
    (0x03, 0x04,  0x07,  0,  0),   # step 0's easy case, still easy
]


@cocotb.test()
async def test_sharpened_requirement(dut):
    seed()
    rows = ["", "      a      b   result  overflow  carry",
            "   ----   ----   ------  --------  -----"]
    for a, b, exp_r, exp_v, exp_c in VECTORS:
        await drive(dut, a, b, OP_ADD)
        got = (int(dut.result.value), int(dut.overflow.value),
               int(dut.carry.value))
        assert got == (exp_r, exp_v, exp_c), (
            f"R-ADD-OVF: a={a:#04x} b={b:#04x} got (result,ovf,carry)={got} "
            f"want ({exp_r:#04x},{exp_v},{exp_c})")
        rows.append(f"   {a:#04x}   {b:#04x}     {exp_r:#04x}  {exp_v:>8}  {exp_c:>5}")
    rows.append(f"   {len(VECTORS)}/{len(VECTORS)} definite expected values met"
                " -- dut/alu.sv implements the signed reading")
    cocotb.log.info("\n".join(rows))
