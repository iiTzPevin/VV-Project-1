"""STEP 0 -- the environment you inherit: Week 5's shaping plus two lines of
hygiene. Green, boundaries parked -- and blind.

Someone tidied the shaped environment from Week 5. The reasoning reads well:
a write while full is wasted, a read while empty asks for an undefined head,
so `c_tidy` forbids generating either. The histogram still shows residency on
both boundaries. The scoreboard still checks count, full, empty and the FWFT
head every cycle. The run is green.

Scored against the released pool: 6/8. `ignore_full` and `ignore_empty` are
back -- the two mutants Week 5 spent a session pinning down. Some stimulus
disappeared, the histogram cannot say which, and nothing in this file
measures it. The instrument that can is what this session builds.
"""
import cocotb
import vsc
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge

from models.fifo_model import FifoModel
from demo_common import reset, apply, report, seed, check, WIDTH, DEPTH

FILL, DRAIN = 0, 1
PHASE_LEN = 25
CYCLES = 250


@vsc.randobj
class FifoTxn:
    """Week 5 step 4's hand shaping (one uniform roll, plain implications),
    plus the two boundary guards the tidy-up added."""

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
        with vsc.implies(self.count == self.depth):
            self.wr_en == 0                   # a write while full is wasted
        with vsc.implies(self.count == 0):
            self.rd_en == 0                   # nothing to read -- don't ask


@cocotb.test()
async def test_blind(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    model = FifoModel(WIDTH, DEPTH)
    seed()
    await reset(dut)
    model.reset()

    txn, counts = FifoTxn(), []
    for cycle in range(CYCLES):
        txn.phase = FILL if (cycle // PHASE_LEN) % 2 == 0 else DRAIN
        txn.count = model.count
        txn.randomize()
        wr, rd, data = int(txn.wr_en), int(txn.rd_en), int(txn.wr_data)
        model.step(wr, data, rd)
        await apply(dut, wr, rd, data)
        check(dut, model)
        counts.append(model.count)
        await FallingEdge(dut.clk)

    report(dut, counts)
