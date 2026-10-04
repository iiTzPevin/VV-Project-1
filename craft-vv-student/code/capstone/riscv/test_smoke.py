"""SMOKE test -- RV32I capstone core (Track 1).

Loads the hand-assembled program in program.hex (single-cycle: one instruction
per clock), runs it, and scoreboards the DUT's final architectural state against
the golden ISS (lib/models/rv32i_model.py). Exercises every supported opcode:
add sub and or xor addi andi ori lw sw beq (taken + not-taken) jal.

This is the PASS-clean bring-up test students are given. It is NOT a full
verification suite -- that (CRV, coverage, assertions, mutation) is the capstone.
"""
import os
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, Timer
from models.rv32i_model import (ADD, SUB, AND, OR, XOR, ADDI, ANDI, ORI,
                                LW, SW, BEQ, JAL, assemble, to_hex_lines, RV32I)

# --- canonical smoke program (mirrors program.hex; keep in sync) ---
PROGRAM = [
    ADDI( 1, 0,   5),   # 0x00  x1  = 5
    ADDI( 2, 0,   3),   # 0x04  x2  = 3
    ADD ( 3, 1,   2),   # 0x08  x3  = 8
    SUB ( 4, 1,   2),   # 0x0C  x4  = 2
    AND ( 5, 1,   2),   # 0x10  x5  = 1
    OR  ( 6, 1,   2),   # 0x14  x6  = 7
    XOR ( 7, 1,   2),   # 0x18  x7  = 6
    ANDI( 8, 1,   6),   # 0x1C  x8  = 4
    ORI ( 9, 2,   8),   # 0x20  x9  = 11
    ADDI(13, 0,   1),   # 0x24  x13 = 1  (guard: branch-taken must NOT overwrite)
    ADDI(15, 0,   1),   # 0x28  x15 = 1  (guard: jal must NOT overwrite)
    ADDI(10, 0, 256),   # 0x2C  x10 = 0x100 (data base)
    SW  ( 3, 10,  0),   # 0x30  mem[0x100] = x3 = 8
    LW  (11, 10,  0),   # 0x34  x11 = mem[0x100] = 8
    BEQ ( 1, 2,   8),   # 0x38  5 != 3 -> NOT taken, fall through
    ADDI(12, 0,  99),   # 0x3C  x12 = 99 (executes)
    BEQ ( 1, 1,   8),   # 0x40  1 == 1 -> taken, skip 0x44
    ADDI(13, 0,  77),   # 0x44  would set x13=77 (must be SKIPPED)
    JAL (14,     8),    # 0x48  x14 = pc+4 = 0x4C, jump to 0x50 (skip 0x4C)
    ADDI(15, 0,  55),   # 0x4C  would set x15=55 (must be SKIPPED)
    BEQ ( 0, 0,   0),   # 0x50  halt: self-loop, no writes
]

DMEM_BASE = 0x100
RUN_CYCLES = 30


async def _read_reg(dut, idx):
    dut.dbg_sel.value = idx
    await Timer(1, units="ns")
    return int(dut.dbg_reg.value)


async def _read_dmem(dut, byte_addr):
    dut.dbg_dmem_idx.value = (byte_addr >> 2) % 64
    await Timer(1, units="ns")
    return int(dut.dbg_dmem_data.value)


@cocotb.test()
async def test_smoke(dut):
    # program.hex on disk must match the program above (harness $readmemh's it).
    here = os.path.dirname(__file__)
    with open(os.path.join(here, "program.hex")) as f:
        on_disk = [ln.strip() for ln in f if ln.strip()]
    expected_hex = to_hex_lines(assemble(PROGRAM))
    assert on_disk == expected_hex, (
        "program.hex is stale vs PROGRAM in test_smoke.py -- regenerate it.")

    # golden reference
    iss = RV32I(assemble(PROGRAM))
    iss.run(RUN_CYCLES)

    # bring up the DUT
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    dut.dbg_sel.value = 0
    dut.dbg_dmem_idx.value = 0
    dut.rst_n.value = 0
    for _ in range(3):
        await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.rst_n.value = 1

    # run the program
    for _ in range(RUN_CYCLES):
        await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)

    # scoreboard architectural registers written by the program
    checked = [3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
    for idx in checked:
        got = await _read_reg(dut, idx)
        want = iss.reg(idx)
        assert got == want, f"x{idx}: DUT={got:#x} ISS={want:#x}"

    # spot-check the meaning of the interesting cases explicitly
    assert (await _read_reg(dut, 12)) == 99, "beq not-taken path did not execute"
    assert (await _read_reg(dut, 13)) == 1,  "beq taken failed to skip x13<-77"
    assert (await _read_reg(dut, 14)) == 0x4C, "jal link register wrong"
    assert (await _read_reg(dut, 15)) == 1,  "jal failed to skip x15<-55"

    # scoreboard data memory (sw then lw round-trip landed in memory)
    got_mem = await _read_dmem(dut, DMEM_BASE)
    assert got_mem == iss.load_word(DMEM_BASE) == 8, \
        f"dmem[{DMEM_BASE:#x}]: DUT={got_mem} ISS={iss.load_word(DMEM_BASE)}"

    dut._log.info("RV32I smoke PASS: all supported opcodes match the ISS.")
