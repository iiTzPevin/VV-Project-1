"""STEP 3 -- write the shaping you would obviously write. Then measure it.

The instinct is a phase field and a weighted distribution per phase:

    with vsc.implies(self.phase == FILL):
        vsc.dist(self.wr_en, [vsc.weight(1, 85), vsc.weight(0, 15)])
    with vsc.implies(self.phase == DRAIN):
        vsc.dist(self.wr_en, [vsc.weight(0, 80), vsc.weight(1, 20)])

It reads correctly. It solves without complaint. Every transaction is legal.
And it shapes almost nothing.

The reason is not that the tool drops the constraint. It is that **`dist`
ignores the `implies` that encloses it**: the weighted distribution is applied
to the field unconditionally, in every phase, whatever the guard says. Write
two phase-conditional distributions on the same field and both apply all the
time -- 85/15 and 20/80 average out to roughly uniform, and the shaping
cancels itself.

Hard relational constraints inside `implies` ARE gated correctly (step 1 proved
that: the contradiction only appeared at count == DEPTH). The defect is
specific to `dist`.

This test does two measurements. The first shows the cancellation. The second
is the decisive one: a transaction with a SINGLE guarded `dist`, measured in
the phase where the guard is false. If the distribution is still there, the
guard was never honored -- and that is the whole finding in one number.
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
        self.phase = vsc.uint8_t(FILL)

    @vsc.constraint
    def c_phase(self):
        with vsc.implies(self.phase == FILL):
            vsc.dist(self.wr_en, [vsc.weight(1, 85), vsc.weight(0, 15)])
            vsc.dist(self.rd_en, [vsc.weight(0, 80), vsc.weight(1, 20)])
        with vsc.implies(self.phase == DRAIN):
            vsc.dist(self.wr_en, [vsc.weight(0, 80), vsc.weight(1, 20)])
            vsc.dist(self.rd_en, [vsc.weight(1, 85), vsc.weight(0, 15)])


@vsc.randobj
class OneBranchTxn:
    """A single guarded dist. If the guard worked, DRAIN would be ~0.50."""

    def __init__(self):
        self.wr_en = vsc.rand_bit_t(1)
        self.rd_en = vsc.rand_bit_t(1)
        self.phase = vsc.uint8_t(FILL)

    @vsc.constraint
    def c_only_fill(self):
        with vsc.implies(self.phase == FILL):
            vsc.dist(self.wr_en, [vsc.weight(1, 85), vsc.weight(0, 15)])


@cocotb.test()
async def test_dist_trap(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    model = FifoModel(WIDTH, DEPTH)
    seed()

    txn = FifoTxn()
    for phase, name in ((FILL, "FILL"), (DRAIN, "DRAIN")):
        txn.phase = phase
        cocotb.log.info("--- phase %s: what did the constraints buy us? ---", name)
        measure_stimulus(txn)          # expect ~+-0.07, not ~+-0.65

    # The decisive experiment: ONE dist, guarded to FILL. Read the DRAIN row.
    cocotb.log.info("--- one guarded dist: is the implies honored at all? ---")
    one = OneBranchTxn()
    for phase, name in ((FILL, "guard TRUE "), (DRAIN, "guard FALSE")):
        one.phase = phase
        rates, _ = measure_stimulus(one, n=800, fields=("wr_en",))
        cocotb.log.info("    %s -> P(wr_en=1) = %.2f", name, rates["wr_en"])
    cocotb.log.info("    Both near 0.85: the dist applies whether or not the "
                    "guard holds. `implies` does not gate `dist`.")

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
