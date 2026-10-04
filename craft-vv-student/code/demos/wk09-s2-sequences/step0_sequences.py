"""STEP 0 -- stimulus becomes a library.

The environment is Tuesday's, imported untouched from demo_common. Everything
new in this file is a sequence: the smallest one possible, a read-after-write
that exercises a policy, and a random burst across the whole map. The driver
never changes again -- new behavior means another sequence, and the same
handshake (start_item / finish_item against the driver's get_next_item)
carries them all.
"""
import random

import cocotb
from cocotb.clock import Clock
from pyuvm import uvm_sequence, uvm_test, ConfigDB, uvm_root

from demo_common import (A_CTRL, A_STATUS, A_SCRATCH, MASK,
                         RegItem, RegEnv, reset, seed)

N_BURST = 80


class RegSeqBase(uvm_sequence):
    """Two helpers so sequences read like register accesses."""
    async def wr(self, addr, data):
        it = RegItem("wr")
        await self.start_item(it)
        it.we, it.addr, it.data = 1, addr, data & MASK
        await self.finish_item(it)

    async def rd(self, addr):
        it = RegItem("rd")
        await self.start_item(it)
        it.we, it.addr, it.data = 0, addr, 0
        await self.finish_item(it)
        return it.data                       # back-annotated by the driver


class SingleWriteSeq(RegSeqBase):
    """The smallest sequence that does anything: one write."""
    async def body(self):
        await self.wr(A_CTRL, 0x00000011)


class ReadAfterWriteSeq(RegSeqBase):
    """Write, read straight back -- including one write the DUT must ignore."""
    async def body(self):
        await self.wr(A_CTRL, 0xC0DE0001)
        await self.rd(A_CTRL)
        await self.wr(A_SCRATCH, 0x5CBA7C11)  # odd value: the LSB must survive
        await self.rd(A_SCRATCH)
        await self.wr(A_STATUS, 0xFFFFFFFF)   # RO: the DUT must ignore this
        await self.rd(A_STATUS)               # scoreboard expects 0x5a5a0f0f


class RandomBurstSeq(RegSeqBase):
    """N_BURST random transactions across the map -- reads and writes
    interleaved; LOCK and SECURE traffic included by construction."""
    async def body(self):
        rnd = random.Random(ConfigDB().get(None, "", "SEED"))
        for _ in range(N_BURST):
            addr = rnd.randint(0, 7)
            if rnd.randint(0, 1):
                await self.wr(addr, rnd.getrandbits(32))
            else:
                await self.rd(addr)


class SequenceTest(uvm_test):
    """Runs the library in order. Note what this class does NOT know: which
    driver class is in the build. Step 1 trades on that."""
    def build_phase(self):
        self.env = RegEnv.create("env", self)

    async def run_phase(self):
        self.raise_objection()
        for seq_cls in (SingleWriteSeq, ReadAfterWriteSeq, RandomBurstSeq):
            await seq_cls(seq_cls.__name__).start(self.env.agent.seqr)
            sb = self.env.sb
            cocotb.log.info(f"after {seq_cls.__name__:<17}: "
                            f"{sb.n_writes:>3} writes, {sb.n_checked:>2} reads "
                            f"checked, {sb.errors} mismatches")
        self.drop_objection()

        cocotb.log.info(f"driver in the build: "
                        f"{type(self.env.agent.driver).__name__}")
        cocotb.log.info(f"corrupted writes injected by the driver: "
                        f"{getattr(self.env.agent.driver, 'injected', 0)}")
        assert self.env.sb.n_checked > 0, "scoreboard checked no reads"
        assert self.env.sb.errors == 0, \
            f"scoreboard found {self.env.sb.errors} mismatch(es)"


@cocotb.test()
async def test_sequences(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset(dut)
    ConfigDB().set(None, "*", "DUT", dut)
    ConfigDB().set(None, "*", "SEED", seed())
    await uvm_root().run_test("SequenceTest", keep_singletons=True)
