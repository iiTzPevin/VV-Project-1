"""STEP 1 -- close the hole by a constraint change, not a directed test.

The tempting fix is a directed epilogue: fill the FIFO, force wr_en for two
cycles, exit. It would light exactly one cell, (full, write), and leave its
three siblings dark -- a patch on the number, not on the stimulus. The report
said four cells; the diagnosis (step 0) said all four are forced off by one
constraint. So the fix is the constraint: `c_tidy` is deleted, nothing is
added. The guards bought no correctness -- the DUT already ignores a write
while full and a read while empty, and the spec says driving both is legal.
What they bought was unreachability.

With the guards gone the Week 5 shaping already visits the boundary cells:
the 10% enable overlap puts writes and simultaneous read+writes on a parked-
full FIFO, reads and simultaneous ops on a parked-empty one. The convergence
row steps up and closes; the final assert makes closure a checked claim, so a
future edit that reopens the hole fails the run instead of shipping.

Scored against the released pool: 8/8 -- `ignore_full` and `ignore_empty`
fall the first time the stimulus reaches their cells. Same scoreboard,
same cycle budget; the only edit in this file is a deletion.
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
    """Week 5's hand shaping. `c_tidy` is gone -- that deletion is the fix."""

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

    # c_tidy deleted. It forced wr_en low at full and rd_en low at empty --
    # which is a sentence that names all four empty bins of step 0.


@CoverPoint("top.occ", xf=lambda count, wr, rd: occ_bin(count), bins=OCC_BINS)
@CoverPoint("top.op", xf=lambda count, wr, rd: op_bin(wr, rd), bins=OP_BINS)
@CoverCross("top.occ_x_op", items=["top.occ", "top.op"])
def sample_coverage(count, wr, rd):
    """One sample per cycle: pre-edge occupancy x requested operation."""
    pass


@cocotb.test()
async def test_close(dut):
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

    # Closure is a checked claim, not a screenshot. Reopen the hole and this
    # run fails. (Holds for seeds 1..10 at this cycle budget; worst measured
    # closure was cycle 201.)
    assert cov_pct("top.occ_x_op") == 100.0, \
        f"cross stuck at {cov_pct('top.occ_x_op'):.1f}% -- a bin went unreachable"
