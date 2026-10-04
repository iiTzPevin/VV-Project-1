"""STEP 1 -- over-constraint, the loud kind.

Four constraints, each defensible on its own:
    never idle            wr_en | rd_en == 1
    no simultaneous r/w   wr_en + rd_en <= 1
    keep the pipe busy    wr_en == 1
    drain when full       count == DEPTH -> rd_en == 1

Together they are unsatisfiable -- but ONLY once the FIFO actually fills. The
run is green for dozens of cycles, then the solver has nowhere to go. This is
what a real over-constraint bug looks like: latent until a state is reached.

Expect a SolveFailure. That is the point of the step; do not "fix" it yet.
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
        self.count = vsc.uint8_t(0)          # NOT random: the current occupancy
        self.depth = vsc.uint8_t(DEPTH)

    @vsc.constraint
    def c_never_idle(self):
        self.wr_en + self.rd_en >= 1

    @vsc.constraint
    def c_no_simultaneous(self):
        self.wr_en + self.rd_en <= 1

    @vsc.constraint
    def c_keep_busy(self):
        self.wr_en == 1

    @vsc.constraint
    def c_drain_when_full(self):
        with vsc.implies(self.count == self.depth):
            self.rd_en == 1


@cocotb.test()
async def test_overconstrained(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    model = FifoModel(WIDTH, DEPTH)
    seed()
    await reset(dut)
    model.reset()

    txn, counts = FifoTxn(), []
    for cycle in range(200):
        txn.count = model.count
        try:
            txn.randomize()
        except vsc.SolveFailure:
            cocotb.log.error(
                f"solver found no legal transaction at cycle {cycle}, "
                f"occupancy = {model.count}")
            report(dut, counts)
            raise
        wr, rd, data = int(txn.wr_en), int(txn.rd_en), int(txn.wr_data)
        model.step(wr, data, rd)
        await apply(dut, wr, rd, data)
        check(dut, model)
        counts.append(model.count)
        await FallingEdge(dut.clk)

    report(dut, counts)
