# Week 3 · Session 2 — find a bug with a wave, measure your tests with mutants

You watched this in class. Here it is again so you can run it yourself.

**What it shows.** A green test suite is a claim about the vectors you drove,
and nothing more. `found/total` measures that claim. Every survivor names a
vector you never drove.

Run everything from `code/`.

| Step | File | What you should get |
|------|------|---------------------|
| 0 | `step0_first_divergence.py` | first divergence at **t=1ns**, plus `dump.vcd` |
| 1 | `step1_survivors.py` | **7/8** — `drop_add_carry` survives |
| 2 | `step2_strengthened.py` | **8/8** |

Every number here was measured on `dut/alu.sv` against
`tb/alu/mutants_released.yaml`, which holds 8 mutants. Scoring used Icarus. The
traced run used Verilator 5.020. Saved output is in `expected/` if you want to
compare. One pool run is 9 simulator calls and takes about 51 seconds.

---

## Step 0 — plant a bug, then find it in the wave

Run the clean version first, so you know what working looks like:

```bash
make -C demos/wk03-s2-waves-mutants STEP=0 SIM=verilator VERILATOR_TRACE=1
# -> clean: DUT and model agree on all 10 vectors
```

Now plant one bug into a copy of the RTL and run it again:

```bash
make -C demos/wk03-s2-waves-mutants plant MUTANT=add2sub
rm -rf demos/wk03-s2-waves-mutants/sim_build      # important, see The trap below
make -C demos/wk03-s2-waves-mutants STEP=0 DUT=~/.vvtemp/alu_add2sub.sv SIM=verilator VERILATOR_TRACE=1
```

**You should see:**

```
DIVERGE t=1ns  ADD a=0x03 b=0x04      result dut 0xff != model 0x07 | carry dut 1 != model 0 | overflow dut 1 != model 0
DIVERGE t=3ns  ADD a=0x7f b=0x01      result dut 0x7e != model 0x80 | overflow dut 0 != model 1
first divergence at t=1ns -- 2/10 vectors diverge; put the wave cursor there
AssertionError: 2 divergences; read the wave at t=1ns
```

You also get a `dump.vcd` of about 2.3 KB in the demo folder. This step logs
every divergence and then fails once at the end. A test that stopped at the
first mismatch would have cut the trace short.

### Read the wave

Open it with `gtkwave demos/wk03-s2-waves-mutants/dump.vcd`, then:

1. Insert from scope `alu`: `a`, `b`, `op`, `result`, `zero`, `carry`,
   `overflow`. Set data format to hex for the buses.
2. Move the cursor to **1 ns**, the first divergence the log named. Each vector
   holds the bus for 2 ns and the sample lands mid-column, so the cursor sits
   inside the offending vector. You should read `a=03 b=04 op=0` (ADD), and
   `result=ff carry=1 overflow=1`. The model wanted `07 / 0 / 0`.
3. Check the other logged time, 3 ns. Also an ADD. Ten vectors, two
   divergences, both of them ADD. The AND, OR, XOR, set-less-than and shift
   columns all agree with the model. So the bug is in the adder. You worked
   that out without opening the RTL.
4. Confirm it: `diff dut/alu.sv ~/.vvtemp/alu_add2sub.sv`. Line 33, a `+` became a
   `-`. One character.

**No GTKWave, or no display?** You can still finish this step. Check three
facts by hand instead. `dump.vcd` exists after the run. `grep '\$var' dump.vcd`
lists all seven signals above. The state covering t=1ns is
`a=0x03 b=0x04 op=0x00 result=0xff carry=1 overflow=1`.

**What it means.** The failing check tells you *when*. The wave tells you
everything else that was true at that moment. Failing check, then time, then
wave, then cause. That is the debugging loop you will use for the rest of the
course.

**The trap.** If you switch `DUT=` without deleting `sim_build`, make reuses
the RTL it compiled last time. The build is newer than the source, so make
skips the rebuild. Your planted run then stays green, or your clean run stays
red, and nothing warns you. Delete `sim_build` between DUT switches.

