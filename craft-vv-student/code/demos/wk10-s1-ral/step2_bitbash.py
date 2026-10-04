"""STEP 2 -- bit-bash plus the access-policy walk, generated from the table.

Bit-bash walks a 1 through every writable bit (then all-ones, zero, and a
mixed pattern) and read-back must match -- it catches stuck, aliased, and
mis-decoded bits, for every RW register, from one loop. Then the policy walk
checks the policy *column*: RO must reject writes; W1C must be un-settable
from the bus (a 1 clears, it never sets). Neither check can be expressed as
read-after-write.

Plant the released "RO is secretly writable" mutant and watch the RO check
fire:

    python3 demos/wk10-s1-ral/plant.py ro_writable
    make -C demos/wk10-s1-ral STEP=2 \
        DUT=~/.vvtemp/wk10-mutants/ro_writable/axil_regfile.sv
"""
import random

import cocotb

from demo_common import banner, seed
from step1_reset import REGS, A

PATTERNS = [1 << b for b in range(32)] + [0xFFFFFFFF, 0x00000000, 0xA5A5A5A5]


@cocotb.test()
async def test_bit_bash(dut):
    """Walking-ones + all-ones + zero + mixed on every RW register."""
    bus, model = banner(dut)
    seed()
    await bus.reset()
    rows = ["", "  bit-bash: one loop over the table's RW rows:"]
    for name, r in REGS.items():
        if r["policy"] != "RW":
            continue
        for p in PATTERNS:
            await bus.write(r["addr"], p)
            model.write(r["addr"], p)
            got = await bus.read(r["addr"])
            assert got == p == model.read(r["addr"]), \
                f"{name} bit-bash {p:#010x}: read {got:#010x}"
        rows.append(f"  [RW ] {name:<8} {len(PATTERNS)} patterns "
                    f"(walking-1s, all-1s, zero, 0xa5a5a5a5)   ok")
    cocotb.log.info("\n".join(rows))


@cocotb.test()
async def test_access_policy(dut):
    """The policy column, checked: RO rejects writes; W1C cannot be set."""
    bus, model = banner(dut)
    seed()
    await bus.reset()
    rows = ["", "  access-policy walk:"]

    # RO: STATUS must hold its fixed pattern across junk writes
    for junk in (0xFFFFFFFF, random.getrandbits(32), 0x00000000):
        await bus.write(A["STATUS"], junk)
        model.write(A["STATUS"], junk)
        got = await bus.read(A["STATUS"])
        assert got == REGS["STATUS"]["reset"] == model.read(A["STATUS"]), \
            f"RO STATUS changed to {got:#010x} after write {junk:#010x}"
    rows.append(f"  [RO ] STATUS   held {REGS['STATUS']['reset']:#010x} "
                f"across 3 junk writes           ok")

    # W1C: an all-ones write sets nothing (a 1 clears; the bus can never set)
    await bus.write(A["INTR"], 0xFFFFFFFF)
    model.write(A["INTR"], 0xFFFFFFFF)
    got = await bus.read(A["INTR"])
    assert got == 0 == model.read(A["INTR"]), \
        f"W1C INTR settable from the bus: all-ones write left {got:#010x}"
    rows.append("  [W1C] INTR     all-ones write set nothing "
                "(bus can only clear)      ok")

    rows.append("  policy checks fired: RO, W1C -- neither is read-after-write")
    cocotb.log.info("\n".join(rows))
