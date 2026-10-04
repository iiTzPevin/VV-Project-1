"""STEP 2 -- vacuity: a green assertion that checked nothing.

The DUT is still the planted ignore_full mutant from step 1 -- the overflow
bug is COMPILED IN. The stimulus is Week 5's unshaped random walk: the same
transaction, the same 200 cycles, the same default seed -- the one whose
histogram never reaches full. Watching it: the whole fifo_sva.sv suite, the
Week 5 scoreboard, and step2_vacuity.sv with the student-style overflow
property plus its two covers.

Everything passes. Then read the two numbers printed after the run:
c_full = 0, c_overwrite_seen = 0. The antecedent never fired, so the green
assert judged nothing -- on RTL that drops writes on the floor. Same
command with DEMO_SEED=8: the walk parks on full and the same properties
catch the same bug at the first over-write.
"""
import cocotb
import vsc
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge

from models.fifo_model import FifoModel
from demo_common import DEPTH, WIDTH, apply, check, report, reset, seed


@vsc.randobj
class FifoTxn:                        # Week 5's transaction, unchanged
    def __init__(self):
        self.wr_en = vsc.rand_bit_t(1)
        self.rd_en = vsc.rand_bit_t(1)
        self.wr_data = vsc.rand_bit_t(WIDTH)


@cocotb.test()
async def test_vacuous_green(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    seed()
    model = FifoModel(WIDTH, DEPTH)
    await reset(dut)
    model.reset()

    txn, counts, ante = FifoTxn(), [], 0
    for _ in range(200):
        txn.randomize()
        wr, rd, data = int(txn.wr_en), int(txn.rd_en), int(txn.wr_data)
        ante += int(model.full and wr == 1)    # the antecedent, counted by hand
        model.step(wr, data, rd)
        await apply(dut, wr, rd, data)
        check(dut, model)
        counts.append(model.count)
        await FallingEdge(dut.clk)

    report(dut, counts)
    cocotb.log.info(
        f"antecedent (full && wr_en) held on {ante} of 200 cycles -- "
        f"the [covers] lines below are the tool's own count")
