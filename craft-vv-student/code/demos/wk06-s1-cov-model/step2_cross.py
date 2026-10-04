"""STEP 2 -- the cross. Same stimulus, same checks, one added decorator.

`CoverCross` pairs every occupancy bin with every operation bin: 12 cells.
The headline drops from two green 100% lines to 66.7%, and the grid shows
why: four cells are empty, and they are not four random cells --

    (full, write)  (full, simul)  (empty, read)  (empty, simul)

the four boundary interactions. Two of them are the addresses of the two
surviving mutants: a write issued while full is the only stimulus that can
expose `ignore_full`; a read issued while empty, the only one for
`ignore_empty`. Both single coverpoints were green because every row and
every column has hits somewhere -- the cross is what notices the pairs that
never met. A model without it could not have asked the question, and closing
these cells is Thursday's session.
"""
import cocotb
import vsc
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge
from cocotb_coverage.coverage import CoverPoint, CoverCross

from models.fifo_model import FifoModel
from demo_common import (reset, apply, seed, check, occ_bin, op_bin,
                         cov_lines, cov_grid, OCC_BINS, OP_BINS, WIDTH, DEPTH)

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


@CoverPoint("top.occ", xf=lambda count, wr, rd: occ_bin(count), bins=OCC_BINS)
@CoverPoint("top.op", xf=lambda count, wr, rd: op_bin(wr, rd), bins=OP_BINS)
@CoverCross("top.occ_x_op", items=["top.occ", "top.op"])   # <- the added line
def sample_coverage(count, wr, rd):
    """One sample per cycle: pre-edge occupancy x requested operation."""
    pass


@cocotb.test()
async def test_cross(dut):
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

    cocotb.log.info(cov_lines("top.occ", "top.op", "top.occ_x_op"))
    cocotb.log.info(cov_grid("top.occ_x_op"))
