"""STEP 1 -- the transaction becomes the unit of randomization.

Same DUT, same checks, but stimulus now comes from a pyvsc @randobj instead of
a hand-written list. 200 cycles instead of 8. This is a strict improvement --
and the histogram will show it is not nearly enough.
"""
import cocotb
import vsc
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge

from models.fifo_model import FifoModel
from demo_common import reset, apply, report, seed, WIDTH, DEPTH


@vsc.randobj
class FifoTxn:
    def __init__(self):
        self.wr_en = vsc.rand_bit_t(1)
        self.rd_en = vsc.rand_bit_t(1)
        self.wr_data = vsc.rand_bit_t(WIDTH)


@cocotb.test()
async def test_uniform_random(dut):
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
        assert int(dut.count.value) == model.count, \
            f"count {int(dut.count.value)} != model {model.count}"
        counts.append(model.count)
        await FallingEdge(dut.clk)

    report(dut, counts)
