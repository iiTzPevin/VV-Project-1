"""STEP 0 -- where Session 1 left us: 7/8 on the released pool.

Uniform-random stimulus, a scoreboard that checks count, full, empty and the
FWFT head. One mutant still survives: `ignore_full` (writes accepted while
full). Look at the histogram before you look at the score -- with this seed the
FIFO never fills, so the overflow bug is never exercised. You cannot detect a
fault you never reach.
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


@cocotb.test()
async def test_unshaped(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    model = FifoModel(WIDTH, DEPTH)
    seed()
    await reset(dut)
    model.reset()

    txn, counts = FifoTxn(), []
    for _ in range(200):
        txn.randomize()
        wr, rd, data = int(txn.wr_en), int(txn.rd_en), int(txn.wr_data)
        model.step(wr, data, rd)
        await apply(dut, wr, rd, data)
        check(dut, model)
        counts.append(model.count)
        await FallingEdge(dut.clk)

    report(dut, counts)
