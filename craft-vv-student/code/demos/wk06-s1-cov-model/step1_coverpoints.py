"""STEP 1 -- the first two coverpoints: occupancy and operation.

Stimulus and scoreboard are step 0, unchanged. The additions are passive:
two sampled coverpoints, occupancy in {empty, partial, full} and operation in
{idle, write, read, simul}. Each sample records "which operation was issued
in which occupancy state" -- pre-edge count, requested enables -- which is why
`sample_coverage` runs before `model.step`.

Both coverpoints report 100%: every occupancy state was visited, every
operation was issued. The odometer agrees with the histogram -- and it is
measuring the wrong thing. It counts the two axes separately, so it cannot
see that particular (state, operation) pairs never met. The score is still
6/8; nothing on this screen explains why.
"""
import cocotb
import vsc
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge
from cocotb_coverage.coverage import CoverPoint

from models.fifo_model import FifoModel
from demo_common import (reset, apply, seed, check, occ_bin, op_bin,
                         cov_lines, OCC_BINS, OP_BINS, WIDTH, DEPTH)

FILL, DRAIN = 0, 1
PHASE_LEN = 25
CYCLES = 250


@vsc.randobj
class FifoTxn:
    """The step 0 transaction, unchanged: shaping plus the tidy guards."""

    def __init__(self):
        self.wr_en = vsc.rand_bit_t(1)
        self.rd_en = vsc.rand_bit_t(1)
        self.wr_data = vsc.rand_bit_t(WIDTH)
        self.roll = vsc.rand_uint8_t()
        self.phase = vsc.uint8_t(FILL)
        self.count = vsc.uint8_t(0)
        self.depth = vsc.uint8_t(DEPTH)

    @vsc.constraint
    def c_roll(self):
        self.roll in vsc.rangelist(vsc.rng(0, 99))

    @vsc.constraint
    def c_phase(self):
        with vsc.implies(self.phase == FILL):
            with vsc.implies(self.roll < 85):
                self.wr_en == 1
            with vsc.implies(self.roll >= 85):
                self.wr_en == 0
            with vsc.implies(self.roll < 10):
                self.rd_en == 1
            with vsc.implies(self.roll >= 10):
                self.rd_en == 0
        with vsc.implies(self.phase == DRAIN):
            with vsc.implies(self.roll < 85):
                self.rd_en == 1
            with vsc.implies(self.roll >= 85):
                self.rd_en == 0
            with vsc.implies(self.roll < 10):
                self.wr_en == 1
            with vsc.implies(self.roll >= 10):
                self.wr_en == 0

    @vsc.constraint
    def c_tidy(self):
        with vsc.implies(self.count == self.depth):
            self.wr_en == 0
        with vsc.implies(self.count == 0):
            self.rd_en == 0


# The model, straight from the Week 2 vplan: occupancy states and operations.
@CoverPoint("top.occ", xf=lambda count, wr, rd: occ_bin(count), bins=OCC_BINS)
@CoverPoint("top.op", xf=lambda count, wr, rd: op_bin(wr, rd), bins=OP_BINS)
def sample_coverage(count, wr, rd):
    """One sample per cycle: pre-edge occupancy x requested operation."""
    pass


@cocotb.test()
async def test_coverpoints(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    model = FifoModel(WIDTH, DEPTH)
    seed()
    await reset(dut)
    model.reset()

    txn = FifoTxn()
    for cycle in range(CYCLES):
        txn.phase = FILL if (cycle // PHASE_LEN) % 2 == 0 else DRAIN
        txn.count = model.count
        txn.randomize()
        wr, rd, data = int(txn.wr_en), int(txn.rd_en), int(txn.wr_data)
        sample_coverage(model.count, wr, rd)      # sample BEFORE the edge
        model.step(wr, data, rd)
        await apply(dut, wr, rd, data)
        check(dut, model)
        await FallingEdge(dut.clk)

    cocotb.log.info(cov_lines("top.occ", "top.op"))
