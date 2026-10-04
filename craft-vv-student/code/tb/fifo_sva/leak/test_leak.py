"""Runnable demo for the information-flow assertion in dut/leak_check.sv.

Phase 1 (secure): hammer the SECRET input with random values while driving
public_in independently. The bound assertion a_no_secret_leak must hold every
cycle -- pub_out may depend on public_in but NOT on secret. (Build with
`make LEAK=1` to inject -DLEAK_BUG and watch the assertion fire.)

Phase 2 (open): with secure_mode=0 the secret is legitimately declassified into
the output, so pub_out == public_in ^ secret and the assertion is not checked.
"""
import random
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, Timer

MASK = 0xFF


@cocotb.test()
async def test_information_flow(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    dut.rst_n.value = 0
    dut.secure_mode.value = 0
    dut.secret.value = 0
    dut.public_in.value = 0
    for _ in range(3):
        await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.rst_n.value = 1
    rnd = random.Random(0x5EC12E7)

    # Phase 1 -- secure: the secret must not reach pub_out.
    for _ in range(300):
        pub = rnd.randint(0, MASK)
        dut.secure_mode.value = 1
        dut.secret.value = rnd.randint(0, MASK)     # vary the secret wildly
        dut.public_in.value = pub
        await RisingEdge(dut.clk)
        await Timer(1, units="ns")
        assert int(dut.pub_out.value) == pub, \
            f"LEAK: secure pub_out={int(dut.pub_out.value):#x} != public_in={pub:#x}"
        await FallingEdge(dut.clk)

    # Phase 2 -- open: the secret is declassified on purpose.
    for _ in range(100):
        pub = rnd.randint(0, MASK)
        sec = rnd.randint(0, MASK)
        dut.secure_mode.value = 0
        dut.secret.value = sec
        dut.public_in.value = pub
        await RisingEdge(dut.clk)
        await Timer(1, units="ns")
        assert int(dut.pub_out.value) == (pub ^ sec), \
            f"open pub_out={int(dut.pub_out.value):#x} != pub^sec={pub ^ sec:#x}"
        await FallingEdge(dut.clk)
