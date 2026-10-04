# CRAFT V&V Capstone -- runnable DUTs (Weeks 11-14)

Three self-contained capstone DUTs. Each team picks **one track** and verifies it
across the four capstone milestones. Each track gives you the *device under test*, a golden
reference, a released practice mutant pool, and a **bring-up smoke test that
already passes**. You start from a known-good build. Your time goes to
verification, not to getting RTL to elaborate.

> Mutation scoring is **found / total** (we say *found*, never "killed"). You get a
> `mutants_released.yaml` to practice against; grading runs a larger **hidden**
> pool. ~90% found = full mutation credit (see the course policy).

## The three tracks

| Track | Directory | DUT | Golden reference |
|-------|-----------|-----|------------------|
| 1. RISC-V core | `riscv/` | `rv32i_core.sv` -- single-cycle RV32I subset (`add sub and or xor addi andi ori lw sw beq jal`) | `lib/models/rv32i_model.py` (ISS + assembler) |
| 2. Interconnect | `axi_subsystem/` | `axi_subsystem.sv` -- 2-master round-robin arbiter + address-mapped bus + 2 register peripherals + the FWFT FIFO | `lib/models/fifo_model.py` (FIFO slave) |
| 3. Security / trojan | `trojan/` | `secure_gate_clean.sv` (golden) + `secure_gate_trojan.sv` (planted backdoor) | the security properties P1-P3 in the SPEC |

Each track directory contains: `SPEC.md`, the RTL, `mutants_released.yaml`, a
`Makefile` (copy of the ALU/FIFO pattern with `TOPLEVEL`/`MODULE`/`VERILOG_SOURCES`
adjusted), and `test_smoke.py`.

## Run the smoke tests (all pass clean, Icarus)

```
source /opt/course/cocotb-env/bin/activate   # eustis; see INSTALL.md for a laptop
cd code && export PYTHONPATH="$PWD/lib"
make -s -C capstone/riscv          SIM=icarus     # RV32I: 1 test  PASS
make -s -C capstone/axi_subsystem  SIM=icarus     # bus:   3 tests PASS
make -s -C capstone/trojan         SIM=icarus     # secure_gate clean: 2 tests PASS
```

Score your suite against the released pool (each track's DUT lives in its own
directory, so pass `--dut-dir`):

```
python -m craft_mutate.mutate --tb capstone/riscv \
    --pool capstone/riscv/mutants_released.yaml --dut-dir capstone/riscv --sim icarus
python -m craft_mutate.mutate --tb capstone/axi_subsystem \
    --pool capstone/axi_subsystem/mutants_released.yaml --dut-dir capstone/axi_subsystem --sim icarus
python -m craft_mutate.mutate --tb capstone/trojan \
    --pool capstone/trojan/mutants_released.yaml --dut-dir capstone/trojan --sim icarus
```

The provided smoke tests already find every released mutant (8 / 8 / 7). That is
the floor, not the goal -- the hidden pool is larger and the smoke tests do **no**
constrained-random, coverage, or assertion work.

## Milestone map (M1 -> M4)

The capstone is staged. What each milestone means **per track**:

### M1 -- Verification plan + architecture
Read `SPEC.md`; write the vplan (features, stimulus/coverage/checks matrix, risk
list) and your TB architecture (driver / monitor / scoreboard / coverage).
- **RISC-V:** enumerate the 12 opcodes, immediate forms, hazards, corner cases
  (x0 discard, branch taken/not-taken, load-use, address wrap). Plan a
  scoreboard against the ISS.
- **Interconnect:** plan arbiter fairness, address decode, region isolation, and
  the FIFO slave contract; identify the multi-master contention space.
- **Trojan:** state the security properties (P1 no-backdoor, P2 no-leak, P3
  counter-integrity) and how you will *prove* them, not just test them.

### M2 -- Constrained-random + coverage (Ch 7-10; pyvsc + cocotb-coverage)
Replace directed pokes with constrained-random stimulus and close functional +
code coverage.
- **RISC-V:** randomize instruction streams (legal encodings), random data/immediates
  (large/negative), random register targets; cover every opcode x operand class.
- **Interconnect:** randomize both masters' req/we/addr/wdata; cover contention,
  every region, FIFO full/empty boundaries reached *through the bus*.
- **Trojan:** randomize keys/data; cover locked/unlocked paths and the counter --
  and observe that random keys essentially never trip the backdoor (motivates M3).

### M3 -- Assertions / formal + mutation (Ch 11-14; SVA + SymbiYosys)
Add SVA/ABV and, where tractable, formal proofs; then close the mutation pools.
- **RISC-V:** assertions for x0-invariance, link-address correctness, no-write on
  non-writeback ops; mutation-close the ALU/branch/jal/load logic.
- **Interconnect:** assert one-hot grant (mutual exclusion), no-starvation
  fairness, region isolation; reuse the FIFO SVA from Weeks 4-8.
- **Trojan:** **formally prove P1/P2** on `secure_gate_clean.sv` (they hold) and
  show the same proof **fails** on `secure_gate_trojan.sv` -- the backdoor is one
  value in 2^32, so this is the whole point: prove it, don't hunt for it.

### M4 -- Closure + report + demo
Hit the coverage and found/total gates in CI, then write the signoff report
(coverage, mutation score with any justified survivors, assertion/proof results)
and demo it.

## Provided vs. what you build

**Provided (do not need to modify -- but read closely):**
- Synthesizable RTL for each DUT (runs under Icarus and Verilator).
- Golden references: the RV32I ISS + assembler, the FIFO model, the security props.
- A passing `test_smoke.py` per track (bring-up only), a `Makefile`, and a
  `mutants_released.yaml` (~7-8 valid, compiling mutants).
- Observability hooks in the RTL where needed (e.g. the RV32I `dbg_*` read ports).

**You build (the graded capstone):**
- The full verification plan and TB architecture (M1).
- Constrained-random stimulus + functional/code coverage model and closure (M2).
- SVA / formal properties and proofs; drive found/total up on the hidden pool (M3).
- CI gate pass + signoff report + demo (M4). Grad teams add the marked Graduate
  Extension and mini-replication paper.

The smoke tests are deliberately shallow. Treat a green smoke run as *"the DUT is
alive"* -- your job is everything after that.
