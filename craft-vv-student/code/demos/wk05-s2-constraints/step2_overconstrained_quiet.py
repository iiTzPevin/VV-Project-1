"""STEP 2 -- over-constraint, the quiet kind. This is the dangerous one.

Remove the contradiction. Keep one guard that looks like good hygiene:

    don't let it overflow    count >= DEPTH-1 -> rd_en == 1

The solver is happy. Every cycle is legal. Nothing errors, the test is green,
and the suite looks healthy. It also can no longer reach `full` -- so the
overflow mutant is now undetectable by construction. An over-constraint that
throws is a bug you fix in ten minutes; an over-constraint that solves is a
hole in your coverage argument that survives to tape-out.
"""
import cocotb
import vsc
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge

from models.fifo_model import FifoModel
from demo_common import reset, apply, report, seed, check, WIDTH, DEPTH


@vsc.randobj
class FifoTxn:
    def __init__(self):
        self.wr_en = vsc.rand_bit_t(1)
        self.rd_en = vsc.rand_bit_t(1)
        self.wr_data = vsc.rand_bit_t(WIDTH)
        self.count = vsc.uint8_t(0)
        self.depth = vsc.uint8_t(DEPTH)

    @vsc.constraint
    def c_never_idle(self):
        self.wr_en + self.rd_en >= 1

    @vsc.constraint
    def c_no_simultaneous(self):
        self.wr_en + self.rd_en <= 1

    @vsc.constraint
    def c_dont_overflow(self):               # <-- the plausible-looking guard
        with vsc.implies(self.count >= self.depth - 1):
            self.rd_en == 1


@cocotb.test()
async def test_overconstrained_quiet(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    model = FifoModel(WIDTH, DEPTH)
    seed()
    await reset(dut)
    model.reset()

    txn, counts = FifoTxn(), []
    for _ in range(200):
        txn.count = model.count
        txn.randomize()
        wr, rd, data = int(txn.wr_en), int(txn.rd_en), int(txn.wr_data)
        model.step(wr, data, rd)
        await apply(dut, wr, rd, data)
        check(dut, model)
        counts.append(model.count)
        await FallingEdge(dut.clk)

    report(dut, counts)
