"""STUDENT STARTER -- Week 6 functional-coverage FIFO testbench.

Goal: build a functional coverage model for the FIFO and drive constrained-
random stimulus until it closes, while scoreboarding against the golden model.

Right now this is deliberately weak:
  * the coverage model has only an *operation* coverpoint -- no occupancy
    coverpoint and no CROSS, so it can never tell you whether you exercised
    "write while full" or "read while empty";
  * the stimulus is a short uniform-random burst that rarely fills or drains
    the FIFO; and
  * the scoreboard checks only count.

Finish the TODOs: add the occupancy coverpoint (empty / partial / full), add
the occupancy x operation CROSS, drive (reuse the Week-5 biased @vsc.randobj)
until the cross is fully covered, and check full/empty/rd_data every cycle.

Run:    make SIM=icarus
Score:  cd code && just mutate fifo_cov            # released pool
        cd code && just mutate fifo_cov hidden     # hidden pool (grading)
"""
import random

import cocotb
import vsc
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, Timer
from cocotb_coverage.coverage import CoverPoint, coverage_db

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
    # TODO: add a `count` field + boundary-biasing constraints (Week 5) so the
    # stimulus actually reaches empty and full.


def op_bin(wr_en, rd_en):
    if wr_en and rd_en:
        return "simul"
    if wr_en:
        return "write"
    if rd_en:
        return "read"
    return "idle"


# TODO: add a CoverPoint("top.occ", ...) for occupancy (empty/partial/full) and
# a CoverCross("top.occ_x_op", ...) so boundary operations become coverage bins.
@CoverPoint("top.op", xf=lambda wr, rd: op_bin(wr, rd),
            bins=["idle", "write", "read", "simul"])
def sample_coverage(wr, rd):
    pass


@cocotb.test()
async def test_coverage(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    model = FifoModel(WIDTH, DEPTH)

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
    for _ in range(60):                       # TODO: drive until coverage closes
        txn.randomize()
        wr, rd, data = int(txn.wr_en), int(txn.rd_en), int(txn.wr_data)
        sample_coverage(wr, rd)
        dut.wr_en.value = wr
        dut.rd_en.value = rd
        dut.wr_data.value = data
        model.step(wr, data, rd)
        await RisingEdge(dut.clk)
        await Timer(1, units="ns")
        assert int(dut.count.value) == model.count, \
            f"count {int(dut.count.value)} != model {model.count}"
        # TODO: also check full, empty, and rd_data every cycle.
        await FallingEdge(dut.clk)

    op = coverage_db["top.op"].cover_percentage
    dut._log.info(f"operation coverage = {op:.2f}%  (occupancy + cross: TODO)")
