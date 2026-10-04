"""Shared helpers for the Week 9 Session 1 demo. The step files hold the UVM
structure being taught; this file holds only what every step needs -- the
pinned seed, reset, the one stimulus stream two steps share, and a fingerprint
that can tell two runs apart.
"""
import os
import random
import zlib

import cocotb
from cocotb.triggers import RisingEdge, FallingEdge

# word addresses (dut/specs/axil_regfile.md)
A_CTRL, A_STATUS, A_SCRATCH, A_INTR, A_LOCK, A_SECURE = 0, 1, 2, 3, 4, 5
MASK = 0xFFFFFFFF
N_RANDOM = 60          # random transactions after the reset-value sweep


def seed(default=5):
    """Pin the stream so the room sees the run we rehearsed.
    Override from the shell:  make STEP=3 DEMO_SEED=7
    """
    s = int(os.environ.get("DEMO_SEED", default))
    cocotb.log.info(f"demo seed = {s}")
    return s


def gen_stimulus(seed_val, n=N_RANDOM):
    """The one stimulus stream of this session: read the whole map, then n
    random transactions. Step 0 drives it flat; step 3 replays it through the
    agent. Same list in, so any difference between the runs is structural.
    """
    rnd = random.Random(seed_val)
    txns = [(0, a, 0) for a in range(8)]     # reset values first, incl. unmapped
    for _ in range(n):
        txns.append((rnd.randint(0, 1), rnd.randint(0, 7), rnd.getrandbits(32)))
    return txns


class StreamDigest:
    """Order-sensitive fingerprint of a (we, addr, data) transaction stream.
    Two runs with the same digest drove and observed identical bus traffic.
    """
    def __init__(self):
        self.crc = 0
        self.count = 0

    def update(self, we, addr, data):
        self.crc = zlib.crc32(f"{we}:{addr:x}:{data:08x};".encode(), self.crc)
        self.count += 1

    @property
    def hex(self):
        return f"{self.crc:08x}"


async def reset(dut):
    """Drive a clean reset and leave the bus idle on a falling edge."""
    dut.req.value = 0
    dut.we.value = 0
    dut.addr.value = 0
    dut.wdata.value = 0
    dut.rst_n.value = 0
    for _ in range(3):
        await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.rst_n.value = 1


def announce(comp, phase, note=""):
    """One line per phase per component -- the step 1 capture is built from
    these. Production code uses comp.logger; the demo
    logs via cocotb so the capture is byte-stable across machines.
    """
    tail = f"   {note}" if note else ""
    cocotb.log.info(f"{phase:<15}{comp.get_full_name()}{tail}")