**On your own testbench,** use `just waves alu` rather than remembering the
flag. It clears the stale `sim_build`, picks `WAVES=1` for Icarus or
`VERILATOR_TRACE=1` for Verilator, and prints the path to open.

> **Check yourself.** Before you open the wave, predict which of the seven
> signals will be wrong at t=1ns. Then look. Getting this wrong is useful.

---

## Step 1 — score a green suite

This suite is where Session 1 ended: every operation driven, all four outputs
asserted, green on clean RTL. Now measure it.

A mutant is a small, exact change to the source. Open
`tb/alu/mutants_released.yaml` and read two of them: `add2sub`, which you just
met in the wave, and `drop_add_carry`. A mutant is **found** when your suite
goes red on the mutated RTL. Your score is found over total. We say *found*,
never "killed."

**Predict your score before you run this.** Write the number down.

```bash
STEP=1 python3 -m craft_mutate.mutate --tb demos/wk03-s2-waves-mutants \
    --pool tb/alu/mutants_released.yaml --sim icarus
```

**You should see** (full transcript in `expected/step1-pool.txt`):

```
  clean RTL: 1 tests passed.
  [found  ] add2sub              (test-failed)  -- ADD computes a - b instead of a + b
  ...
  [SURVIVED] drop_add_carry       (passed)  -- ADD never reports carry-out
  ...
==== found/total = 7/8  =  87.5%  (threshold 90%) ====
surviving mutants: drop_add_carry
```

A suite you would have shipped missed an injected bug outright. It passed, and
the bug was right there.

**Work out why before you read the yaml.** What does it take to *see* a dead
carry-out? You need an ADD whose sum needs more than eight bits. No vector in
`demo_common.VECTORS` goes past `0xff`. The suite is not wrong. It is silent
about a place it never drove.

That is the Week 1 vocabulary: the checker gave you observability, but the
stimulus never gave you controllability of that corner.

> **Check yourself.** Name the exact stimulus that would make the dead carry
> visible. Aim for the smallest one you can remember.

---

## Step 2 — one vector for the survivor

`step2_strengthened.py` is step 1 plus one line:

```python
VECTORS_PLUS = VECTORS + [
    (0x80, 0x80, OP_ADD),   # equal operands, sign boundary: 0x00, carry=1, overflow=1
]
```

Run the suite green first (`just demo 03 s2 2`, now 11 vectors), then score it
again:

```bash
STEP=2 python3 -m craft_mutate.mutate --tb demos/wk03-s2-waves-mutants \
    --pool tb/alu/mutants_released.yaml --sim icarus
```

**You should see** (full transcript in `expected/step2-pool.txt`):

```
  [found  ] drop_add_carry       (test-failed)  -- ADD never reports carry-out
==== found/total = 8/8  =  100.0%  (threshold 90%) ====
```

**7/8 to 8/8, for one aimed vector.**

**What it means.** The survivor list is a to-do list. Each entry names a
stimulus you never drove, or an output you never checked. The loop is: score,
read the survivors, aim, score again. That loop is HW3 — same DUT, this
released pool to practise on, and a hidden pool for the grade.

---

## If it breaks

| Symptom | Cause | Fix |
|---|---|---|
| Planted run stays green, or the clean run stays red | stale `sim_build`, compiled from the other DUT | `rm -rf demos/wk03-s2-waves-mutants/sim_build` between `DUT=` switches |
| No `dump.vcd` | `VERILATOR_TRACE=1` missing, or `SIM` left at icarus | Re-run with `SIM=verilator VERILATOR_TRACE=1`. **Verilator silently ignores `WAVES=1`** — green run, no file, no error — so it is not a substitute. With Icarus, `WAVES=1` *is* the flag, and it writes `sim_build/alu.fst`. GTKWave opens that too |
| Pool run scores the wrong step | `STEP=N` typed after the command, or left off, so it defaults to 0 | The env assignment goes before `python3`. Check the harness banner names the module you meant |
| `make plant` fails with a find-string error | `dut/alu.sv` has drifted from the released pool | Re-sync the pool's `find` strings against the DUT. The harness would refuse the same way |
| No GTKWave on your machine | — | Use the three checks in step 0. The log alone carries the localization story |
