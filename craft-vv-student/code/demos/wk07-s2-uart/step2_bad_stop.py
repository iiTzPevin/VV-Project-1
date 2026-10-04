"""STEP 2 -- forge a bad stop bit: frame_err must pulse, rx_valid must not.

The receiver's contract on a framing violation has three clauses: frame_err
pulses exactly once, rx_valid stays silent, rx_data keeps its old value.
The transmitter refuses to produce a broken frame, so drive rxd directly
and forge the stop bit low. Then prove recovery: the next clean frame is
received as if nothing happened.

Step 1's loopback walk still runs first, unchanged -- the import below is
the whole diff. This is the error path the starter never drove, and it is
what catches rx_err_silent (a bad stop bit swallowed). Cumulative score on
the released pool: 8/8.
"""
import cocotb
from cocotb.clock import Clock

from demo_common import drive_frame, reset_uart, seed, start_rx_watch
from step1_frame_walk import test_frame_walk        # step 1 rides along


@cocotb.test()
async def test_bad_stop(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    seed()
    await reset_uart(dut)

    got, pulses = [], {"valid": 0, "err": 0}
    start_rx_watch(dut, got, pulses)
    before = int(dut.rx_data.value)

    await drive_frame(dut, 0x5A, stop_level=0)      # stop bit forged low
    assert pulses["err"] == 1, \
        f"bad stop: frame_err pulsed {pulses['err']}x, want exactly 1"
    assert pulses["valid"] == 0, "bad stop: rx_valid pulsed on a broken frame"
    assert int(dut.rx_data.value) == before, "rx_data changed on a rejected frame"
    cocotb.log.info("bad stop: frame_err 1x, rx_valid 0x, rx_data untouched")

    await drive_frame(dut, 0xC3, stop_level=1)      # clean frame: recovery
    assert pulses["valid"] == 1 and got == [0xC3], \
        f"recovery: valid={pulses['valid']} got={[hex(b) for b in got]}"
    assert pulses["err"] == 1, "spurious frame_err after recovery"
    cocotb.log.info("recovery: next clean frame lands, rx_data = 0xc3")
