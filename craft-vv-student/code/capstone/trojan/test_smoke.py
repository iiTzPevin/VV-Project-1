"""SMOKE test -- secure_gate CLEAN variant (Track 3, security).

Brings up the clean key-comparator gate and checks the security contract:
  * for every wrong key the gate stays locked and data_out is masked to 0;
  * the MAGIC_KEY that the TROJAN variant reacts to must NOT unlock the clean gate
    (this is exactly the backdoor the trojan plants -- the clean part proves the
    intended behavior);
  * the correct key unlocks and passes data through;
  * access_count advances only while unlocked.

Runs against DUT=secure_gate_clean.sv (the Makefile default). Point DUT= at
secure_gate_trojan.sv and the MAGIC_KEY check below will FAIL -- that is the
trojan being detected by a targeted vector. Randomly hitting the 32-bit trigger
is astronomically unlikely, which is the pedagogical point (M3: prove the
property, don't just add vectors).
"""
import random
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, Timer

EXPECTED_KEY = 0xA5A51234
MAGIC_KEY    = 0xDEADBEEF          # the trojan trigger; clean gate must ignore it
DW_MASK      = 0xFF


async def reset(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    dut.key.value = 0
    dut.data_in.value = 0
    dut.rst_n.value = 0
    for _ in range(3):
        await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.rst_n.value = 1


async def apply_key(dut, key, data):
    """Drive key/data combinationally and sample the gate outputs."""
    await FallingEdge(dut.clk)
    dut.key.value = key
    dut.data_in.value = data & DW_MASK
    await Timer(1, units="ns")
    return int(dut.unlocked.value), int(dut.data_out.value)


@cocotb.test()
async def test_security_property(dut):
    """Locked + zero output for wrong keys (incl. near-misses and the magic key)."""
    await reset(dut)
    data = 0xAB
    wrong_keys = [
        0x00000000,
        0x12345678,
        0xFFFFFFFF,
        0x00001234,          # matches only the low 16 bits of EXPECTED_KEY
        0xA5A50000,          # matches only the high 16 bits of EXPECTED_KEY
        EXPECTED_KEY ^ 0x1,  # off by a single bit
        MAGIC_KEY,           # trojan trigger -- clean gate must stay locked
    ]
    for k in wrong_keys:
        unlocked, dout = await apply_key(dut, k, data)
        assert unlocked == 0, f"gate unlocked on wrong key {k:#010x} (backdoor?)"
        assert dout == 0, f"data leaked ({dout:#x}) while locked on key {k:#010x}"

    # add random wrong keys for good measure
    rnd = random.Random(0x5EC)
    for _ in range(200):
        k = rnd.randint(0, 0xFFFFFFFF)
        if k == EXPECTED_KEY:
            continue
        unlocked, dout = await apply_key(dut, k, data)
        assert unlocked == 0 and dout == 0, f"leak on random wrong key {k:#010x}"

    # correct key: unlock and pass data through
    unlocked, dout = await apply_key(dut, EXPECTED_KEY, data)
    assert unlocked == 1, "correct key did not unlock the gate"
    assert dout == (data & DW_MASK), f"data_out {dout:#x} != data_in {data:#x} when unlocked"


@cocotb.test()
async def test_access_count(dut):
    """access_count increments only while unlocked."""
    await reset(dut)
    await FallingEdge(dut.clk)

    # unlocked for 5 cycles
    dut.key.value = EXPECTED_KEY
    dut.data_in.value = 0xAB
    for _ in range(5):
        await RisingEdge(dut.clk)
    await Timer(1, units="ns")
    assert int(dut.access_count.value) == 5, \
        f"count {int(dut.access_count.value)} != 5 after 5 unlocked cycles"

    # locked for 3 cycles -> frozen
    dut.key.value = 0x00000000
    for _ in range(3):
        await RisingEdge(dut.clk)
    await Timer(1, units="ns")
    assert int(dut.access_count.value) == 5, \
        f"count advanced ({int(dut.access_count.value)}) while locked"

    # unlocked again for 2 cycles -> resumes
    await FallingEdge(dut.clk)
    dut.key.value = EXPECTED_KEY
    for _ in range(2):
        await RisingEdge(dut.clk)
    await Timer(1, units="ns")
    assert int(dut.access_count.value) == 7, \
        f"count {int(dut.access_count.value)} != 7 after resuming"

    dut._log.info("secure_gate CLEAN smoke PASS: contract holds, no backdoor.")
