"""STEP 5 -- the regression, not the run.

Session 1 ended on a table nobody liked: unshaped stimulus reached `full`
anywhere from 0 to 39 cycles depending only on the seed. Two seeds in ten never
filled the FIFO at all. Whether that week's regression would have caught an
overflow bug was decided by a number nobody chose on purpose.

Run the shaped stimulus across eight seeds and read the same column. If the
shaping is a property of the testbench rather than of luck, every row reaches
both boundaries and the spread is narrow. That is what makes it a regression.
"""
import cocotb
import vsc
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge

from models.fifo_model import FifoModel
from demo_common import reset, apply, check, WIDTH, DEPTH
from step4_shaped import FifoTxn, FILL, DRAIN, PHASE_LEN

SEEDS = [1, 2, 3, 4, 5, 6, 7, 8]


async def one_seed(dut, s):
    import random
    random.seed(s)
    model = FifoModel(WIDTH, DEPTH)
    await reset(dut)
    model.reset()
    txn = FifoTxn()
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
    return counts.count(0), counts.count(DEPTH)


@cocotb.test()
async def test_seeded_regression(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    rows = ["", "  seed   empty-cycles   full-cycles   both boundaries?",
            "  ----   ------------   -----------   ----------------"]
    worst = 10 ** 9
    for s in SEEDS:
        e, f = await one_seed(dut, s)
        rows.append(f"  {s:>4}   {e:>12}   {f:>11}   "
                    f"{'yes' if e and f else 'NO'}")
        worst = min(worst, min(e, f))
    rows.append(f"  worst boundary residency across {len(SEEDS)} seeds: "
                f"{worst} cycles")
    cocotb.log.info("\n".join(rows))
    assert worst > 0, ("shaping is not a property of the testbench: at least "
                       "one seed never reached a boundary")
