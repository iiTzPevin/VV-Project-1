# Week 5 · Session 2 — constraint solving and its two failure modes

You watched this in class. Here it is again so you can run it yourself.

**What it shows.** Constraints fail in two ways. One is loud, and the solver
gives up in the middle of a run. One is quiet, and the constraint set solves
every cycle while shaping nothing at all. A constraint set that provably shapes
nothing still scored 100%, so a single-seed score cannot tell a testbench that
works from one that got lucky.

Run everything from `code/`.

| Step | File | What you should get |
|------|------|---------------------|
| 0 | `step0_start.py` | 7/8, survivor `ignore_full` |
| 1 | `step1_overconstrained_fail.py` | **SolveFailure at cycle 8** |
| 2 | `step2_overconstrained_quiet.py` | 7/8, green |
| 3 | `step3_dist_trap.py` | **8/8 — by luck**, drift **−0.01** |
| 4 | `step4_shaped.py` | 8/8, drift **+0.51 / −0.52** |
| 5 | `step5_seeded.py` | 8 seeds, all pass |

Each step is one command. Here is step 0, in both forms:

```bash
just demo 05 s2 0        # or:  make -C demos/wk05-s2-constraints STEP=0
```

All numbers measured on `dut/fifo.sv` with Icarus against
`tb/fifo_crv/mutants_released.yaml` (8 mutants). Captured output in `expected/`.

---

## Step 0 — the carry-in

```bash
just demo 05 s2 0
```

Re-establish Tuesday's endpoint. 7/8, and `full` is never reached with this
seed. Today is entirely about the one that got away.

> **Check yourself.** Say in one sentence why `ignore_full` survived on
> Tuesday. Your answer should name a state, not a check.

---

## Step 1 — over-constraint, the loud kind

Add four constraints, one at a time. Accept each on its own merits. They are
all things a competent engineer writes:

```python
self.wr_en + self.rd_en >= 1          # never idle
self.wr_en + self.rd_en <= 1          # no simultaneous read+write
self.wr_en == 1                       # keep the pipe busy
with vsc.implies(self.count == self.depth):
    self.rd_en == 1                   # drain when full
```

```bash
just demo 05 s2 1
```

**You should see:**

```
ERROR  solver found no legal transaction at cycle 8, occupancy = 8
vsc.model.solve_failure.SolveFailure: solve failure
```

**What it means.** It ran green for eight cycles. The contradiction only exists
at `count == DEPTH`, so the bug was invisible until the stimulus reached the
state that exposed it. That is what over-constraint looks like in a real
environment: latent, state-dependent, and it surfaces the week you finally get
deep enough.

**Worth 30 seconds.** Try to score this testbench with the mutation harness and
it refuses:

```
[baseline] running clean fifo.sv through step1_overconstrained_fail ...
  ERROR: testbench does not pass on clean RTL (test-failed). Fix the testbench before scoring.
```

A broken testbench fails on every mutant, which is a perfect 8/8 if nobody
checks the clean run first. That baseline is why the harness has one.

> **Check yourself.** Two of the four constraints are enough to make cycle 8
> unsolvable. Name them, and say what occupancy value makes them collide.

---

## Step 2 — over-constraint, the quiet kind

Delete the contradiction. Keep one guard that looks like hygiene:

```python
with vsc.implies(self.count >= self.depth - 1):
    self.rd_en == 1                   # "don't let it overflow"
```

```bash
just demo 05 s2 2
```

Green. Every cycle legal. **7/8 — the same score as step 0.**

The score did not move. Did anything?

**What it means.** Look at the histogram. Occupancy 7 gets 3 cycles, occupancy
8 gets **zero**, and now it is zero *by construction*. In step 0 the FIFO
missed `full` because of the seed. Here no seed can ever reach it. Same number,
categorically different risk, and `found/total` cannot distinguish the two. The
histogram can. This is what "coverage bounds your ignorance" means in one
screen.

> **Check yourself.** You have two runs that both score 7/8. Write the one
> question you would ask to tell them apart, and name the output that answers
> it.

---

## Step 3 — the trap

Write the shaping any textbook would write: a phase field, a weighted `dist`
per phase.

```python
with vsc.implies(self.phase == FILL):
    vsc.dist(self.wr_en, [vsc.weight(1, 85), vsc.weight(0, 15)])
    vsc.dist(self.rd_en, [vsc.weight(0, 80), vsc.weight(1, 20)])
```

**Predict before you run.** With 85% writes and 20% reads, what net drift per
cycle? Most people say about +0.65.

```bash
just demo 05 s2 3
```

**You should see:**

