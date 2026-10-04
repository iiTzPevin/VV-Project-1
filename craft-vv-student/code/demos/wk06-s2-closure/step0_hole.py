"""STEP 0 -- the hole, re-established: 66.7% cross coverage that will not move.

Tuesday's endpoint. The environment reads well (Week 5 shaping plus two tidy
guards), the scoreboard is green, both single coverpoints are 100% -- and the
cross is stuck at 66.7% with four empty cells:

    (full, write)  (full, simul)  (empty, read)  (empty, simul)

New today: the convergence row. Cross coverage is sampled every 50 cycles,
and it plateaus at 66.7% from the first sample. A plateau is ambiguous --
closure, an unlucky seed, or a bin the constraints cannot reach. More cycles
and more seeds will not answer that; reading the empty bin against the
constraint set will. Do that before step 1: every empty cell needs an enable
that `c_tidy` forces to zero in exactly that occupancy state. The hole is not
bad luck. It is a constraint.

Scored against the released pool: 6/8, `ignore_full` and `ignore_empty`
surviving -- the two mutants that live at the addresses the cross names.
"""
import cocotb
import vsc
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge
from cocotb_coverage.coverage import CoverPoint, CoverCross

from models.fifo_model import FifoModel
from demo_common import (reset, apply, seed, check, occ_bin, op_bin,
                         cov_lines, cov_grid, cov_pct, trace_row,
                         OCC_BINS, OP_BINS, WIDTH, DEPTH)

FILL, DRAIN = 0, 1
PHASE_LEN = 25
CYCLES = 250


@vsc.randobj
class FifoTxn:
    """Week 5's hand shaping, plus the tidy guards that came with the env."""

    def __init__(self):
        self.wr_en = vsc.rand_bit_t(1)
        self.rd_en = vsc.rand_bit_t(1)
        self.wr_data = vsc.rand_bit_t(WIDTH)
        self.roll = vsc.rand_uint8_t()        # one uniform draw, 0..99
        self.phase = vsc.uint8_t(FILL)        # NOT random: set by the driver
        self.count = vsc.uint8_t(0)           # NOT random: fed from the model
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
        # The guards under interrogation today. At full, wr_en is forced low;
        # at empty, rd_en is forced low. Now reread the four empty bins.
        with vsc.implies(self.count == self.depth):
            self.wr_en == 0                   # a write while full is wasted
        with vsc.implies(self.count == 0):
            self.rd_en == 0                   # nothing to read -- don't ask


@CoverPoint("top.occ", xf=lambda count, wr, rd: occ_bin(count), bins=OCC_BINS)
@CoverPoint("top.op", xf=lambda count, wr, rd: op_bin(wr, rd), bins=OP_BINS)
@CoverCross("top.occ_x_op", items=["top.occ", "top.op"])
def sample_coverage(count, wr, rd):
    """One sample per cycle: pre-edge occupancy x requested operation."""
    pass


@cocotb.test()
async def test_hole(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    model = FifoModel(WIDTH, DEPTH)
    seed()
    await reset(dut)
    model.reset()

    txn, trace = FifoTxn(), []
    for cycle in range(CYCLES):
        txn.phase = FILL if (cycle // PHASE_LEN) % 2 == 0 else DRAIN
        txn.count = model.count
        txn.randomize()
        wr, rd, data = int(txn.wr_en), int(txn.rd_en), int(txn.wr_data)
        sample_coverage(model.count, wr, rd)
        model.step(wr, data, rd)
        await apply(dut, wr, rd, data)
        check(dut, model)
        if (cycle + 1) % 50 == 0:
            trace.append((cycle + 1, cov_pct("top.occ_x_op")))
        await FallingEdge(dut.clk)

    cocotb.log.info(cov_lines("top.occ", "top.op", "top.occ_x_op"))
    cocotb.log.info(cov_grid("top.occ_x_op"))
    cocotb.log.info(trace_row(trace))
