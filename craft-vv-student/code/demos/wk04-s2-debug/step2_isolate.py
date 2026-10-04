"""STEP 2 -- isolate: the smallest sequence that still fails.
FAILS on the planted DUT, on purpose -- and PASSES once step 3 fixes it.

Two hypotheses died to get here. (1) "The model mishandles simultaneous
read+write" -- Tuesday's classic -- but the divergence-cycle pins read
wr_en=1 rd_en=0; no read was involved. (2) "count is off by a cycle" -- but
shrinking shows 47 mixed vectors were never needed: eight writes are clean
and the ninth alone diverges. Write-only, nine transactions, one operation
type. Whatever is wrong lives in the write path at the full boundary.

The asserts below state the CONTRACT (a full FIFO refuses the ninth write),
so this file is red on the bug and green after the fix -- step 3 reruns it.
Rerun with WAVES=1 for the GTKWave part of the session.
"""
import cocotb

from demo_common import FifoDriver, FifoTxn, seed, DEPTH


@cocotb.test()
async def test_isolate(dut):
    seed()
    drv = FifoDriver(dut)
    await drv.reset()

    # eight writes: fill to the brim, watching the head the whole way
    for i in range(DEPTH):
        await drv.drive(FifoTxn(1, 0, 0xA0 + i))
    cocotb.log.info(
        f"after {DEPTH} writes: count={int(dut.count.value)} "
        f"full={int(dut.full.value)} head=0x{int(dut.rd_data.value):02X}")

    # the ninth write. The contract: refused, nothing changes.
    await drv.drive(FifoTxn(1, 0, 0x5A))
    count = int(dut.count.value)
    full = int(dut.full.value)
    head = int(dut.rd_data.value)
    cocotb.log.info(
        f"after the 9th write (0x5A): count={count} full={full} "
        f"head=0x{head:02X}")
    if head != 0xA0:
        cocotb.log.error(
            f"0xA0 left the FIFO without a read -- head is 0x{head:02X}. "
            f"The 9th write landed on the oldest word: a silent drop.")
    cocotb.log.info("waveform: make STEP=2 WAVES=1, then "
                    "gtkwave sim_build/fifo.fst "
                    "(add clk wr_en full do_wr count wr_ptr rd_ptr)")

    assert count == DEPTH, \
        f"a full FIFO must refuse the 9th write: count {count} != {DEPTH}"
    assert full == 1, f"full must stay asserted, got {full}"
    assert head == 0xA0, \
        f"the oldest word must survive an overflow attempt: head 0x{head:02X}"
    cocotb.log.info("contract holds: the 9th write was refused")
