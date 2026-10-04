# ALU specification (dut/alu.sv)

A parameterized, **purely combinational** arithmetic logic unit (ALU): two
operands in, a result and three status flags out. The unifying example for
Weeks 1--3.

## Parameters
- `WIDTH` (default 8) — width of `a`, `b`, and `result`, in bits. `op` is
  3 bits at every `WIDTH`. Concrete constants below (`b[2:0]`, `8'h7F`, ...)
  assume the default `WIDTH = 8`.

## Ports
| Signal | Dir | Width | Meaning |
|--------|-----|-------|---------|
| `a`, `b` | in | WIDTH | operands |
| `op` | in | 3 | operation select (see Operations) |
| `result` | out | WIDTH | operation result |
| `zero` | out | 1 | `result` is all zeros |
| `carry` | out | 1 | carry flag (see Flags) |
| `overflow` | out | 1 | overflow flag (see Flags) |

## Operations
| `op` | Name | `result` |
|------|------|----------|
| `3'd0` | ADD | `a + b`, modulo `2^WIDTH` |
| `3'd1` | SUB | `a - b`, modulo `2^WIDTH` |
| `3'd2` | AND | bitwise AND of `a` and `b` |
| `3'd3` | OR | bitwise OR of `a` and `b` |
| `3'd4` | XOR | bitwise XOR of `a` and `b` |
| `3'd5` | SLT | `1` if `a < b` comparing both as **signed** (two's-complement) values, else `0` |
| `3'd6` | SLL | `a` shifted left by the shift amount; vacated bits are `0` |
| `3'd7` | SRL | `a` shifted right by the shift amount; vacated bits are `0` (logical shift) |

**Shift amount:** the low `$clog2(WIDTH)` bits of `b` — `b[2:0]` at the
default width. The upper bits of `b` do not participate: `b = 8'd9` shifts
by 1, not by 9.

Opcodes not listed in the table are undefined; do not rely on the `result`
or flag values they produce.

## Flags
- `zero` — set iff `result` is all zeros. Updated by every operation.
- `carry` — the carry produced by the arithmetic operations. For ADD this is
  the carry out of the most-significant bit: set iff `a + b >= 2^WIDTH`.
  `0` for the logical, compare, and shift operations.
- `overflow` — set when the mathematical result of an arithmetic operation
  (ADD, SUB) does not fit in `WIDTH` bits. `0` for the logical, compare, and
  shift operations.

## Timing
Purely combinational: `result`, `zero`, `carry`, and `overflow` are functions
of the current `a`, `b`, and `op` and of nothing else. No clock, no reset, no
internal state. In simulation, drive the inputs, let the logic settle (one
timestep), then sample the outputs.

## Corner cases a good testbench must hit
Add and subtract at the wrap boundaries (exactly at, and one either side);
equal operands (`a == b`); the sign corners `8'h7F`/`8'h80` and the extremes
`8'h00`/`8'hFF`; SLT with one negative operand; shifts by 0, by `WIDTH-1`,
and by `b >= WIDTH`; and `zero` both asserted and deasserted under every
operation.
