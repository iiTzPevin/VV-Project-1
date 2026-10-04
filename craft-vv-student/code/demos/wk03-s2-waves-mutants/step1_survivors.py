"""STEP 1 -- Session 1's endpoint, scored instead of admired.

`make STEP=1` runs it green on the clean RTL: ten vectors, four outputs
asserted each. The demo action is the harness -- run it against the released
pool and read the survivor list:

    STEP=1 python3 -m craft_mutate.mutate --tb demos/wk03-s2-waves-mutants \
        --pool tb/alu/mutants_released.yaml --sim icarus

A mutant is FOUND when this suite goes red on it. Expect 7/8 with
`drop_add_carry` surviving: every vector here keeps a+b inside eight bits,
so a dead carry-out never becomes observable. The suite is not wrong -- it is
silent about a case it never drives.
"""
import cocotb
from cocotb.triggers import Timer

from models.alu_model import alu_model
from demo_common import VECTORS, WIDTH, drive, label, seed


def check_all(dut, a, b, op):
    exp = alu_model(a, b, op, WIDTH)
    where = label(a, b, op)
    assert int(dut.result.value) == exp.result, \
        f"{where}: result {int(dut.result.value):#04x} != {exp.result:#04x}"
    assert int(dut.zero.value) == exp.zero, f"{where}: zero flag"
    assert int(dut.carry.value) == exp.carry, f"{where}: carry flag"
    assert int(dut.overflow.value) == exp.overflow, f"{where}: overflow flag"


@cocotb.test()
async def test_survivors(dut):
    seed()
    for a, b, op in VECTORS:
        drive(dut, a, b, op)
        await Timer(1, units="ns")
        check_all(dut, a, b, op)
    cocotb.log.info(f"{len(VECTORS)} vectors x 4 outputs checked")
