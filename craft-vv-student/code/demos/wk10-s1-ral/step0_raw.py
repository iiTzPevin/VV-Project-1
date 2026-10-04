"""STEP 0 -- the honest starting point: raw read/write pairs, no model.

What everyone writes first against a register map: write each register that
looks writable, read it back, compare. Skip STATUS ("read-only, nothing to
write") and INTR ("hardware-driven, leave it alone"). It passes -- and it has
verified storage, not the map. No reset value is checked, no policy is
checked, and the lock bit is only shown to *store* a 1, never to *enforce*
anything.
"""
import random

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, Timer

from demo_common import seed

# the map, as a naive test sees it: "the writable ones"
WRITABLE = [("CTRL", 0x0), ("SCRATCH", 0x2), ("SECURE", 0x5), ("LOCK", 0x4)]
ADDR_STATUS = 0x1


async def raw_write(dut, addr, data):
    await FallingEdge(dut.clk)
    dut.req.value = 1
    dut.we.value = 1
    dut.addr.value = addr
    dut.wdata.value = data
    await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.req.value = 0
    dut.we.value = 0


async def raw_read(dut, addr):
    await FallingEdge(dut.clk)
    dut.req.value = 1
    dut.we.value = 0
    dut.addr.value = addr
    await RisingEdge(dut.clk)
    await Timer(1, units="ns")
    data = int(dut.rdata.value)          # nobody looks at rvalid
    await FallingEdge(dut.clk)
    dut.req.value = 0
    return data


@cocotb.test()
async def test_raw_readwrite(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    seed()
    dut.rst_n.value = 0
    dut.req.value = 0
    dut.we.value = 0
    dut.addr.value = 0
    dut.wdata.value = 0
    for _ in range(3):
        await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.rst_n.value = 1
    await FallingEdge(dut.clk)

    rows = ["", "  read-after-write, straight down the map (no model):"]
    for name, addr in WRITABLE:
        val = 0x1 if name == "LOCK" else random.getrandbits(32)
        await raw_write(dut, addr, val)
        got = await raw_read(dut, addr)
        assert got == val, f"{name}: wrote {val:#010x}, read {got:#010x}"
        note = "   (the lock bit stores a 1 -- tested!)" if name == "LOCK" else ""
        rows.append(f"  {name:<8} <= {val:#010x}   read -> {got:#010x}   ok{note}")

    got = await raw_read(dut, ADDR_STATUS)
    rows.append(f"  STATUS   read -> {got:#010x}   nonzero, looks alive (unchecked)")
    rows.append(f"  {len(WRITABLE)}/{len(WRITABLE)} read-after-write pairs match: PASS")
    rows.append("  never checked: reset values, RO, W1C, address decode,")
    rows.append("                 or whether LOCK=1 protects anything")
    cocotb.log.info("\n".join(rows))
