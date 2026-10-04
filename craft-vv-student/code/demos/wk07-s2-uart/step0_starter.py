"""STEP 0 -- where the starter leaves you: one byte, one weak check, 3/8.

This is tb/uart_sva's test_smoke in substance: send one byte, wait about a
frame, confirm the transmitter came back to ready. The bound checker
(dut/uart_sva.sv, compiled with --assert) already fires on any mutant that
breaks the frame SHAPE of any transmission -- start level, stop level,
ready-only-in-idle -- which is why even this run scores 3/8 and not 0/8.

What nothing here checks is the DATA and the RECEIVER: no loopback, no look
at rx_data, no error path. All five survivors on the released pool are data
or receive-side bugs. An assertion only fires on a bug the stimulus reaches
and the property watches -- the next two steps buy the rest.
"""
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge

from demo_common import CLKS_PER_BIT, reset_uart, seed, send


@cocotb.test()
async def test_starter(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    seed()
    await reset_uart(dut)

    await send(dut, 0xA5)
    for _ in range(12 * CLKS_PER_BIT):       # wait out roughly a frame
        await RisingEdge(dut.clk)

    assert int(dut.tx_ready.value) == 1, "tx never returned to ready"
    cocotb.log.info("one byte sent, tx_ready high again -- "
                    "and that is all this run checked")
