"""STEP 0 -- the Week-3 way: one function does every job.

Clocking, reset, prediction, driving, and judging, interleaved in one test.
It passes, and it even covers the corners. Count the jobs this one function
carries, then watch steps 1-3 take them away -- without changing one vector
or one check. The digest at the bottom of the report is the receipt.
"""
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

from demo_common import seed, report, DEPTH


@cocotb.test()
async def test_monolith(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    seed()

    # -- reset: by hand, in the test --------------------------------------
    dut.wr_en.value = 0
    dut.rd_en.value = 0
    dut.wr_data.value = 0
    dut.rst_n.value = 0
    for _ in range(3):
        await RisingEdge(dut.clk)
    dut.rst_n.value = 1

    # -- the reference queue: also by hand, also in the test ---------------
    exp = []

    # -- the vectors: written out longhand, phase comments doing the work --
    vectors = [
        # first in, first out
        (1, 0, 0xA0), (1, 0, 0xA1), (1, 0, 0xA2), (0, 1, 0x00),
        (1, 1, 0xA3), (0, 1, 0x00), (0, 1, 0x00),
        # fill to full, knock twice (both knocks must be refused)
        (1, 0, 0xB0), (1, 0, 0xB1), (1, 0, 0xB2), (1, 0, 0xB3),
        (1, 0, 0xB4), (1, 0, 0xB5), (1, 0, 0xB6), (1, 0, 0xB7),
        (1, 0, 0xE0), (1, 0, 0xE1),
        # drain to empty, knock twice (both knocks must be ignored)
        (0, 1, 0x00), (0, 1, 0x00), (0, 1, 0x00), (0, 1, 0x00),
        (0, 1, 0x00), (0, 1, 0x00), (0, 1, 0x00), (0, 1, 0x00),
        (0, 1, 0x00), (0, 1, 0x00),
        # both boundaries, simultaneous
        (1, 1, 0xC0),
        (1, 0, 0xC1), (1, 0, 0xC2), (1, 0, 0xC3), (1, 0, 0xC4),
        (1, 0, 0xC5), (1, 0, 0xC6), (1, 0, 0xC7),
        (1, 1, 0xE2),
        (0, 1, 0x00), (0, 1, 0x00), (0, 1, 0x00),
        # mixed traffic across the wrap
        (1, 1, 0xD0), (1, 1, 0xD1), (0, 1, 0x00), (1, 0, 0xD2),
        (0, 1, 0x00), (0, 1, 0x00), (0, 1, 0x00), (0, 1, 0x00),
    ]

    applied = []
    for i, (wr, rd, data) in enumerate(vectors, start=1):
        # predict: reference-queue math, inline
        do_wr = wr and len(exp) < DEPTH
        do_rd = rd and len(exp) > 0
        if do_rd:
            exp.pop(0)
        if do_wr:
            exp.append(data)
        # drive: pin wiggles, inline
        dut.wr_en.value = wr
        dut.rd_en.value = rd
        dut.wr_data.value = data
        await RisingEdge(dut.clk)
        await Timer(1, units="ns")
        # judge: four checks, inline
        assert int(dut.count.value) == len(exp), \
            f"cycle {i}: count {int(dut.count.value)} != model {len(exp)}"
        assert bool(dut.full.value) == (len(exp) == DEPTH), \
            f"cycle {i}: full {bool(dut.full.value)} != model {len(exp) == DEPTH}"
        assert bool(dut.empty.value) == (len(exp) == 0), \
            f"cycle {i}: empty {bool(dut.empty.value)} != model {len(exp) == 0}"
        if exp:  # FWFT: head valid only when not empty
            assert int(dut.rd_data.value) == exp[0], \
                f"cycle {i}: rd_data {int(dut.rd_data.value):#04x} != head {exp[0]:#04x}"
        applied.append((wr, rd, data))

    report(applied)
