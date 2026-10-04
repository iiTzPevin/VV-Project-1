"""STEP 3 -- 100% of a weak model, with two mutants alive underneath it.

Take step 0's environment -- the guarded stimulus that cannot write while
full or read while empty -- and swap in a weaker coverage model: the same two
coverpoints, no cross. That is not a strawman; it is the model you will most
often be handed. Ask an AI for a FIFO coverage model and this shape is the
usual answer (CtM-06 has you run that experiment); plenty of humans write it
too, because each coverpoint on its own looks complete.

This run PASSES. The report reads 100%, twice. The final asserts hold, so
the suite certifies itself closed -- and scored against the released pool it
finds 6/8, with `ignore_full` and `ignore_empty` alive. Nothing here is
mysterious: 100% is a statement about the model, and this model contains no
bin that the missing stimulus would have left empty. Coverage bounds your
ignorance exactly as far as the model reaches, and not one cell further.

That is the closure argument HW6 wants in `closure.md`: not "the number is
100," but "here is what my model can see, here is what it cannot, and here
is why I believe the difference is acceptable." One blind spot to name in
yours: no occupancy/operation bin sees a one-cycle glitch on `full` that
leaves the end state correct. No coverpoint in THIS model catches that
fault class either -- which is Week 7's opening problem.
"""
import cocotb
import vsc
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge
from cocotb_coverage.coverage import CoverPoint

from models.fifo_model import FifoModel
from demo_common import (reset, apply, seed, check, occ_bin, op_bin,
                         cov_lines, cov_pct, OCC_BINS, OP_BINS, WIDTH, DEPTH)

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


# The weak model: same coverpoints as step 1 of Session 1 -- and no cross.
@CoverPoint("top.occ", xf=lambda count, wr, rd: occ_bin(count), bins=OCC_BINS)
@CoverPoint("top.op", xf=lambda count, wr, rd: op_bin(wr, rd), bins=OP_BINS)
def sample_coverage(count, wr, rd):
    pass


@cocotb.test()
async def test_weak_model(dut):
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
        sample_coverage(model.count, wr, rd)
        model.step(wr, data, rd)
        await apply(dut, wr, rd, data)
        check(dut, model)
        await FallingEdge(dut.clk)

    cocotb.log.info(cov_lines("top.occ", "top.op"))
    cocotb.log.info("coverage model closed: every bin in the model was hit")

    # The suite certifies itself done. Both asserts hold; the pool disagrees.
    assert cov_pct("top.occ") == 100.0
    assert cov_pct("top.op") == 100.0
