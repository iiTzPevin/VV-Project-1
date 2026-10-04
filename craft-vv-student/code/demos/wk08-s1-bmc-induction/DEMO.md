# Week 8 · Session 1 — BMC finds the bug; only a stronger invariant proves it gone

You watched this in class. Here it is again so you can run it yourself.

**What it shows.** "True" and "inductive" are two different properties of a
property. A property can be true and still fail induction. When induction
fails you strengthen the invariant. Deepening the search cannot help.

Run everything from `code/`.

| Step | File | What you should get |
|------|------|---------------------|
| 0 | `step0_proof.sby` | **PASS ×2** — BMC to depth 20, plus an unbounded k-induction proof |
| 1 | `step1_planted_bmc.sby` | **FAIL, step 9** — a 9-step counterexample trace |
| 2 | `step2_loose_bound.sby` | **UNKNOWN** — a true bound that induction refuses at all sixteen depths |
| 3 | `step3_strengthened.sby` | **PASS** — one added assert, proved in under a second |
| — | `formal_score.py` | **5/8** — the invariant set against the released pool |

Here is step 0, in both forms:

```bash
just demo 08 s1 0        # or:  make -C demos/wk08-s1-bmc-induction STEP=0
```

Steps are `.sby` files, not cocotb, so they need `sby`, `yosys` and `z3`. If a
command is not found, that is an environment problem and not a broken demo.
Setup notes are in `code/formal/README.md`.

Each step runs SymbiYosys (smtbmc + z3) and
leaves its work directory next to the Makefile; a FAIL drops
`engine_0/trace.vcd` there. No `DEMO_SEED`: counterexamples are forced by the
property, not sampled. Every number below was measured on `dut/fifo.sv`
(unmodified; step 1 mutates a `~/.vvtemp` copy) against
`tb/fifo_crv/mutants_released.yaml` (8 mutants), on the course container —
wall-clock times move with the machine, verdicts and step counts do not.
Captured output for each step is in `expected/`. If your run differs, the DUT,
the pool, or the yosys version moved.

If `sby` or `z3` is not on your machine, that is an environment problem and not
a broken demo — see the first row of **If it breaks** below.

Captures were made with
`... 2>&1 | grep -E '\] (summary|DONE)|induction: ##.*(Trying|successful|failed)|^(counterexample|planted|  |====)' | grep -v Elapsed | sed -E 's/^SBY [0-9:]+ //; s/##   [0-9:]+  //'`
— two-task steps captured task-by-task, so a live parallel run interleaves
the same lines in a different order.

---

## Step 0 — get the proof, before you break anything

```bash
just demo 08 s1 0
```

It takes about 33 seconds. In Week 7 you wrote assertions and *simulated*
them. The guarantee was bounded by the stimulus you drove. Same FIFO, same
invariants, no stimulus at all: `wr_en`, `rd_en`, `wr_data` are free inputs,
and the solver considers every value of all of them, every cycle.

The properties are in `formal/fifo/fifo_formal.sv` — count in [0,DEPTH], flag
consistency, no overflow/underflow behavior — asserted through a wrapper so
`dut/fifo.sv` is never edited. This step is `formal/fifo/fifo.sby` run from
the demo dir (`just formal fifo` is the everyday spelling).

**You should see** (`expected/step0.out`):

```
[step0_proof_bmc] DONE (PASS, rc=0)
[step0_proof_prove] summary: successful proof by k-induction.
[step0_proof_prove] DONE (PASS, rc=0)
```

**What it means.** Two different claims. `bmc` = no violation within 20
cycles. `prove` = no violation *ever* — base case plus inductive step. Keep the
two verbs apart. Step 2 drives a wedge between them.

> **Check yourself.** Write down, in one sentence each, what `bmc` PASS
> entitles you to say and what `prove` PASS entitles you to say.

---

## Step 1 — plant the off-by-one, get handed the trace

```bash
just demo 08 s1 1
```

The Makefile plants the released `full_offbyone` mutant (`full` at
`cnt == DEPTH-1`) into `~/.vvtemp/craft-wk08-s1/fifo_bug.sv` and reruns the same
BMC. Nine seconds:

**You should see:**

```
[step1_planted_bmc] summary: engine_0 (smtbmc z3) returned FAIL
[step1_planted_bmc] summary:   failed assertion fifo_formal.$assert$fifo_formal.sv:56$58 at ... step 9
[step1_planted_bmc] DONE (FAIL, rc=0)
```

`DONE (FAIL, rc=0)` — rc 0 because the `.sby` says `expect fail`: the FAIL
verdict is the properties doing their job.

**Open the trace cold** (`step1_planted_bmc/engine_0/trace.vcd` in GTKWave;
signals `rst_n`, `wr_en`, `count`, `full`).

> **Check yourself.** Read the trace before you read the next paragraph. Say
> what the solver drove, and where `full` first tells a lie.

One assumed reset cycle, then seven consecutive writes — count climbs 0 to 7
and `full` rises a cycle early, breaking `full == (count == DEPTH)`. Nobody
hand-writes seven-writes-and-nothing-else as a directed test; the solver
derived the *shortest* path to the lie. There is also a replayable
`trace_tb.v` next to the VCD — HW8 wants a saved trace as evidence.

