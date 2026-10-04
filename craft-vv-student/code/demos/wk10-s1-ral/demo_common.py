"""Shared plumbing for the Week 10 Session 1 demo. The step files hold only
what the demo is about: the register map, the generic tests, the policies.
"""
import os
import random

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, Timer

from models.regfile_model import RegfileModel

MASK = 0xFFFFFFFF


def seed(default=5):
    """Pin the junk values so the room sees the run we rehearsed.
    Override from the shell:  make STEP=0 DEMO_SEED=7
    """
    s = int(os.environ.get("DEMO_SEED", default))
    random.seed(s)
    cocotb.log.info(f"demo seed = {s}")
    return s


class RegBus:
    """Register-access adapter over the axil_regfile bus (same one the
    reference suite uses). read() checks rvalid -- the bus contract is part
    of what a register test verifies."""

    def __init__(self, dut):
        self.dut = dut

    async def reset(self):
        d = self.dut
        d.req.value = 0
        d.we.value = 0
        d.addr.value = 0
        d.wdata.value = 0
        d.rst_n.value = 0
        for _ in range(3):
            await RisingEdge(d.clk)
        await FallingEdge(d.clk)
        d.rst_n.value = 1
        await FallingEdge(d.clk)

    async def write(self, addr, data):
        d = self.dut
        await FallingEdge(d.clk)
        d.req.value = 1
        d.we.value = 1
        d.addr.value = addr & 0xF
        d.wdata.value = data & MASK
        await RisingEdge(d.clk)
        await FallingEdge(d.clk)
        d.req.value = 0
        d.we.value = 0

    async def read(self, addr):
        d = self.dut
        await FallingEdge(d.clk)
        d.req.value = 1
        d.we.value = 0
        d.addr.value = addr & 0xF
        await RisingEdge(d.clk)
        await Timer(1, units="ns")     # registered read: rvalid/rdata valid now
        assert int(d.rvalid.value) == 1, \
            f"rvalid not asserted for read of addr {addr:#x}"
        data = int(d.rdata.value)
        await FallingEdge(d.clk)
        d.req.value = 0
        return data


def banner(dut):
    """Clock + bus adapter + the mirror (RegfileModel tracks what the model
    believes the hardware holds -- the 'mirrored value')."""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    return RegBus(dut), RegfileModel()
