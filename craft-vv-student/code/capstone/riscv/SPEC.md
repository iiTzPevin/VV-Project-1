# RV32I capstone core -- SPEC (Track 1)

A **small single-cycle RV32I subset core**. One instruction retires per clock.
`x0` is hardwired to 0. Harvard memories (separate instruction/data). This is a
teaching DUT: correctness over performance, fully synthesizable, runs under
Icarus and Verilator.

- RTL: `rv32i_core.sv` (the DUT that gets mutated)
- Sim harness (always compiled, not mutated): `rv32i_top.sv`, `rv32i_imem.sv`, `rv32i_dmem.sv`
- Golden ISS + assembler: `lib/models/rv32i_model.py` (import as `models.rv32i_model`)

## Supported instruction subset (the contract)
Only these 12 instructions are supported. Everything else decodes to a NOP.

| Instr | Type | Semantics |
|-------|------|-----------|
| `add  rd,rs1,rs2` | R | `rd = rs1 + rs2` |
| `sub  rd,rs1,rs2` | R | `rd = rs1 - rs2` |
| `and  rd,rs1,rs2` | R | `rd = rs1 & rs2` |
| `or   rd,rs1,rs2` | R | `rd = rs1 | rs2` |
| `xor  rd,rs1,rs2` | R | `rd = rs1 ^ rs2` |
| `addi rd,rs1,imm` | I | `rd = rs1 + sext(imm)` |
| `andi rd,rs1,imm` | I | `rd = rs1 & sext(imm)` |
| `ori  rd,rs1,imm` | I | `rd = rs1 | sext(imm)` |
| `lw   rd,imm(rs1)`| I | `rd = DMEM[rs1 + sext(imm)]` |
| `sw   rs2,imm(rs1)`| S | `DMEM[rs1 + sext(imm)] = rs2` |
| `beq  rs1,rs2,imm`| B | `if (rs1 == rs2) pc += sext(imm)` else `pc += 4` |
| `jal  rd,imm`     | J | `rd = pc + 4; pc += sext(imm)` |

Immediates are sign-extended to 32 bits. Word accesses only (aligned); byte /
halfword loads/stores and the rest of RV32I are **out of scope** for this core.

## Register model
- 32 general registers, XLEN = 32. `x0` always reads 0 and ignores writes.
- A write to `rd` (when `rd != x0` and the instruction writes back) is visible
  on the **next** clock edge.

## Memory map
Both memories are small directly-mapped word arrays; the high address bits are
ignored (index = `(addr >> 2) mod WORDS`). Defaults: 64 words each.

| Region | Base | Notes |
|--------|------|-------|
| Instruction memory | `0x0000_0000` | `pc` starts at 0; preloaded from `program.hex` |
| Data memory | any (aliased) | `lw`/`sw`; the smoke program uses base `0x0000_0100` |

Because addressing is modulo the array size, `0x100` maps to word index 0 of the
data memory. The ISS mirrors this exactly.

## Reset
Active-low, synchronous. While `rst_n == 0`, on the next edge `pc <= 0`. The
register file is not reset; the ISS starts registers at 0 and the smoke program
only reads registers it has previously written (or `x0`).

## Observability hooks (harness)
Synthesizable read muxes, present so a scoreboard can read architectural state
without hierarchical peeking:
- `dbg_sel` / `dbg_reg` -- combinational read of register `dbg_sel`.
- `dbg_dmem_idx` / `dbg_dmem_data` -- combinational read of data-memory word.

## Security / correctness properties worth proving (M3)
- `x0` is never mutated (reads 0 regardless of any write targeting it).
- A non-taken `beq` and any non-writeback instruction leave `rd` unchanged.
- `jal` link register equals `pc + 4` of the jump instruction.
- Effective address for `lw`/`sw` equals `rs1 + sext(imm)`.

## What the smoke test exercises (and what it does NOT)
`test_smoke.py` loads `program.hex` (a ~20-instruction hand-assembled program),
runs it single-cycle, and scoreboards **every supported opcode** against the ISS
-- including `beq` taken *and* not-taken, the `sw`->`lw` round-trip through data
memory, and `jal`'s link + skip. It is a **bring-up** test only.

It does **not** provide constrained-random coverage, corner-case immediates
(large/negative offsets, wrap), hazard/alignment stress, or assertions. Building
that suite -- and closing the mutation pools -- is the capstone work (M2-M4).
The released pool `mutants_released.yaml` (8 mutants) is provided for practice;
the reference smoke test already finds all 8, but your graded suite is scored
against a larger hidden pool.
