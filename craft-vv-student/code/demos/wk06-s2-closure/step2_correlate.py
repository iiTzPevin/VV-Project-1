"""STEP 2 -- correlate: does closing coverage move found/total?

Both environments, back to back in one run, same seed, same cycle budget,
same scoreboard. The only difference is `c_tidy` -- present in TxnGuarded,
absent in TxnOpen. Each drives its own copy of the coverage model
(`before.*` / `after.*`), and the run ends with the two rows side by side.

Coverage this file measures; found/total the harness measures. Score each
environment separately (the commands are in DEMO.md, results in the table):

    before  (step 0, guarded)   cross  66.7%   found 6/8
    after   (step 1, open)      cross 100.0%   found 8/8

The two numbers moved together, and for a reason you can point at: the empty
cells were the only stimulus that reaches `ignore_full` and `ignore_empty`.
Closing coverage raised found/total because the missing bins were missing
REACHES. That is the correlation the homework asks you to report -- and when
the two curves ever diverge (coverage climbing, finds flat), you have found a
fault your model cannot see. Step 3 builds one on purpose.
"""
import cocotb
import vsc
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge
from cocotb_coverage.coverage import CoverPoint, CoverCross

from models.fifo_model import FifoModel
from demo_common import (reset, apply, seed, check, occ_bin, op_bin,
                         cov_pct, OCC_BINS, OP_BINS, WIDTH, DEPTH)

FILL, DRAIN = 0, 1
PHASE_LEN = 25
CYCLES = 250


class _Shaping:
    """Week 5's hand shaping, shared by both transactions below."""

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


@vsc.randobj
class TxnGuarded(_Shaping):
    """Step 0's transaction: the tidy guards still in force."""

    @vsc.constraint
    def c_tidy(self):
        with vsc.implies(self.count == self.depth):
            self.wr_en == 0
        with vsc.implies(self.count == 0):
            self.rd_en == 0


@vsc.randobj
class TxnOpen(_Shaping):
    """Step 1's transaction: c_tidy deleted. The whole diff is that absence."""


@CoverPoint("before.occ", xf=lambda count, wr, rd: occ_bin(count), bins=OCC_BINS)
@CoverPoint("before.op", xf=lambda count, wr, rd: op_bin(wr, rd), bins=OP_BINS)
@CoverCross("before.occ_x_op", items=["before.occ", "before.op"])
def sample_before(count, wr, rd):
    pass


@CoverPoint("after.occ", xf=lambda count, wr, rd: occ_bin(count), bins=OCC_BINS)
@CoverPoint("after.op", xf=lambda count, wr, rd: op_bin(wr, rd), bins=OP_BINS)
@CoverCross("after.occ_x_op", items=["after.occ", "after.op"])
def sample_after(count, wr, rd):
    pass


async def drive(dut, txn, sample):
    """One full run: same seed, same budget, same checks for either txn."""
    model = FifoModel(WIDTH, DEPTH)
    seed()
    await reset(dut)
    model.reset()
    for cycle in range(CYCLES):
        txn.phase = FILL if (cycle // PHASE_LEN) % 2 == 0 else DRAIN
        txn.count = model.count
        txn.randomize()
        wr, rd, data = int(txn.wr_en), int(txn.rd_en), int(txn.wr_data)
        sample(model.count, wr, rd)
        model.step(wr, data, rd)
        await apply(dut, wr, rd, data)
        check(dut, model)
        await FallingEdge(dut.clk)


@cocotb.test()
async def test_before_guarded(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await drive(dut, TxnGuarded(), sample_before)


@cocotb.test()
async def test_after_open(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await drive(dut, TxnOpen(), sample_after)

    cocotb.log.info("\n".join([
        "",
        "  env                          cross    found/total (harness)",
        "  ---------------------------  ------   ---------------------",
        f"  before: guarded (step 0)     {cov_pct('before.occ_x_op'):5.1f}%   score step 0",
        f"  after:  c_tidy deleted       {cov_pct('after.occ_x_op'):5.1f}%   score step 1",
    ]))
