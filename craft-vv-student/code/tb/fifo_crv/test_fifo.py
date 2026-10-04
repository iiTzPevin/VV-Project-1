"""STUDENT STARTER -- Week 5 constrained-random FIFO testbench (pyvsc).

Goal: replace directed stimulus with a @vsc.randobj transaction and a proper
scoreboard so the constrained-random suite finds the whole FIFO mutant pool.

Right now this is deliberately weak: the transaction is uniform random (no bias
toward the boundaries), the run is short, and the scoreboard checks *only*
count. That leaves the full/empty flags, the FWFT head (rd_data), pointer wrap,
and the simultaneous-read+write corner completely unchecked -- raise the
found/total by finishing the TODOs.

Run:    make SIM=icarus
Score:  cd code && just mutate fifo_crv            # released pool
        cd code && just mutate fifo_crv hidden     # hidden pool (grading)
"""
import random

import cocotb
import vsc
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, Timer

from models.fifo_model import FifoModel

WIDTH = 8
DEPTH = 8
MASK = (1 << WIDTH) - 1


@vsc.randobj
class FifoTxn:
    def __init__(self, width=WIDTH):
        self.wr_en = vsc.rand_bit_t(1)
        self.rd_en = vsc.rand_bit_t(1)
        self.wr_data = vsc.rand_bit_t(width)

    # TODO: add a non-random `count` field and constraints that bias wr_en/rd_en
    # toward the boundaries (write hard when nearly empty, read hard when nearly
    # full) and force frequent simultaneous read+write. Uniform random rarely
    # fills or drains an 8-deep FIFO.


@cocotb.test()
async def test_crv(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    model = FifoModel(WIDTH, DEPTH)

    # reset
    dut.wr_en.value = 0
    dut.rd_en.value = 0
    dut.wr_data.value = 0
    dut.rst_n.value = 0
    for _ in range(3):
        await RisingEdge(dut.clk)
    dut.rst_n.value = 1
    model.reset()
    await FallingEdge(dut.clk)

    random.seed(1)
    txn = FifoTxn()
    for _ in range(40):                      # TODO: far too short to fill/drain
        txn.randomize()
        wr, rd, data = int(txn.wr_en), int(txn.rd_en), int(txn.wr_data)
        dut.wr_en.value = wr
        dut.rd_en.value = rd
        dut.wr_data.value = data
        model.step(wr, data, rd)
        await RisingEdge(dut.clk)
        await Timer(1, units="ns")
        # weak scoreboard: only the count is compared to the model
        assert int(dut.count.value) == model.count, \
            f"count {int(dut.count.value)} != model {model.count}"
        # TODO: also check full, empty, and rd_data (the FWFT head) every cycle.
        await FallingEdge(dut.clk)
