"""STEP 1 -- the vector that was missing. Expect a FAIL; that is the step.

Same DUT, same checker, the same six vectors -- plus one: equal operands with
the top bit set. Read the failure line closely before anyone touches code:
the sum is still correct. Only the carry is wrong, and only for this vector.
A checker watching sum alone would have stayed green.
"""
import cocotb

from demo_common import drive, gold, seed, table

VECTORS = [
    (0x01, 0x02),
    (0x00, 0x00),
    (0x37, 0x28),
    (0xFF, 0x01),
    (0x05, 0x05),
    (0x80, 0x7F),
    (0x90, 0x90),   # the missing one: a == b, top bit set
]


@cocotb.test()
async def test_the_vector(dut):
    seed()
    rows = []
    for a, b in VECTORS:
        s, c = await drive(dut, a, b)
        rows.append((a, b, s, c))
        if (s, c) != gold(a, b):
            table(rows)                # show the six greens and the one red
        assert (s, c) == gold(a, b), \
            f"a={a:#04x} b={b:#04x}: got sum={s:#04x} carry_out={c}, " \
            f"model says sum={gold(a, b)[0]:#04x} carry_out={gold(a, b)[1]}"
    table(rows)
