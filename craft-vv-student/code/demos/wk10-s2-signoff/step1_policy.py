"""STEP 1 -- the locked-register assertion, and the mutant that proves it earns
its keep.

The property, stated once: protected state must not change under a
transaction that lacks privilege. This step is that sentence as a check --
lock, drive the unauthorized write, assert SECURE is unmoved and INTR[0] is
latched. On the clean RTL it passes. On the released policy mutant
(`secure_writable_locked` -- the case arm's lock test deleted) the write
lands and the assertion fires:

    python3 demos/wk10-s2-signoff/plant.py secure_writable_locked
    make -C demos/wk10-s2-signoff STEP=1 \
        DUT=~/.vvtemp/wk10-mutants/secure_writable_locked/axil_regfile.sv

A happy-path read/write test passes on that mutant -- which is the week's
point: the policy is the security boundary, and only a policy-aware check
guards it.
"""
import cocotb

from demo_common import banner, seed

A_INTR, A_LOCK, A_SECURE = 0x3, 0x4, 0x5


@cocotb.test()
async def test_locked_register_assertion(dut):
    """Protected state must not change under a transaction that lacks privilege."""
    bus, model = banner(dut)
    seed()
    await bus.reset()
    rows = ["", "  the access-control property, as a check:"]

    # arrange: something known sits in SECURE, then the lock goes on
    await bus.write(A_SECURE, 0xA5A5A5A5);  model.write(A_SECURE, 0xA5A5A5A5)
    await bus.write(A_LOCK, 0x1);           model.write(A_LOCK, 0x1)
    rows.append("  arrange: SECURE <= 0xa5a5a5a5, then LOCK <= 1")

    # act: the unauthorized write
    await bus.write(A_SECURE, 0xDEADBEEF);  model.write(A_SECURE, 0xDEADBEEF)
    rows.append("  act:     SECURE <= 0xdeadbeef with LOCK=1   (no privilege)")

    # assert: protected state unmoved, violation latched
    got = await bus.read(A_SECURE)
    assert got == 0xA5A5A5A5 == model.read(A_SECURE), \
        f"SECURITY: locked SECURE accepted a write (now {got:#010x})"
    rows.append("  assert:  SECURE still reads 0xa5a5a5a5   -> write dropped   ok")
    intr = await bus.read(A_INTR)
    assert intr & 0x1, "locked SECURE write did not latch INTR[0]"
    rows.append(f"  assert:  INTR[0] latched ({intr:#010x})   -> violation visible   ok")

    rows.append("  property held on this RTL. Now plant secure_writable_locked")
    rows.append("  and run the same check -- the policy is the security boundary.")
    cocotb.log.info("\n".join(rows))
