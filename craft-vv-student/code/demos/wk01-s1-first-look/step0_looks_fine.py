"""STEP 0 -- the weak test: the one everyone writes first.

Six directed vectors against the ADD slice, both outputs checked against the
golden model on every one. There is even a carry case and an equal-operands
case. It passes. Before moving on, ask what these six vectors have in common
with each other -- and not with the other 65,530.
"""
import cocotb

from demo_common import drive, gold, seed, table

VECTORS = [
    (0x01, 0x02),   # smoke: small operands
    (0x00, 0x00),   # zeros
    (0x37, 0x28),   # mid-range
    (0xFF, 0x01),   # carry out of the top bit -- and we check it
    (0x05, 0x05),   # equal operands -- we even try that
    (0x80, 0x7F),   # top bit set, no carry
]


@cocotb.test()
async def test_looks_fine(dut):
    seed()
    rows = []
    for a, b in VECTORS:
        s, c = await drive(dut, a, b)
        assert (s, c) == gold(a, b), \
            f"a={a:#04x} b={b:#04x}: got sum={s:#04x} carry_out={c}, " \
            f"model says sum={gold(a, b)[0]:#04x} carry_out={gold(a, b)[1]}"
        rows.append((a, b, s, c))
    table(rows)
    cocotb.log.info(f"{len(rows)}/{len(rows)} vectors match the model")
