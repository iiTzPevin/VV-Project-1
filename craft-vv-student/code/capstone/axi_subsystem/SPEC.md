# Interconnect subsystem -- SPEC (Track 2)

A small **address-mapped bus subsystem**: a 2-master round-robin arbiter feeding
a single-cycle request bus with three slaves -- two scratch-register peripherals
and the course FWFT FIFO. Deliberately "AXI-ish" (valid/grant handshake, address
decode, register + streaming peripherals) but stripped to the essentials so it is
tractable to verify in one project.

- RTL: `axi_subsystem.sv` -- top + `rr_arbiter2` (both mutated by this track)
- `fifo.sv` -- copied verbatim from `dut/fifo.sv`, compiled alongside, **not** mutated here
- Golden model for the FIFO slave: `lib/models/fifo_model.py`

## Parameters
- `DW` (32) data width, `AW` (16) address width, `FIFO_DEPTH` (8).

## Master interface (x2, identical)
| Signal | Dir | Meaning |
|--------|-----|---------|
| `mX_req` | in | master X requests a transfer this cycle |
| `mX_we` | in | 1 = write, 0 = read |
| `mX_addr` | in | byte address (see map) |
| `mX_wdata` | in | write data |
| `mX_gnt` | out | this master is granted **this** cycle |
| `mX_rdata` | out | read data (valid when `mX_rvalid`) |
| `mX_rvalid` | out | this master's transaction completed this cycle |

A transaction is **single-cycle**: it is granted and completes in the same clock.
Combinational reads; writes/pushes/pops commit on the rising edge.

## Arbitration (the contract)
- Round-robin between the two masters. From reset the pointer favors **master 1**
  first; after each grant the pointer swings to the other master.
- **At most one** grant per cycle. If only one master requests, it is always
  granted. If both request, exactly one wins and the loser must retry.
- Only the granted master sees `rvalid`/`gnt` asserted.

## Address map
Region is `addr[15:12]`; the in-region word index is `addr[3:2]`.

| Region | `addr[15:12]` | Slave | Behavior |
|--------|---------------|-------|----------|
| REG0 | `0x0` | 4x32b scratch regs | `addr[3:2]` selects reg; write stores, read returns |
| REG1 | `0x1` | 4x32b scratch regs | independent from REG0 (no aliasing) |
| FIFO | `0x2` | FWFT FIFO | see below |

FIFO sub-ports (within region 2):
| Offset | `addr[3:2]` | Access | Effect |
|--------|-------------|--------|--------|
| `0x0` (data)   | 0 | write | **push** `wdata` (dropped if full) |
| `0x0` (data)   | 0 | read  | return FWFT head and **pop** (ignored if empty) |
| `0x4` (status) | 1 | read  | `{ .., count[3:0], full<<1, empty }`; no side effect |

Example addresses: `REG0[0]=0x0000`, `REG1[2]=0x1008`, FIFO data `=0x2000`,
FIFO status `=0x2004`.

## Reset
Active-low, synchronous. Clears the arbiter pointer (favor master 1 next),
zeroes both register files, and resets the FIFO (empty).

## Properties worth proving (M3)
- **Mutual exclusion:** never `m0_gnt && m1_gnt` in the same cycle.
- **No starvation:** under continuous contention each master is granted at least
  once every 2 cycles (round-robin fairness).
- **Region isolation:** a write to one region never changes another region's state.
- **FIFO contract** (inherited from `dut/specs/fifo.md`): write-while-full dropped,
  read-while-empty ignored, FWFT ordering, `full/empty` consistent with `count`.

## What the smoke test exercises (and what it does NOT)
`test_smoke.py` has three tests: `test_arbitration` (round-robin order from reset
under contention + mutual exclusion + rvalid gating), `test_registers` (both
peripherals write/read-back per master + no aliasing), and `test_fifo` (push/pop
FWFT order and the status word, scoreboarded against `FifoModel`).

It is a **bring-up** test. It does not do constrained-random multi-master traffic,
back-pressure/retry stress, full-FIFO/empty-FIFO boundary storms through the bus,
fairness over long runs, or SVA. Those, plus closing the mutation pools, are the
capstone (M2-M4). The released pool `mutants_released.yaml` (8 mutants) is for
practice; the reference smoke test finds all 8.
