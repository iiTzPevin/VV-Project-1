"""STEP 1 -- loop the wire back and measure the frame, bit-time by bit-time.

One external wire (txd -> rxd) plus a logic-analyzer capture of it. The test
now checks all three views of the same byte:

  the WIRE   -- start low for 8 clocks, 8 stable data bits, stop high for 8:
                the framing contract, measured sample by sample;
  the DATA   -- what went in comes out, in order, LSB first (this is where
                tx_msb_first / rx_bit_order / tx_data_corrupt die);
  the PULSES -- one rx_valid per frame, frame_err never, on a clean wire.

The first frame is printed row by row so the room reads 0xa5 straight off
the samples. The bound uart_sva.sv checker watches every cycle throughout.
"""
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge

from demo_common import (CLKS_PER_BIT, FRAME, find_frame, frame_report,
                         reset_uart, seed, send, start_loopback,
                         start_rx_watch)

SENT = [0xA5, 0x4B, 0x01, 0x80]     # 0x4B/0x01/0x80 are direction-sensitive


@cocotb.test()
async def test_frame_walk(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    seed()
    await reset_uart(dut)

    trace, got, pulses = [], [], {"valid": 0, "err": 0}
    start_loopback(dut, trace)
    start_rx_watch(dut, got, pulses)

    for b in SENT:
        await send(dut, b)
        for _ in range(FRAME + 2 * CLKS_PER_BIT):
            await RisingEdge(dut.clk)

    assert got == SENT, f"loopback: sent={[hex(b) for b in SENT]} " \
                        f"got={[hex(b) for b in got]}"
    assert pulses["err"] == 0, f"frame_err pulsed {pulses['err']}x on a clean wire"

    # walk every frame in the capture; print the first one in full
    idx = 0
    for n, b in enumerate(SENT):
        idx = find_frame(trace, idx)
        assert idx is not None, f"frame {n} never appeared on the wire"
        val, text = frame_report(trace, idx)
        assert val == b, f"frame {n}: wire reads {val:#04x}, sent {b:#04x}"
        if n == 0:
            cocotb.log.info(text)
        idx += 10 * CLKS_PER_BIT
    cocotb.log.info(f"{len(SENT)} frames measured on the wire; "
                    f"rx_valid pulsed {pulses['valid']}x; "
                    f"frame_err {pulses['err']}x")
