"""STEP 2 -- controllability and observability, measured.

Drive every input pair -- all 2^16; this block is small enough, and Week 3's
DUTs will not be -- and count mismatches at two observation points. The
stimulus is identical both times; only where we look changes. Where you look
decides whether the bug exists for you.
"""
import math

import cocotb

from demo_common import MASK, drive, gold, seed


@cocotb.test()
async def test_observation_points(dut):
    seed()
    at_sum, at_carry, on_diagonal = 0, 0, 0
    first = None
    for a in range(MASK + 1):
        for b in range(MASK + 1):
            s, c = await drive(dut, a, b)
            es, ec = gold(a, b)
            if s != es:
                at_sum += 1
            if c != ec:
                at_carry += 1
                on_diagonal += int(a == b)
                if first is None:
                    first = (a, b)
    total = (MASK + 1) ** 2
    active = at_carry + at_sum          # pairs where the DUT is wrong anywhere
    p = active / total
    coin_flip = math.ceil(math.log(0.5) / math.log(1 - p)) if p else 0
    cocotb.log.info("\n".join([
        "",
        f"  input pairs driven          : {total}  (exhaustive: 8+8 input bits)",
        f"  pairs where the DUT is wrong: {active}"
        f"   ({on_diagonal} of {at_carry} on the a == b diagonal;"
        f" first at a={first[0]:#04x} b={first[1]:#04x})",
        f"  observed at sum             : {at_sum}",
        f"  observed at carry_out       : {at_carry}",
        "",
        f"  controllability: 1 pair in {total // active} activates the bug --"
        f" a uniform random test needs ~{coin_flip} vectors"
        " for a coin-flip chance of reaching it once",
        f"  observability:  the bug was activated {active} times;"
        " a checker watching only sum saw 0 of them",
    ]))
    assert at_sum == 0, "unexpected: sum mismatches -- not the planted bug"
    assert at_carry == 128 and on_diagonal == at_carry, \
        "mismatch pattern moved -- addc.sv no longer carries the planted bug"
