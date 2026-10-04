"""STEP 3 -- check every output the spec names, not only `result`.

Three of the eight released mutants live entirely in the flags: a dropped
carry, a dropped overflow, an inverted zero. A result-only checker can never
see them, however many vectors it drives. Same stimulus, same settle -- four
assertions per vector.
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
async def test_check_flags(dut):
    seed()
    for a, b, op in VECTORS:
        drive(dut, a, b, op)
        await Timer(1, units="ns")
        check_all(dut, a, b, op)
    cocotb.log.info(f"{len(VECTORS)} vectors x 4 outputs checked")
