"""STEP 3 -- the locked SECURE register: access control as a checked property.

The spec's security interaction: while LOCK.bit0==1 a write to SECURE must be
dropped AND hardware must latch INTR[0]; unlock and it is writable again. The
property in one sentence: protected state must not change under a transaction
that lacks privilege.

The step ends with INTR[0] still set on purpose -- clearing it is the We Do
(write the W1C check: a 1 clears, a 0 holds; the reference is
the reference suite covers both writes in a single w1c policy test).

Plant the released policy mutant (`secure_writable_locked`) and the
unauthorized write lands -- the check fires:

    python3 demos/wk10-s1-ral/plant.py secure_writable_locked
    make -C demos/wk10-s1-ral STEP=3 \
        DUT=~/.vvtemp/wk10-mutants/secure_writable_locked/axil_regfile.sv
"""
import cocotb

from demo_common import banner, seed
from step1_reset import REGS, A


@cocotb.test()
async def test_secure_lock(dut):
    """SECURE writable only while unlocked; a locked write raises INTR[0]."""
    bus, model = banner(dut)
    seed()
    await bus.reset()
    rows = ["", "  the security interaction, per spec:"]

    # unlocked -> writable
    await bus.write(A["LOCK"], 0x0);            model.write(A["LOCK"], 0x0)
    await bus.write(A["SECURE"], 0xA5A5A5A5);   model.write(A["SECURE"], 0xA5A5A5A5)
    got = await bus.read(A["SECURE"])
    assert got == 0xA5A5A5A5, f"SECURE not writable while unlocked: {got:#010x}"
    rows.append("  [1] LOCK=0, SECURE <= 0xa5a5a5a5, read-back ok   (unlocked: writable)")

    # locked -> the unauthorized write MUST be dropped
    await bus.write(A["LOCK"], 0x1);            model.write(A["LOCK"], 0x1)
    await bus.write(A["SECURE"], 0x5A5A5A5A);   model.write(A["SECURE"], 0x5A5A5A5A)
    got = await bus.read(A["SECURE"])
    assert got == 0xA5A5A5A5 == model.read(A["SECURE"]), \
        f"SECURITY: locked SECURE accepted a write (now {got:#010x})"
    rows.append("  [2] LOCK=1, SECURE <= 0x5a5a5a5a   -> dropped, still 0xa5a5a5a5   ok")

    # ... and hardware latches the violation
    got = await bus.read(A["INTR"])
    assert got & 0x1, "locked SECURE write did not latch INTR[0]"
    assert model.read(A["INTR"]) & 0x1
    rows.append(f"  [3] INTR[0] latched by hardware: INTR reads {got:#010x}   ok")

    # unlock -> writable again
    await bus.write(A["LOCK"], 0x0);            model.write(A["LOCK"], 0x0)
    await bus.write(A["SECURE"], 0xDEADBEEF);   model.write(A["SECURE"], 0xDEADBEEF)
    got = await bus.read(A["SECURE"])
    assert got == 0xDEADBEEF, f"SECURE not writable after unlock: {got:#010x}"
    rows.append("  [4] LOCK=0, SECURE <= 0xdeadbeef, read-back ok   (unlocked again)")

    rows.append("  property held: protected state never moved without privilege")
    rows.append("  INTR[0] is still set. Clearing it is the We Do:")
    rows.append("  write the W1C check -- a 1 clears it, a 0 must not.")
    cocotb.log.info("\n".join(rows))
