"""STUDENT STARTER -- Week 7 assertion-based verification of the FWFT FIFO.

The SVA checker in dut/fifo_sva.sv is already *bound* into the FIFO and
compiled with `--assert` (see the Makefile). Those concurrent assertions watch
the design every cycle -- but an assertion can only fire on a bug your STIMULUS
actually drives the design into. This starter barely exercises the FIFO, so
most assertions never get a chance to trip and the found/total score is low.

Your job: drive the FIFO through every corner so the bound assertions (and a
data scoreboard) light up on a broken design:
  * fill to full and attempt an over-write (a_no_overflow),
  * drain to empty and attempt an over-read (a_no_underflow),
  * hold with no read while non-empty (a_head_stable),
  * simultaneous read+write, including across a pointer wrap (a_count_hold),
  * and check rd_data order against models.fifo_model.FifoModel (data path).

Run:     make                                   # Verilator + SVA
Score:   python -m craft_mutate.mutate --tb tb/fifo_sva \\
             --pool tb/fifo_sva/mutants_released.yaml --sim verilator

Right now this only does three writes and one weak check -- raise the score.
"""
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, Timer
from models.fifo_model import FifoModel


@cocotb.test()
async def test_smoke(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
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
    # TODO: fill to full and over-write; drain to empty and over-read.
    # TODO: hold with no read while non-empty; do simultaneous read+write + wrap.
    # TODO: scoreboard rd_data order against a FifoModel.
