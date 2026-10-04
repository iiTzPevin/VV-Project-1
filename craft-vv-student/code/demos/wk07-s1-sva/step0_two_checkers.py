"""STEP 0 -- two layers of checking, side by side, both green.

The immediate layer is Week 5's scoreboard: a Python assert that checks the
instant check() is called -- and only then. The concurrent layer is new:
dut/fifo_sva.sv is bound inside the FIFO (dut/fifo_bind.sv) and compiled with
--assert, so its properties are sampled at every posedge whether or not the
testbench is looking.

The walk hits every corner -- fill, hold at full, drain, over-read -- and
leaves an 8-cycle BLIND stretch in the middle: stimulus keeps hammering
writes at a full FIFO while check() is never called. On clean RTL nothing is
lost (the over-writes are dropped; the first look after the stretch agrees
with the model), so this step is green everywhere. Step 1 plants a bug
exactly where nobody is looking.
"""
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge

from models.fifo_model import FifoModel
from demo_common import (DEPTH, WIDTH, apply, check, count_sva, reset, seed,
                         sva_path)

stats = {"checks": 0, "blind": 0, "edges": 0}


async def corner_walk(dut, model):
    """Fill to full, hold, go blind while over-writing, drain, over-read.
    Every phase but the blind one ends each cycle with an immediate look."""

    async def drive(wr, rd, data=0, look=True):
        model.step(wr, data, rd)
        await apply(dut, wr, rd, data)
        stats["edges"] += 1
        if look:
            check(dut, model)
            stats["checks"] += 1
        else:
            stats["blind"] += 1
        await FallingEdge(dut.clk)

    for i in range(DEPTH):                    # fill to full, checked
        await drive(1, 0, 0x10 + i)
    for _ in range(2):                        # hold at full, checked
        await drive(0, 0)
    for _ in range(6):                        # BLIND: over-write while full
        await drive(1, 0, 0xEE, look=False)   #   (dropped on clean RTL)
    for _ in range(2):                        # BLIND: idle
        await drive(0, 0, look=False)
    for _ in range(DEPTH):                    # drain to empty, checked
        await drive(0, 1)
    for _ in range(2):                        # over-read while empty, checked
        await drive(0, 1)


@cocotb.test()
async def test_two_checkers(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    seed()
    model = FifoModel(WIDTH, DEPTH)
    await reset(dut)
    model.reset()

    await corner_walk(dut, model)

    n_assert, _ = count_sva(sva_path("fifo_sva.sv"))
    cocotb.log.info(
        f"immediate : check() looked {stats['checks']} times -- "
        f"a Python assert checks only when called")
    cocotb.log.info(
        f"blind     : {stats['blind']} of {stats['edges']} driven cycles "
        f"had no check() call at all")
    cocotb.log.info(
        f"concurrent: {n_assert} properties from dut/fifo_sva.sv sampled "
        f"at every posedge, blind cycles included")
