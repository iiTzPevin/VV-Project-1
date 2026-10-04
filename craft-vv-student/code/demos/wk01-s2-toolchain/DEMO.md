# Week 1 · Session 2 — the toolchain, end to end

You watched this in class. Here it is again so you can run it yourself.

**What it shows.** The whole flow is one `make` once your environment checks
out. The first red banner of the semester was the checker's bug, not the
design's. A checker is a model you have to verify too.

Run everything from `code/`.

| Step | What runs | What you should get |
|------|-----------|---------------------|
| 0 | `bash ../../setup/verify_env.sh` | **5 OK, 1 opt** |
| 1 | `make -C tb/alu SIM=icarus` (recursed) | **PASS=1** |
| 2 | `step2_add_vector.py` | **FAIL, on purpose** |
| 3 | `step3_model_width.py` | TESTS=2 **PASS=2** |
| — | scoring aside | **1/8 → 2/8** |

Each step is one command. Here is step 0, in both forms:

```bash
just demo 01 s2 0        # or:  make -C demos/wk01-s2-toolchain STEP=0
```

Steps 0 and 1 are toolchain commands, dispatched by the Makefile. Steps 2 and
3 are cocotb modules. They are a copy of `tb/alu/test_alu.py` held in this
directory plus one edit each, so the course starter stays untouched. All
numbers were measured with Icarus. `SIM=verilator` also passes, and it is what
the deck shows. Mutation scores are against `tb/alu/mutants_released.yaml`,
which holds 8 mutants. Captured output is in `expected/`.

---

## Step 0 — check your environment

```bash
just demo 01 s2 0
```

**You should see:**

```
=== CRAFT V&V toolchain ===
OK   verilator: Verilator 5.020 2024-01-01 rev (Debian 5.020-1)
OK   iverilog: iverilog: invalid option -- '-'
OK   yosys: Yosys 0.33 (git sha1 2584903a060)
...
OK   cocotb: 1.9.2
...
=== end-to-end smoke (ALU under icarus) ===
OK   smoke: ALU reference testbench passes
=== done ===
```

**What it means.** One command answers "is my machine ready for the
semester". Each line names the week that needs the tool. The last line
compiled RTL, ran a testbench, and read the result. If that says OK, nothing
this course asks of your machine is untested.

Three lines are worth a closer look. The `opt gtkwave` line means optional, so
install it when you want waveforms. The odd `iverilog: invalid option` text is
cosmetic, because iverilog has no `--version` flag, and OK still means found.
The `wk5-dist-guard` line asserts a Week 5 lecture premise. Ignore it today.
It will make sense in October.

Run the same command on your own laptop or on eustis. Two known time-sinks
show up: GTKWave on Windows and a stale Verilator. Both have a row in the Fix
table below.

> **Check yourself.** Cover the output and name the six things this script
> checks. Then say which week needs each one.

---

## Step 1 — get your first green run

Walk the anatomy before running: `dut/alu.sv` (the design), `tb/alu/
test_alu.py` (stimulus and checks — the `assert` line is the verification,
the rest is setup), `tb/alu/Makefile` (wires design to simulator). Then:

```bash
just demo 01 s2 1        # recurses:  make -C tb/alu SIM=icarus
```

**You should see:**

```
** TEST                          STATUS  SIM TIME (ns) ... **
** test_alu.test_smoke            PASS           1.00 ... **
** TESTS=1 PASS=1 FAIL=0 SKIP=0                  1.00 ... **
```

**What it means.** That banner is the machine's verdict. It is the only line
of the run a grader reads.

### Now do it again with waves

Waves are **off by default**. A plain run writes no trace at all. Use the
recipe rather than the flag, because the flag is simulator-specific and it
fails quietly:

```bash
just waves alu              # Icarus:    WAVES=1          -> tb/alu/sim_build/alu.fst
just waves alu verilator    # Verilator: VERILATOR_TRACE=1 -> tb/alu/dump.vcd
```

The recipe prints the file it wrote. Open that file with `gtkwave`, for
example `gtkwave tb/alu/sim_build/alu.fst`.

**The trap.** `WAVES=1` under Verilator is silently ignored: green banner, no
file, no error. That one costs people a whole afternoon.

One test, one vector, 1 ns of simulated time. The waveform shows `a=3, b=4,
result=7` and *when* they settled, which the banner cannot say.

