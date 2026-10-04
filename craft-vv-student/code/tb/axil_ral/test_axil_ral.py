"""STUDENT STARTER -- Week 10 automated register (RAL-style) tests.

You are given the register map (REGS) and a working bus-access adapter (RegBus).
Only a minimal reset-value test is written.  It passes on the golden RTL but
catches almost none of the register-policy mutants, because it never bit-bashes
the RW registers and never checks the RO / W1C / SECURE policies.

Your job (Week 10 lab) -- add the automated tests the reference has:
  TODO(1): test_bit_bash     -- walking-ones/all-ones/zero on RW regs, read-back
  TODO(2): test_ro_policy    -- writes to STATUS must be ignored
  TODO(3): test_w1c_policy   -- a 1 clears INTR, a 0 does not (arm via a violation)
  TODO(4): test_secure_lock  -- SECURE writable only while LOCK.bit0 == 0
                                (the security check)

There is more than one complete answer. Yours is graded on what it finds,
not on how closely it matches anyone else's.
"""
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, Timer

MASK = 0xFFFFFFFF

REGS = {
    "CTRL":    dict(addr=0x0, policy="RW",        reset=0x00000000),
    "STATUS":  dict(addr=0x1, policy="RO",        reset=0x5A5A0F0F),
    "SCRATCH": dict(addr=0x2, policy="RW",        reset=0x00000000),
    "INTR":    dict(addr=0x3, policy="W1C",       reset=0x00000000),
    "LOCK":    dict(addr=0x4, policy="RW",        reset=0x00000000),
    "SECURE":  dict(addr=0x5, policy="LOCKED_RW", reset=0x00000000),
}
A = {name: r["addr"] for name, r in REGS.items()}


class RegBus:
    """Lightweight register-access adapter over the axil_regfile bus."""
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
        await Timer(1, units="ns")
        data = int(d.rdata.value)
        await FallingEdge(d.clk)
        d.req.value = 0
        return data


@cocotb.test()
async def test_reset_values(dut):
    """Minimal: check a couple of registers read their reset value."""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    bus = RegBus(dut)
    await bus.reset()
    for name in ("CTRL", "SCRATCH"):
        got = await bus.read(REGS[name]["addr"])
        assert got == REGS[name]["reset"], \
            f"{name} reset: got {got:#010x} expected {REGS[name]['reset']:#010x}"

    # TODO(1..4): add bit-bash and the RO / W1C / SECURE policy tests here.