**Variants worth 30 seconds each:**

```bash
make -C demos/wk08-s1-bmc-induction STEP=1 MUT=count_wr_dec    # FAIL at step 3
make -C demos/wk08-s1-bmc-induction STEP=1 MUT=rd_data_wrptr   # PASS, rc=1
```

The second one is the uncomfortable one: a corrupted read path *proves clean*,
because no property mentions `rd_data`. sby exits non-zero — `expect fail` was
not met — which is the tooling telling you your property set missed. Hold that
thought for Session 2.

---

## Step 2 — meet a property that is true and unprovable by induction

`count` never exceeds 8. So `count <= 9` is also true — trivially, since it is
weaker.

> **Check yourself.** A weaker property should be easier to prove. Predict the
> verdict before you run this step.

```bash
just demo 08 s1 2
```

The property (`step2_loose_bound.sv`):

```systemverilog
// TRUE (reachable counts stop at DEPTH) -- but NOT inductive.
assert (count <= DEPTH + 1);
```

**You should see** sixteen refusals in about a second, then:

```
[step2_loose_bound] summary: engine_0 (smtbmc z3) returned pass for basecase
[step2_loose_bound] summary: engine_0 (smtbmc z3) returned FAIL for induction
[step2_loose_bound] DONE (UNKNOWN, rc=0)
```

UNKNOWN, not FAIL: the base case passed — no reachable violation — but the
inductive step failed at every k from 15 down to 0. Open
`step2_loose_bound/engine_0/trace_induct.vcd`: the solver starts at
**count==9**, a state the loose bound *allows* but reset can never produce,
idles there for 14 cycles (idle and simultaneous read+write both hold count), then one
write-only cycle steps to 10 — violation. Induction does not know
reachability; it starts anywhere the hypothesis permits.

**What it means.** The induction counterexample is not a bug report. It is the
solver naming the spurious pre-state your invariant fails to exclude. Read it
as a to-do list.

---

## Step 3 — prove more to prove it at all

`diff step2_loose_bound.sv step3_strengthened.sv` — one added line:

```systemverilog
assert (count <= DEPTH + 1);
// THE STRENGTHENING: the tight bound IS inductive, and once it
// is in the hypothesis the loose bound rides along.
assert (count <= DEPTH);
```

```bash
just demo 08 s1 3
```

Under a second, same depth 15.

**You should see:**

```
[step3_strengthened] summary: successful proof by k-induction.
[step3_strengthened] DONE (PASS, rc=0)
```

**What it means.** Nobody weakened the goal or deepened the search. One
assertion was *added*, which strengthened the induction hypothesis until the
spurious count==9 start state was excluded. Strengthening is the daily craft of
formal: read the induction trace, name the unreachable pre-state, add the
invariant that rules it out, rerun. HW8's graduate extension is one full lap of
exactly this loop.

> **Check yourself.** Say why adding an assertion can make a proof succeed,
> when adding a test can only ever make a suite slower.

---

## What the pool sweep shows

The no-overflow property needs the FIFO full, then a write attempt.

> **Check yourself.** What BMC depth reaches that corner? Write the number
> down before you read on.

The measured pool sweep is in `expected/pool-sweep.txt`. `ignore_full` is the
deepest counterexample in the pool — **step 11** (reset, eight writes to fill,
the overflowing write, the check). And measured cold: at `depth 10` the same
overflow bug **proves clean** — `DONE (PASS)`. Silence past the bound is not a
proof; that is why step 0 ran `prove` too.

**What Session 2 picks up:** the sweep found 5/8. All three survivors —
`rd_data_wrptr`, `mem_corrupt`, `wrptr_wrap_early` — corrupt *data*, and every
property proved here is about *count and flags*. A proof is exhaustive over
inputs and states, and silent about everything you did not specify. Session 2
is about what that buys you — and what it does not — when the bug is planted
on purpose.

---

## If it breaks

| Symptom | Cause | Fix |
|---|---|---|
| `sby: command not found` / z3 missing | wrong environment | `source ../.venv/bin/activate` or the eustis course env. The setup and property notes are in `code/formal/README.md`. Nothing is wrong with the demo |
| `DONE (PASS, rc=1)` + make error on step 1 | you planted a mutant the invariants cannot see (`MUT=` typo'd or set to a data-path mutant) | default is `MUT=full_offbyone`; the rc=1 is sby reporting `expect fail` unmet |
| `plant_bug: find-string ... not unique` | `dut/fifo.sv` and the pool drifted apart | re-sync; the pool's find strings must match the RTL byte-for-byte |
| Failing assert reported at `fifo_formal.sv:56` but line 56 is the count bound | yosys 0.33 source spans start at the previous statement's end | the failing check is the line-59 flag-consistency assert — the trace (count=7, full=1) is the ground truth, trust it over the label |
| `DONE (UNKNOWN)` on step 2 read as a tool failure | it is the designed outcome | UNKNOWN = unproved, not disproved; basecase passed, induction refused — that distinction *is* the step |
| Work dirs cluttered after an interrupted run | sby was killed mid-run | `sby -f` clears its own work dir on the next run; deleting `step*_*/` dirs (not the `.sby`/`.sv` files) is always safe |
