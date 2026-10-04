"""STEP 1 -- the sampling off-by-one. KEPT BROKEN on purpose.

Same vectors, plus the golden model as a checker -- so this *should* be our
first self-checking testbench. Look at the order inside the loop: we sample
`result` on the line after we drive, and only then let the simulator settle.
Sequential Python is not sequential simulated time. Every read returns the
answer to the PREVIOUS vector's question -- wrong but plausible, and the
whole table shifts by one row.

The fix is step 2, and it is two lines trading places.
"""
import cocotb
from cocotb.triggers import Timer

from models.alu_model import alu_model
from demo_common import VECTORS, WIDTH, drive, label, seed


@cocotb.test()
async def test_sample_early(dut):
    seed()
    drive(dut, 0, 0, 0)                # park the ALU at a known state:
    await Timer(1, units="ns")         # 0 + 0 -> result 0x00

    wrong = off_by_one = 0
    prev_exp = 0x00
    for a, b, op in VECTORS:
        drive(dut, a, b, op)
        got = int(dut.result.value)    # BUG: sampled before the settle
        await Timer(1, units="ns")     # the settle happens after we looked
        exp = alu_model(a, b, op, WIDTH).result
        note = "  <- the previous vector's answer" if got == prev_exp else ""
        verdict = "ok   " if got == exp else "WRONG"
        cocotb.log.info(f"{label(a, b, op):<22} read {got:#04x}   "
                        f"model says {exp:#04x}   {verdict}{note}")
        wrong += int(got != exp)
        off_by_one += int(got == prev_exp)
        prev_exp = exp

    cocotb.log.info(f"{wrong}/{len(VECTORS)} reads wrong -- and "
                    f"{off_by_one}/{len(VECTORS)} match the vector BEFORE "
                    f"the one we asked about")
    assert wrong == 0, f"sampled one settle too early on {wrong} vectors"