> **Check yourself.** This run is green. What exactly did it prove? Answer
> before you read on. (One vector, one op, result only.)

---

## Step 2 — make the first edit, and meet the classic first failure

Open `step2_add_vector.py`. It is the starter file plus the one thing everyone
adds first, a new test with a hand-written expectation. The vector is
Tuesday's: `a = b = 0x90`. The expectation is `a + b`.

```bash
just demo 01 s2 2
```

**You should see:**

```
AssertionError: ADD a=0x90 b=0x90: result 32 != 288
assert 32 == (144 + 144)
 +  where 32 = int(00100000)
** step2_add_vector.test_smoke            PASS ... **
** step2_add_vector.test_equal_operands   FAIL ... **
```

**What it means.** Read it bottom-up, then answer the question: which is
wrong, the design or the test? Look at `int(00100000)`. That is eight bits.
288 needs nine. The DUT computed the correct 8-bit sum and the correct carry.
The checker demanded a number no 8-bit wire can hold. The first failure of the
semester is in the test, which is the normal case, and it is why a checker is
a model you have to verify too.

> **Check yourself.** Before you look at step 3, write down the fix you would
> make. Then check whether your fix pastes a mask into the assert or asks
> something that already knows the width.

---

## Step 3 — move the expectation into the model

The fix is not `& 0xFF` pasted into the assert. It is asking
`models.alu_model`, which owns the width. And the model also hands back the
bit that 288 was trying to smuggle out, so check `carry` too.

```bash
just demo 01 s2 3
```

**You should see:**

```
** step3_model_width.test_smoke            PASS ... **
** step3_model_width.test_equal_operands   PASS ... **
** TESTS=2 PASS=2 FAIL=0 SKIP=0 ... **
```

**The scoring aside.** The released ALU mutant pool ships this week for
Week 3. Nothing is graded yet. Here is what green is worth, measured against
the 8 released mutants:

```
starter, untouched (what step 1 ran)      ==== found/total = 1/8  =  12.5%  ====
with the step-3 edit                      ==== found/total = 2/8  =  25.0%  ====
  [found  ] drop_add_carry       (test-failed)  -- ADD never reports carry-out
reference solution                        ==== found/total = 8/8  =  100.0%  ====
```

One added check bought exactly one mutant (`drop_add_carry`). And scoring the
*broken* step 2 refuses outright:

```
[baseline] running clean alu.sv through score_step2 ...
  ERROR: testbench does not pass on clean RTL (test-failed). Fix the testbench before scoring.
```

A testbench that fails on everything would "find" every mutant. The clean-RTL
baseline is why the harness cannot be fooled by one.

**What it means.** Green and 12.5% is what "it passes" is worth. Weeks 2 and 3
are about the other seven.

To reproduce the step-3 score: copy `step3_model_width.py` and
`demo_common.py` to a scratch dir with `tb/alu`'s Makefile
(`MODULE = step3_model_width`, keep `DUT ?=` overridable), then from `code/`:
`python3 -m craft_mutate.mutate --tb <scratch> --dut dut/alu.sv --pool
tb/alu/mutants_released.yaml --sim icarus`. The starter's score is
`just mutate alu`.

> **Check yourself.** One added carry check bought one mutant. Name a second
> check you could add, and predict whether it buys another.

---

## If it breaks

| Symptom | Cause | Fix |
|---|---|---|
| `verify_env.sh` shows `MISS python:cocotb` (or `cocotb-config: command not found`) | venv not active | `source /opt/course/cocotb-env/bin/activate` on eustis, `../.venv/bin/activate` locally |
| Verilator errors on your laptop | distro Verilator < 5 fighting cocotb | take the Appendix A build-from-source path — do not sink an afternoon into the distro package |
| GTKWave shows nothing on Windows | WSLg vs VcXsrv display | browser-shell fallback; waveforms are optional today |
| Step 2 passes | you ran step 3, or someone repaired the copy | the broken assert is the exhibit — restore it |
| Stray `sim_build/`/`results.xml` in `tb/alu` after a run | step 1 recurses into the course tree | `just clean` (or delete them by hand) |
| Scoring step 2 "fails" | it refuses at the clean-RTL baseline | that refusal is the teaching point — quote it |
