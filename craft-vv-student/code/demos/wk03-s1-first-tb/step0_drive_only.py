"""STEP 0 -- drive without checking: the testbench that cannot fail.

Ten vectors, every op, corners included. It drives them, waits for the
combinational cloud to settle, prints what came back -- and never compares
anything to anything. Green, and it stays green on almost any broken ALU.
"""
import cocotb
from cocotb.triggers import Timer

from demo_common import VECTORS, drive, label, seed


@cocotb.test()
async def test_drive_only(dut):
    seed()
    for a, b, op in VECTORS:
        drive(dut, a, b, op)
        await Timer(1, units="ns")
        cocotb.log.info(
            f"{label(a, b, op):<22} -> result={int(dut.result.value):#04x} "
            f"zero={int(dut.zero.value)} carry={int(dut.carry.value)} "
            f"overflow={int(dut.overflow.value)}")
    cocotb.log.info(f"{len(VECTORS)} vectors driven, 0 values checked")
