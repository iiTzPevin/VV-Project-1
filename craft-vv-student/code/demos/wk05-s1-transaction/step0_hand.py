"""STEP 0 -- where Week 4 left us: hand-written vectors.

Four writes, four reads, count checked against the model. It passes. It also
never fills the FIFO, never empties it after the first cycle, and never looks
at rd_data. Run it, then look at the histogram.
"""
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge

from models.fifo_model import FifoModel
from demo_common import reset, apply, report, seed, WIDTH, DEPTH


@cocotb.test()
async def test_hand_vectors(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    model = FifoModel(WIDTH, DEPTH)
    seed()
    await reset(dut)
    model.reset()

    counts = []
    sequence = [(1, 0, 0xA0), (1, 0, 0xA1), (1, 0, 0xA2), (1, 0, 0xA3),
                (0, 1, 0x00), (0, 1, 0x00), (0, 1, 0x00), (0, 1, 0x00)]
    for wr, rd, data in sequence:
        model.step(wr, data, rd)
        await apply(dut, wr, rd, data)
        assert int(dut.count.value) == model.count, \
            f"count {int(dut.count.value)} != model {model.count}"
        counts.append(model.count)
        await FallingEdge(dut.clk)

    report(dut, counts)
