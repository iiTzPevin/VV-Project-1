"""STUDENT STARTER -- Week 7 assertion-based verification of the UART.

The SVA checker in dut/uart_sva.sv is bound into the UART and compiled with
`--assert`. Its properties pin the 8N1 framing contract positionally: start
low, stop high, line stable within a bit-time, ready exactly while idle,
rx_valid/frame_err mutually exclusive, rx_data gated by rx_valid.

An assertion only fires on a bug your STIMULUS reaches. This starter sends one
byte and never looks at the receive side, so most of the contract is never
exercised and the found/total score is low. Raise it:
  * loop txd back to rxd and scoreboard the data through (LSB-first order),
  * measure the frame on the wire (start width, per-bit width, stop width),
  * drive rxd directly with a BAD-STOP frame -- frame_err, not rx_valid,
  * drive a glitch (short low pulse) -- neither pulse, rx_data untouched,
  * hammer tx_valid mid-frame -- the frame in flight must not change.

Run:     make
Score:   cd code && just mutate uart_sva      # released pool, found/total
"""
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, Timer

CLKS_PER_BIT = 8


async def reset(dut):
    dut.tx_valid.value = 0
    dut.tx_data.value = 0
    dut.rxd.value = 1
    dut.rst_n.value = 0
    for _ in range(3):
        await RisingEdge(dut.clk)
    dut.rst_n.value = 1
    await FallingEdge(dut.clk)


@cocotb.test()
async def test_smoke(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset(dut)

    # send one byte and wait roughly a frame
    dut.tx_data.value = 0xA5
    dut.tx_valid.value = 1
    await RisingEdge(dut.clk)
    await Timer(1, units="ns")
    dut.tx_valid.value = 0
    for _ in range(12 * CLKS_PER_BIT):
        await RisingEdge(dut.clk)

    # weak check: the transmitter came back to ready
    assert int(dut.tx_ready.value) == 1, "tx never returned to ready"
    # TODO: loop back txd->rxd and check rx_data == what was sent.
    # TODO: measure start/data/stop widths on txd against CLKS_PER_BIT.
    # TODO: bad-stop frame on rxd -> frame_err pulses, rx_valid does not.
    # TODO: glitch on rxd -> no pulse, rx_data unchanged.
