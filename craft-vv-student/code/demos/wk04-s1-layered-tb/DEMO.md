# Week 4 · Session 1 — structure buys reuse, not detection

You watched this in class. Here it is again so you can run it yourself.

**What it shows.** Refactoring one tangled function into driver, monitor and
scoreboard moves the mutation score by exactly zero. What it buys is a
testbench that Thursday's debug session and Project 1 reuse unchanged.

Run everything from `code/`.

| Step | File | What you should get |
|------|------|---------------------|
| 0 | `step0_monolith.py` | green, **8/8**, digest `ae8971e8` |
| 1 | `step1_driver.py` | green, same digest |
| 2 | `step2_monitor_scoreboard.py` | green, same digest |
| 3 | `step3_layers.py` | green, **8/8**, digest `ae8971e8` |

Each step is one command. Here is step 0, in both forms:

```bash
just demo 04 s1 0        # or:  make -C demos/wk04-s1-layered-tb STEP=0
```

Every number below was measured on `dut/fifo.sv` with Icarus, `DEMO_SEED=5`,
against `tb/fifo/mutants_released.yaml` (8 mutants). Captured output for each
step is in `expected/`. The stimulus is directed, so the seed changes nothing.
The digest is the invariant to watch. If your digest is not `ae8971e8`, the
vector list moved.

---

## Step 0 — the Week-3 way

```bash
just demo 04 s1 0
```

This is last week's style pointed at a stateful design. It passes.

**Read the file before the output.** One test function owns five jobs:
clocking, reset, prediction (the inline `exp` list), driving, and judging.
Every future scenario re-implements all five.

**Then read the output.** The corner-case checklist is the same list HW4 asks
for, and it is fully ticked. Full reached 4 cycles, write-while-full refused 3
times, empty re-reached 5 cycles, read-while-empty ignored 3 times, 3
mid-stream simultaneous read+writes, 23 accepted writes across 2 pointer
wraps.

**Now the uncomfortable number.** This tangled thing scores **8/8** on the
released pool:

```bash
STEP=0 PYTHONPATH=$PWD/lib python3 -m craft_mutate.mutate \
    --tb demos/wk04-s1-layered-tb --dut dut/fifo.sv \
    --pool tb/fifo/mutants_released.yaml --sim icarus
```

**What it means.** If the score is already 100%, there is no detection reason
to touch this file. That is why HW4 grades architecture separately from
found/total.

> **Check yourself.** The score is 100%. Write down your own answer to "why
> touch it?" before you read step 1. Keep the answer and check it at step 3.

---

## Step 1 — the driver

This step adds two classes. `FifoTxn` is an operation with a name, not four
wires. `FifoDriver` owns the clock, the reset, and the pin protocol. The
vector list becomes transactions. The checks stay tangled on purpose.

```bash
just demo 04 s1 1
```

**You should see:** green, digest `ae8971e8`.

**What it means.** The next testbench that needs a FIFO driven gets this class
for free. That sentence was not true one step ago.

---

## Step 2 — the monitor and the scoreboard

Why should the monitor read the pins instead of asking the driver what it
sent? Because a monitor that trusts the driver lets a driver bug hide itself.

This step builds `FifoMonitor.capture()`, which takes pins in and puts one
`Observed` record out, and `FifoScoreboard.update()`, which predicts with
`FifoModel` and compares count, full, empty, and the FWFT head. The inline
`exp` list is deleted. Prediction and judgment now have homes too.

```bash
just demo 04 s1 2
```

**You should see:**

```
scoreboard: 47 cycles judged, 0 mismatches
```

**What it means.** Find the `first divergence` branch in the scoreboard. It is
the line that logs the cycle number and the pins before raising. It never
fires today. On Thursday it is the first thing you see.

> **Check yourself.** Sketch what a driver bug would look like if the monitor
> asked the driver what it sent instead of reading the pins. Say which check
> would go green when it should be red.

---

## Step 3 — the same tests, through the layers

```bash
just demo 04 s1 3
```

**You should see:**

```
  sequence clean: first in, first out  (7 txns, 7 judged so far)
  sequence clean: fill to full, knock twice  (10 txns, 17 judged so far)
  ...
  stimulus: 47 cycles, digest ae8971e8   (same digest = same vectors)
```

The test body is now a loop over five named sequences. Adding a scenario is
adding a list.

**Now score it:**

```bash
STEP=3 PYTHONPATH=$PWD/lib python3 -m craft_mutate.mutate \
    --tb demos/wk04-s1-layered-tb --dut dut/fifo.sv \
    --pool tb/fifo/mutants_released.yaml --sim icarus
```

**8/8 → 8/8.** Same digest, same checks, same score.

**What it means.** The refactor bought zero mutants, and that is the claim.
Structure is not a detection upgrade. It is a reuse upgrade. What it bought
shows up Thursday, when reproducing a planted bug costs a ten-line test, and
in Project 1, which starts from this file.

**So when does the score move?** When the checklist grows, not when the
architecture does. The 8/8 here is a property of the corner list. Week 5 opens
with an eight-vector hand test that scores 2/8 on the CRV pool, because nobody
thought of the corners it misses. Thinking of every corner is the cost, and
next week is about paying it differently.

> **Check yourself.** Compare this with the answer you wrote at step 0. Then
> name one thing you could add here that *would* move the score.

---

## If it breaks

| Symptom | Cause | Fix |
|---|---|---|
| `ModuleNotFoundError: models.fifo_model` | `PYTHONPATH` not picking up `code/lib` | Run from `code/`, or `export PYTHONPATH=$PWD/lib` |
| Digest differs between step 0 and steps 1–3 | step 0's longhand vector list drifted from `demo_common.SEQUENCES` | Diff the two lists; they are the only place a drift can live |
| `ValueError: ... not convertible to an integer` on clean RTL | reset skipped — the monitor read X | `await drv.reset()` before the loop; in step 0, the inline reset block |
| Hang at 0 ns after retyping the classes | clock never started | `FifoDriver.__init__` starts it; step 0 starts it inline |
| Score differs from 8/8 | DUT or pool moved | Re-check `dut/fifo.sv` and `tb/fifo/mutants_released.yaml` against `expected/` |
