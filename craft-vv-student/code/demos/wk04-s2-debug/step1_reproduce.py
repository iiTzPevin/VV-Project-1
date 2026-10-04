"""STEP 1 -- reproduce: Tuesday's layered testbench, unchanged, on the
planted DUT. FAILS, on purpose -- keep it failing.

Everything here is imported from demo_common, which carries Session 1's
driver, monitor, scoreboard, and the five sequences verbatim. Reproducing
the bug costs ten lines, because the testbench was built to be reused.
The scoreboard's `first divergence` line names the cycle and shows the pins
that cycle -- that line, not the traceback, is where the debug starts.
"""
import cocotb

from demo_common import (SEQUENCES, FifoDriver, FifoMonitor, FifoScoreboard,
                         run_sequence, seed, report)


@cocotb.test()
async def test_reproduce(dut):
    seed()
    drv = FifoDriver(dut)
    await drv.reset()
    mon, sb = FifoMonitor(dut), FifoScoreboard()

    applied = []
    for name, seq in SEQUENCES:
        await run_sequence(drv, mon, sb, name, seq, applied)

    report(applied)   # not reached on the planted DUT
