"""STEP 4 -- shaping that survives measurement.

Since `dist` will not shape inside an implication, shape it by hand: draw one
uniform `roll` and turn it into the enables with plain implications. Verbose,
but every line does what it says, and the instrument agrees.

    FILL   write while roll < 85, read while roll < 10   (drift about +0.75)
    DRAIN  read  while roll < 85, write while roll < 10   (drift about -0.75)

The 10% overlap keeps simultaneous read+write in the stream -- a corner worth
holding on to, and one the FIFO handles with a `default: cnt <= cnt`.

Occupancy becomes a sawtooth that PARKS at full and at empty for runs of
cycles, instead of grazing them when a seed happens to cooperate.
"""
import cocotb
import vsc
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge

from models.fifo_model import FifoModel
from demo_common import (reset, apply, report, seed, check, measure_stimulus,
                         WIDTH, DEPTH)

FILL, DRAIN = 0, 1
PHASE_LEN = 25


@vsc.randobj
class FifoTxn:
    def __init__(self):
        self.wr_en = vsc.rand_bit_t(1)
        self.rd_en = vsc.rand_bit_t(1)
        self.wr_data = vsc.rand_bit_t(WIDTH)
        self.roll = vsc.rand_uint8_t()       # one uniform draw, 0..99
        self.phase = vsc.uint8_t(FILL)        # NOT random: set by the driver

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


@cocotb.test()
async def test_shaped(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    model = FifoModel(WIDTH, DEPTH)
    seed()

    txn = FifoTxn()
    for phase, name in ((FILL, "FILL"), (DRAIN, "DRAIN")):
        txn.phase = phase
        cocotb.log.info("--- phase %s: same instrument, new constraints ---", name)
        measure_stimulus(txn)

    await reset(dut)
    model.reset()
    counts = []
    for cycle in range(200):
        txn.phase = FILL if (cycle // PHASE_LEN) % 2 == 0 else DRAIN
        txn.randomize()
        wr, rd, data = int(txn.wr_en), int(txn.rd_en), int(txn.wr_data)
        model.step(wr, data, rd)
        await apply(dut, wr, rd, data)
        check(dut, model)
        counts.append(model.count)
        await FallingEdge(dut.clk)

    report(dut, counts)
