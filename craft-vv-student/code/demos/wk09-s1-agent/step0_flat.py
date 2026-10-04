"""STEP 0 -- where Week 4 left us: the flat testbench.

One coroutine drives the bus, samples it, and checks every read against
RegfileModel. It passes, and it finds mutants. Now try to lift any piece of it
onto the next block: the driving is welded to the checking, the checking to
the stimulus, all of it to this file. Today does not add checking power --
it takes this exact behavior and gives it a structure you can keep.
"""
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, Timer

from models.regfile_model import RegfileModel
from demo_common import reset, seed, gen_stimulus, StreamDigest, MASK


async def bus_write(dut, addr, data):
    await FallingEdge(dut.clk)
    dut.req.value = 1
    dut.we.value = 1
    dut.addr.value = addr & 0xF
    dut.wdata.value = data & MASK
    await RisingEdge(dut.clk)                # write commits on this edge
    await FallingEdge(dut.clk)
    dut.req.value = 0
    dut.we.value = 0


async def bus_read(dut, addr):
    await FallingEdge(dut.clk)
    dut.req.value = 1
    dut.we.value = 0
    dut.addr.value = addr & 0xF
    dut.wdata.value = 0
    await RisingEdge(dut.clk)                # read is sampled on this edge
    await Timer(1, units="ns")               # registered data has settled now
    data, rvalid = int(dut.rdata.value), int(dut.rvalid.value)
    await FallingEdge(dut.clk)
    dut.req.value = 0
    return data, rvalid


@cocotb.test()
async def test_flat(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset(dut)
    model, digest, checked = RegfileModel(), StreamDigest(), 0

    for we, addr, data in gen_stimulus(seed()):
        if we:
            await bus_write(dut, addr, data)
            model.write(addr, data)
            digest.update(1, addr, data)
        else:
            rdata, rvalid = await bus_read(dut, addr)
            exp = model.read(addr)
            assert rvalid == 1, f"read a={addr:#x}: rvalid not asserted"
            assert rdata == exp, \
                f"read a={addr:#x}: dut={rdata:#010x} model={exp:#010x}"
            digest.update(0, addr, rdata)
            checked += 1

    cocotb.log.info(f"reads checked against the model: {checked}, mismatches: 0")
    cocotb.log.info(f"stream digest = {digest.hex}  over {digest.count} transactions")
