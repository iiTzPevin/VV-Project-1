# axil_regfile specification (dut/axil_regfile.sv)

A small **synchronous register file** behind a **lightweight bus** (deliberately
*not* full AXI-Lite — no handshakes to stall on, so it is easy to drive from a
UVM driver). Used in Weeks 9-10 (pyuvm environment + automated register tests).

## Ports
| Signal | Dir | Width | Meaning |
|--------|-----|-------|---------|
| `clk` | in | 1 | rising-edge clock |
| `rst_n` | in | 1 | active-low **synchronous** reset |
| `req` | in | 1 | a transaction is valid this cycle |
| `we` | in | 1 | 1 = write, 0 = read |
| `addr` | in | 4 | word address |
| `wdata` | in | 32 | write data |
| `rdata` | out | 32 | **registered** read data |
| `rvalid` | out | 1 | read-data valid, **one cycle after** a read `req` |

## Bus protocol (the timing contract)
- A transaction happens on any cycle where `req==1`.
- **Write:** `req && we` at a rising edge commits the write on that edge.
- **Read:** `req && !we` at a rising edge causes `rdata` (the addressed register,
  through a combinational read mux) to be **registered** and presented with
  `rvalid==1` on the following cycle. `rvalid` is 0 for write cycles and idle
  cycles. There are no wait states; one transaction may be issued per cycle.
- After reset, `rdata==0` and `rvalid==0`.

## Register map and access policies (the functional contract)
| Addr | Name | Policy | Behavior |
|------|------|--------|----------|
| 0x0 | CTRL | **RW** | plain read/write storage |
| 0x1 | STATUS | **RO** | writes ignored; reads the fixed pattern `0x5A5A_0F0F` |
| 0x2 | SCRATCH | **RW** | plain read/write storage |
| 0x3 | INTR | **W1C** | writing a 1 to a bit clears that bit; writing 0 leaves it. Hardware **sets** bit0 on a security violation (see LOCK/SECURE) |
| 0x4 | LOCK | **RW** | `bit0` = lock enable |
| 0x5 | SECURE | **locked-RW** | writable **only while `LOCK.bit0 == 0`**; while locked, writes are **ignored** but reads are still allowed |
| 0x6-0xF | — | — | unmapped: reads return 0, writes ignored |

## Reset values
`CTRL=0`, `STATUS=0x5A5A_0F0F`, `SCRATCH=0`, `INTR=0`, `LOCK=0`, `SECURE=0`.

## The security interaction (Week 10's security check)
When software attempts to write **SECURE while `LOCK.bit0 == 1`**, the write is
dropped **and** hardware latches `INTR[0]` (a "security violation" interrupt).
`INTR[0]` is then cleared by writing 1 to it (W1C). This is the only path that
*sets* an INTR bit, so it is also what makes the W1C behavior observable from a
pure register test:

1. write `LOCK = 1` (lock),
2. attempt `SECURE = X` -> dropped, and `INTR[0]` becomes 1,
3. read `INTR` -> bit0 set,
4. write `INTR = 0x1` (W1C) -> bit0 clears; read `INTR` -> 0.

## Corner cases a good testbench must hit
- Reset values of every register (incl. STATUS's fixed pattern).
- Bit-bash (walking-ones + all-ones + zero) on the RW registers CTRL/SCRATCH.
- **RO**: writes to STATUS never change its read value.
- **W1C**: a 1 clears, a 0 does not; hardware-set then W1C-clear round-trip.
- **SECURE locked**: writes rejected while `LOCK=1`, accepted while `LOCK=0`;
  the locked-write also raises `INTR[0]`.
- Unmapped addresses read 0.
- Read latency / `rvalid` timing.
