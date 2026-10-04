"""STEP 1 -- hunt the sentence until it produces a witness vector.

Same two parts. Now the stimulus is the spec's own corner list -- the wrap
boundaries exactly at and one either side, the sign corners, the extremes --
then a corner cross and a seeded random sweep. We do not need a golden model
to convict the sentence: if it meant one thing, two compliant parts could not
disagree. The assert at the bottom says the readings must match everywhere.

Expect a failure at the first wrap-boundary probe. That is the point of the
step; the fix is a sharper sentence (step 2), not a code change here.
"""
import random

import cocotb

from demo_common import drive, seed, MASK, OP_ADD, WRAP_PROBES, CORNERS


@cocotb.test()
async def test_readings_agree(dut):
    seed()
    vectors = list(WRAP_PROBES)
    vectors += [(a, b) for a in CORNERS for b in CORNERS]
    vectors += [(random.randint(0, MASK), random.randint(0, MASK))
                for _ in range(200)]

    diverge = []
    for a, b in vectors:
        await drive(dut, a, b, OP_ADD)
        sa, sb = int(dut.ovf_s.value), int(dut.ovf_c.value)
        if sa != sb:
            diverge.append((a, b, sa, sb))

    rows = ["", f"  ADD sweep: {len(WRAP_PROBES)} spec probes + "
                f"{len(CORNERS)}x{len(CORNERS)} corner cross + 200 random",
            "      a      b   ovf(A: signed)  ovf(B: carry)",
            "   ----   ----   -------------  -------------"]
    for a, b, sa, sb in diverge[:6]:
        rows.append(f"   {a:#04x}   {b:#04x}   {sa:>13}  {sb:>13}   <- DIVERGE")
    if len(diverge) > 6:
        rows.append(f"   ... and {len(diverge) - 6} more")
    rows.append(f"  readings disagree on {len(diverge)}/{len(vectors)} vectors")
    cocotb.log.info("\n".join(rows))

    assert not diverge, (
        f"one sentence, two compliant parts: readings diverge on "
        f"{len(diverge)}/{len(vectors)} ADD vectors, first witness "
        f"a={diverge[0][0]:#04x} b={diverge[0][1]:#04x} -- "
        f"the defect is in the spec, not in either part")
