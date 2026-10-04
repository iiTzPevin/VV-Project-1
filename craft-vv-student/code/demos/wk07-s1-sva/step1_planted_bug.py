"""STEP 1 -- the same walk, one planted bug: the checker fires by name.

The stimulus is byte-for-byte step 0's -- the import below is the whole file.
What changed is the DUT: the Makefile planted the released `ignore_full`
mutant (writes commit while full) into a scratch copy of fifo.sv via
plant_bug.py. The over-writes sit in the blind stretch, where the scoreboard
never looks, and every check() that runs before them still passes. The bound
property does not wait to be called: a_no_overflow samples full and do_wr at
the offending edge and stops the sim with the property name and the cycle.

This step is kept broken on purpose. Expect (130 ns = the first blind
over-write edge):

  [130000] %Error: fifo_sva.sv:40: Assertion failed in
           fifo.u_sva.a_no_overflow: 'assert' failed.
"""
import cocotb
from cocotb.clock import Clock

from models.fifo_model import FifoModel
from demo_common import DEPTH, WIDTH, reset, seed
from step0_two_checkers import corner_walk


@cocotb.test()
async def test_planted_bug(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    seed()
    model = FifoModel(WIDTH, DEPTH)
    await reset(dut)
    model.reset()
    await corner_walk(dut, model)     # never finishes: fires in the blind stretch
