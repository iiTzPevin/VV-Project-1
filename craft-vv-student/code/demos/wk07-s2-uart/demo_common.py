"""Shared helpers for the Week 7 Session 2 demo (UART, then leak_check).
Keeps each step file short enough to read on a projector -- the step files
hold only what the demo is about.
"""
import os
import random

import cocotb
from cocotb.triggers import RisingEdge, FallingEdge, Timer

CLKS_PER_BIT = 8
NBITS = 8                                    # 8N1: eight data bits, LSB first
FRAME = (1 + NBITS + 1) * CLKS_PER_BIT       # start + data + stop, in clocks


def seed(default=5):
    """Pin the stream so the room sees the run we rehearsed.
    Override from the shell:  make STEP=3 DEMO_SEED=7
    """
    s = int(os.environ.get("DEMO_SEED", default))
    random.seed(s)
    cocotb.log.info(f"demo seed = {s}")
    return s


async def reset_uart(dut):
    """Drive a clean reset; the serial line idles high."""
    dut.tx_valid.value = 0
    dut.tx_data.value = 0
    dut.rxd.value = 1
    dut.rst_n.value = 0
    for _ in range(3):
        await RisingEdge(dut.clk)
    dut.rst_n.value = 1
    await FallingEdge(dut.clk)


async def send(dut, byte):
    """Wait for tx_ready, present one byte for exactly one cycle."""
    while not int(dut.tx_ready.value):
        await RisingEdge(dut.clk)
        await Timer(1, units="ns")
    dut.tx_data.value = byte
    dut.tx_valid.value = 1
    await RisingEdge(dut.clk)
    await Timer(1, units="ns")
    dut.tx_valid.value = 0


def start_loopback(dut, trace):
    """One external wire: sample txd every posedge into `trace` (a logic-
    analyzer capture) and mirror it onto rxd."""
    async def run():
        while True:
            await RisingEdge(dut.clk)
            await Timer(1, units="ns")
            v = int(dut.txd.value)
            trace.append(v)
            dut.rxd.value = v
    return cocotb.start_soon(run())


def start_rx_watch(dut, got, pulses):
    """Count rx_valid / frame_err pulses; append accepted bytes to `got`.
    pulses is a dict: {"valid": 0, "err": 0}."""
    async def run():
        while True:
            await RisingEdge(dut.clk)
            await Timer(2, units="ns")
            if int(dut.rx_valid.value):
                pulses["valid"] += 1
                got.append(int(dut.rx_data.value))
            pulses["err"] += int(dut.frame_err.value)
    return cocotb.start_soon(run())


async def drive_frame(dut, byte, stop_level=1, clks=CLKS_PER_BIT):
    """Bit-bang one 8N1 frame straight onto rxd -- no transmitter involved,
    which is the only way to produce a broken frame: the transmitter refuses
    to make one. stop_level=0 forges a framing violation."""
    dut.rxd.value = 0                        # start bit
    for _ in range(clks):
        await RisingEdge(dut.clk)
    for i in range(NBITS):                   # data bits, LSB first
        dut.rxd.value = (byte >> i) & 1
        for _ in range(clks):
            await RisingEdge(dut.clk)
    dut.rxd.value = stop_level               # stop bit -- or the forged one
    for _ in range(clks):
        await RisingEdge(dut.clk)
    dut.rxd.value = 1                        # back to idle
    for _ in range(clks):
        await RisingEdge(dut.clk)


def find_frame(trace, start=0):
    """Index of the first start edge (line low) at/after `start`, or None."""
    for i in range(start, len(trace)):
        if trace[i] == 0:
            return i
    return None


def frame_report(trace, i, clks=CLKS_PER_BIT):
    """Slice one frame out of the captured wire and check its shape sample
    by sample: start all-low, every data bit stable for a full bit-time,
    stop all-high. Returns (decoded value, printable text)."""
    def seg(k):
        return trace[i + k * clks: i + (k + 1) * clks]

    lines = ["",
             f"  the frame on the wire   (CLKS_PER_BIT={clks}, "
             f"one row per bit-time)",
             "  pos    samples    reads as",
             "  -----  --------   --------"]
    s = seg(0)
    assert s == [0] * clks, f"start bit not {clks} low cycles: {s}"
    lines.append(f"  start  {''.join(map(str, s))}   line low -- frame begins")
    val = 0
    for b in range(NBITS):
        s = seg(1 + b)
        assert len(set(s)) == 1, f"data bit {b} not stable on the wire: {s}"
        val |= s[0] << b
        note = "  (LSB first)" if b == 0 else ""
        lines.append(f"  bit{b}   {''.join(map(str, s))}   {s[0]}{note}")
    s = seg(1 + NBITS)
    assert s == [1] * clks, f"stop bit not {clks} high cycles: {s}"
    lines.append(f"  stop   {''.join(map(str, s))}   line high -- frame ends")
    lines.append(f"  wire reads {val:#04x}")
    return val, "\n".join(lines)
