"""STEP 3 -- the first security assertion: the secret must not move pub_out.

dut/leak_check.sv is a one-function declassifier with the information-flow
monitor from the deck bound inside it. A self-composition reference computes
the same function with the secret scrubbed to zero, and a_no_secret_leak
asserts that in secure mode the real output equals the scrubbed one -- if
the secret can move a public output, the two disagree on that cycle.

This test hammers the secret with 300 random values while public_in varies
independently; the assertion samples every posedge. Then it flips to open
mode, where mixing the secret in is the declassification POLICY, not a leak.

  make STEP=3           holds: 300 secure draws, pub_out never follows the secret
  make STEP=3 LEAK=1    compile with -DLEAK_BUG (the secret is mixed in even in
                        secure mode): a_no_secret_leak fires on the first draw

What a green run means -- and does not: no leak was OBSERVED on these
traces. A tripwire, not a proof; the proof over all reachable states is next
week's formal flow. tb/fifo_sva/SECURITY.md states the boundary in full.
"""
import random

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, Timer

from demo_common import seed

MASK = 0xFF


@cocotb.test()
async def test_no_leak(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    seed()
    dut.rst_n.value = 0
    dut.secure_mode.value = 0
    dut.secret.value = 0
    dut.public_in.value = 0
    for _ in range(3):
        await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.rst_n.value = 1

    # secure mode: whatever the secret does, pub_out must track public_in
    for _ in range(300):
        pub = random.randint(0, MASK)
        dut.secure_mode.value = 1
        dut.secret.value = random.randint(0, MASK)
        dut.public_in.value = pub
        await RisingEdge(dut.clk)
        await Timer(1, units="ns")
        assert int(dut.pub_out.value) == pub, \
            f"LEAK: pub_out={int(dut.pub_out.value):#04x} != public_in={pub:#04x}"
        await FallingEdge(dut.clk)
    cocotb.log.info("secure mode: 300 random secrets, pub_out tracked "
                    "public_in every cycle")

    # open mode: the secret is mixed in on purpose -- policy, not a leak
    for _ in range(50):
        pub, sec = random.randint(0, MASK), random.randint(0, MASK)
        dut.secure_mode.value = 0
        dut.secret.value = sec
        dut.public_in.value = pub
        await RisingEdge(dut.clk)
        await Timer(1, units="ns")
        assert int(dut.pub_out.value) == (pub ^ sec), "open path broken"
        await FallingEdge(dut.clk)
    cocotb.log.info("open mode: 50 draws declassified by policy")
    cocotb.log.info("green means: no leak OBSERVED on these traces -- "
                    "the proof is next week")
