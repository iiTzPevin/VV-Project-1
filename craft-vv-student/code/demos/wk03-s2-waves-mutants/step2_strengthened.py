"""STEP 2 -- one vector, aimed at the survivor.

`drop_add_carry` ties ADD's carry-out to zero. To make that observable, an
ADD must carry: a + b > 0xFF, and the checker must read the flag. The smallest
such stimulus the room will name is equal operands at the sign boundary --
0x80 + 0x80 wraps to 0x00 with carry AND overflow set, so one vector
exercises the survivor and two of Session 1's flag mutants at once.

Everything else is byte-for-byte step 1. Score it:

    STEP=2 python3 -m craft_mutate.mutate --tb demos/wk03-s2-waves-mutants \
        --pool tb/alu/mutants_released.yaml --sim icarus
"""
import cocotb
from cocotb.triggers import Timer

from models.alu_model import OP_ADD
from demo_common import VECTORS, WIDTH, drive, label, seed
from step1_survivors import check_all

VECTORS_PLUS = VECTORS + [
    (0x80, 0x80, OP_ADD),   # equal operands, sign boundary: 0x00, carry=1, overflow=1
]


@cocotb.test()
async def test_strengthened(dut):
    seed()
    for a, b, op in VECTORS_PLUS:
        drive(dut, a, b, op)
        await Timer(1, units="ns")
        check_all(dut, a, b, op)
    cocotb.log.info(f"{len(VECTORS_PLUS)} vectors x 4 outputs checked -- "
                    f"the last one is aimed at the survivor")
