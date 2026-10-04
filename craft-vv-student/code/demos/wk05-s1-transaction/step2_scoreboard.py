"""STEP 2 -- randomizing more is not the same as checking more.

Stimulus is unchanged from step 1. What changes is what we OBSERVE: full,
empty, and the first-word fall-through head (rd_data) are now compared every
cycle, not just count. Week 1's controllability/observability split, arriving
exactly where you would not expect it.
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


def check(dut, model):
    assert int(dut.count.value) == model.count, \
        f"count {int(dut.count.value)} != model {model.count}"
    assert bool(dut.full.value) == model.full, \
        f"full {bool(dut.full.value)} != model {model.full}"
    assert bool(dut.empty.value) == model.empty, \
        f"empty {bool(dut.empty.value)} != model {model.empty}"
    if not model.empty:                       # FWFT: head valid only when !empty
        assert int(dut.rd_data.value) == model.head, \
            f"rd_data {int(dut.rd_data.value):#04x} != head {model.head:#04x}"


@cocotb.test()
async def test_full_scoreboard(dut):
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
