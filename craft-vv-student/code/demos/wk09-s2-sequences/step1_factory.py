"""STEP 1 -- swap the driver through the factory; edit nothing else.

This file contains no environment and no stimulus. It imports step 0's test
byte for byte, defines one driver subclass that corrupts a fraction of writes
on their way to the wires, and installs it with a single factory override.
`RegDriver.create(...)` inside the agent now hands back an ErrInjectDriver --
the agent, env, sequences, and test never learn about it.

Run step 0, then this, and compare: same test name, same sequences, same
scoreboard verdict -- and the log now shows injections. The scoreboard still
passes because it predicts from what the monitor SAW on the bus, not from
what the sequences intended. Checking that survives corrupted stimulus is
checking you can trust next week, when the corruption comes from the RTL.
"""
import random

import cocotb
from cocotb.clock import Clock
from pyuvm import uvm_factory, ConfigDB, uvm_root

from demo_common import RegDriver, reset, seed
from step0_sequences import SequenceTest          # reused, not copied

INJECT_RATE = 0.25


class ErrInjectDriver(RegDriver):
    """RegDriver, except some writes reach the bus with one data bit flipped.
    The injection stream is pinned separately from DEMO_SEED so the corruption
    pattern stays put while the stimulus seed moves."""
    def build_phase(self):
        super().build_phase()
        self.rnd = random.Random(99)
        self.injected = 0

    async def _drive(self, item):
        if item.we and self.rnd.random() < INJECT_RATE:
            bit = self.rnd.randrange(32)
            item.data ^= 1 << bit
            self.injected += 1
            cocotb.log.info(f"INJECT #{self.injected:>2}: flipped wdata bit "
                            f"{bit:>2} on WR a={item.addr:#x}")
        await super()._drive(item)


@cocotb.test()
async def test_factory_override(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset(dut)
    ConfigDB().set(None, "*", "DUT", dut)
    ConfigDB().set(None, "*", "SEED", seed())
    # the line this step exists for:
    uvm_factory().set_type_override_by_type(RegDriver, ErrInjectDriver)
    await uvm_root().run_test("SequenceTest", keep_singletons=True)
