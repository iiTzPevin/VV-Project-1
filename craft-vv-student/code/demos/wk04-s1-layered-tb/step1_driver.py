"""STEP 1 -- the driver: transactions in, pin wiggles out.

The clock, the reset, and the pin protocol get one home, and the stimulus
becomes FifoTxn objects instead of raw tuples. Nothing else moves: the
reference-queue math and the four checks are still tangled in the test.
Same vectors, same checks, same digest as step 0.
"""
from dataclasses import dataclass

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge, Timer

from demo_common import SCENARIO, seed, report, DEPTH


@dataclass
class FifoTxn:
    """One operation the FIFO performs, named -- not four wires, an intent."""
    wr_en: int
    rd_en: int
    wr_data: int = 0


class FifoDriver:
    """Turns transactions into pin wiggles. Owns the clock and the reset --
    the two things every monolithic test re-implements."""

    def __init__(self, dut, period_ns=10):
        self.dut = dut
        cocotb.start_soon(Clock(dut.clk, period_ns, units="ns").start())

    async def reset(self):
        d = self.dut
        d.wr_en.value = 0
        d.rd_en.value = 0
        d.wr_data.value = 0
        d.rst_n.value = 0
        for _ in range(3):
            await RisingEdge(d.clk)
        d.rst_n.value = 1
        await FallingEdge(d.clk)

    async def drive(self, txn):
        d = self.dut
        d.wr_en.value = txn.wr_en
        d.rd_en.value = txn.rd_en
        d.wr_data.value = txn.wr_data
        await RisingEdge(d.clk)
        await Timer(1, units="ns")


@cocotb.test()
async def test_driver_extracted(dut):
    seed()
    drv = FifoDriver(dut)
    await drv.reset()

    exp = []          # prediction and judgment: still inline, still tangled
    applied = []
    for i, (wr, rd, data) in enumerate(SCENARIO, start=1):
        do_wr = wr and len(exp) < DEPTH
        do_rd = rd and len(exp) > 0
        if do_rd:
            exp.pop(0)
        if do_wr:
            exp.append(data)

        await drv.drive(FifoTxn(wr, rd, data))

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