```
--- phase FILL: what did the constraints buy us? ---
induced rates over 400 draws: wr_en=0.53  rd_en=0.54   net drift = -0.01 entries/cycle
--- phase DRAIN: ...
induced rates over 400 draws: wr_en=0.53  rd_en=0.56   net drift = -0.04 entries/cycle
```

**Drift is −0.01, not +0.65.** No error, no warning, and the code reads
perfectly.

**Now find out why.** The obvious guess is that the tool dropped the
constraint. It did not. The second measurement in this step uses a transaction
with a *single* `dist`, guarded to FILL only, and reads it in both phases:

```
guard TRUE  -> P(wr_en=1) = 0.84
guard FALSE -> P(wr_en=1) = 0.84
```

Identical. **`dist` ignores the `implies` that encloses it.** The weighted
distribution is applied to the field unconditionally, in every phase. So the
two-branch version applies 85/15 *and* 20/80 to `wr_en` at all times, and they
average to roughly uniform. The shaping cancels itself.

Note the contrast with step 1. Hard relational constraints inside `implies`
*are* gated correctly. That contradiction only appeared once `count` reached
`DEPTH`. The defect is specific to `dist`. Hold on to that. If you walk away
thinking "`implies` is broken", you have learned something false.

**Now the uncomfortable part — the score is 8/8.**

The stimulus is an unbiased random walk, and on this seed the walk wandered
into `full` and stayed long enough to catch `ignore_full`. Run other seeds:

| seed | 3 | 5 | 7 | 9 |
|---|---|---|---|---|
| `step3_dist_trap` | 7/8 | **8/8** | **8/8** | 7/8 |
| `step4_shaped` | 8/8 | 8/8 | 8/8 | 8/8 |

**What it means.** A constraint set that provably shapes nothing scored 100%.
If you had stopped at the number, you would have shipped it, and told your lead
the boundary was covered. The histogram would not have saved you either. It
showed 16 cycles at `full`. Only measuring the constraint's *induced
distribution* tells you whether the shaping is yours or the seed's.

> **Check yourself.** Your suite scores 8/8 and your histogram shows 16 cycles
> at `full`. Name the one measurement that still says the shaping is worthless,
> and say where in this step's output you read it.

---

## Step 4 — shaping that survives measurement

Since `dist` will not shape inside an implication, shape by hand: one uniform
`roll`, plain implications.

```bash
just demo 05 s2 4
```

**You should see:**

```
induced rates over 400 draws: wr_en=0.73  rd_en=0.21   net drift = +0.51 entries/cycle
induced rates over 400 draws: wr_en=0.23  rd_en=0.75   net drift = -0.52 entries/cycle
```

Same instrument, honest answer. Occupancy is U-shaped: **empty 35 cycles, full
28 cycles**, hollow middle. 8/8.

Note what did *not* change. The scoreboard. Tuesday changed what you observe.
Today changed only where you go.

> **Check yourself.** Step 3 and step 4 both score 8/8. Write down the number
> you would put in a report to defend step 4 and reject step 3.

---

## Step 5 — a regression, not a run

```bash
just demo 05 s2 5
```

**You should see:**

```
  seed   empty-cycles   full-cycles   both boundaries?
     1             35            42   yes
     ...
     8             24            28   yes
  worst boundary residency across 8 seeds: 23 cycles
```

Put it beside Tuesday's lottery table (0–39, two seeds at zero). **Every seed
reaches both boundaries, and the worst case is 23 cycles.** That gap between
luck and property-of-the-testbench is the whole session.

Note the assertion at the bottom of the file. The test *fails* if any seed
misses a boundary. The shaping is not a comment, it is a checked claim.

> **Check yourself.** Name the smallest change to `step5_seeded.py` that would
> turn this regression back into a run, and say what you would lose.

---

## If it breaks

| Symptom | Cause | Fix |
|---|---|---|
| Step 1 does not raise | `txn.count = model.count` line dropped — the guard never fires | The non-random `count` field must be assigned every cycle before `randomize()` |
| Step 3 shows drift ≈ ±0.65 in *both* phases | you deleted one of the two branches | With one branch the dist still applies unguarded — which is the finding, but the cancellation demo needs both |
| `guard TRUE` and `guard FALSE` differ | pyvsc changed behavior | Stop and check `code/setup/verify_env.sh`; the pinned version is what this demo is verified against |
| Step 5 slow | 8 × 200 cycles ≈ 6 s | Trim `SEEDS` to four |
| `SolveFailure` in step 4 | `roll` rangelist dropped, so `roll` can exceed 99 | `c_roll` bounds it to 0–99 |
