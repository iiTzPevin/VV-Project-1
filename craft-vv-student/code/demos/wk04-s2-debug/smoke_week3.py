"""The Week-3-style smoke test, copied from tb/fifo/test_fifo.py's starter so
the course starter stays untouched. Three writes, one count check. Step 0 runs
it against the planted DUT to make the point: this test is green on a FIFO
that destroys data. It is not a step of its own -- step0_plant.py invokes it.
"""
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, Timer

from demo_common import seed


@cocotb.test()
async def test_smoke(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    seed()
    dut.wr_en.value = 0
    dut.rd_en.value = 0
    dut.wr_data.value = 0
    dut.rst_n.value = 0
    for _ in range(3):
        await RisingEdge(dut.clk)
    dut.rst_n.value = 1
    await FallingEdge(dut.clk)

    for i in range(3):
        dut.wr_en.value = 1
        dut.wr_data.value = 0x40 + i
        await RisingEdge(dut.clk)
        await Timer(1, units="ns")
    dut.wr_en.value = 0
    assert int(dut.count.value) == 3, f"count={int(dut.count.value)}"
    cocotb.log.info("three writes, count==3 -- the Week-3 smoke is satisfied")
