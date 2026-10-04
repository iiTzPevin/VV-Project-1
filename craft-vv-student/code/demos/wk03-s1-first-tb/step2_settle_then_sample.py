"""STEP 2 -- the fix: settle, then sample.

Identical to step 1 except the two lines inside the loop trade places: await
the settle first, sample second. `await` is not a function call -- it hands
control to the simulator and resumes only after the event you named. A value
is worth reading only after the event that makes it valid. Green -- and this
time green means ten predictions matched, not zero checks made.
"""
import cocotb
from cocotb.triggers import Timer

from models.alu_model import alu_model
from demo_common import VECTORS, WIDTH, drive, label, seed


@cocotb.test()
async def test_settle_then_sample(dut):
    seed()
    checked = 0
    for a, b, op in VECTORS:
        drive(dut, a, b, op)
        await Timer(1, units="ns")     # let the combinational cloud settle
        got = int(dut.result.value)    # NOW the value answers this vector
        exp = alu_model(a, b, op, WIDTH).result
        assert got == exp, \
            f"{label(a, b, op)}: result {got:#04x} != model {exp:#04x}"
        checked += 1
    cocotb.log.info(f"{checked}/{len(VECTORS)} results checked against the model")
