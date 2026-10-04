# Week 7 · Session 1 — say what must always be true, then prove it fired

You watched this in class. Here it is again so you can run it yourself.

**What it shows.** A green assertion is not evidence until its cover fires.
This demo ends with an all-green suite on RTL that drops writes on the floor.
Two zeros are what expose it.

Run everything from `code/`.

| Step | File | What you should get |
|------|------|---------------------|
| 0 | `step0_two_checkers.py` | green, **8/8** |
| 1 | `step1_planted_bug.py` | **fires at 130 ns** |
| 2 | `step2_vacuity.py` + `.sv` | green, **7/8** — covers **0** |

Each step is one command. Here is step 0, in both forms:

```bash
just demo 07 s1 0        # or:  make -C demos/wk07-s1-sva STEP=0
```

All numbers measured on `dut/fifo.sv` with Verilator 5.020 (`--assert`),
`DEMO_SEED=5`, scored against `tb/fifo_sva/mutants_released.yaml` (8 mutants).
Captured output for every step and variant is in `expected/`. Steps 1–2 run
the released `ignore_full` mutant planted into a scratch copy by `plant_bug.py`
— the repo's RTL is never edited. If your run differs, the DUT or the pool
moved.

---

## Step 0 — two layers of checking, both green

```bash
just demo 07 s1 0
```

The scoreboard you built in Week 5 is an *immediate* check. It is a Python
assert that runs when the code calls it. Today you add the other kind:
`dut/fifo_sva.sv`, bound inside the FIFO by `dut/fifo_bind.sv`, compiled with
`--assert`. Nine concurrent properties, sampled at every posedge, whether or
not the testbench is looking.

The walk fills to full, holds, **goes blind for 8 cycles** (six over-writes at
full and two idles with no `check()` call), drains, over-reads. Clean RTL, so:

**You should see:**

```
immediate : check() looked 20 times -- a Python assert checks only when called
blind     : 8 of 28 driven cycles had no check() call at all
concurrent: 9 properties from dut/fifo_sva.sv sampled at every posedge, blind cycles included
```

**What it means.** Look at the bind. The checker sees `do_wr`, `do_rd`, `cnt`,
which are internal signals a black-box scoreboard never has. That is what
`bind` plus `.*` buys. Scored against the released pool: **8/8**. The two
layers together find everything. Hold that number. Step 2 takes most of it away
without changing a single check.

> **Check yourself.** Eight of the 28 driven cycles had no `check()` call.
> Name what is watching those eight cycles, and what is not.

---

## Step 1 — the same walk, one planted bug

```bash
just demo 07 s1 1
```

**Predict before you run.** The over-writes happen where nobody calls
`check()`. The scoreboard passes every look it takes. Who catches the bug?

The Makefile swapped the DUT for a scratch copy of `fifo.sv` with the released
`ignore_full` mutant planted, so writes commit while full. The stimulus is
byte-for-byte step 0's. `step1_planted_bug.py` is an import and a test wrapper,
nothing else.

**You should see:**

```
[130000] %Error: fifo_sva.sv:40: Assertion failed in fifo.u_sva.a_no_overflow: 'assert' failed.
%Error: .../dut/fifo_sva.sv:40: Verilog $stop
```

**What it means.** 130 ns is the first blind over-write edge. The property did
not wait to be called. It sampled `full && do_wr` on the offending cycle and
named the violated contract clause: `a_no_overflow`, file and line. An
end-of-test mismatch tells you *something* broke. This tells you *what*,
*where*, and *when*, at the moment of the crime. That is the whole case for
assertion-based verification in one line of log.

> **Check yourself.** Say why the scoreboard stayed green here, in one
> sentence that names a cycle count.

---

## Step 2 — vacuity: the green that checked nothing

```bash
just demo 07 s1 2
```

**The setup.** Same broken RTL as step 1, so the overflow bug is still compiled
in. New stimulus: Week 5's unshaped random walk, 200 cycles, default seed.
Watching it: all 9 bound properties, the full Week 5 scoreboard, and one more
file — `step2_vacuity.sv`, the overflow property you write for HW7, plus a
`cover` for its antecedent.

Run it, and enjoy the pass. Histogram: the walk tops out at 7, and `full=0
cycles`, the same seed-5 shape as Week 5. Then read the two lines after the
summary table:

**You should see:**

```
[covers] what each `cover property` counted this run:
[covers]   c_full             line  26   count 0   <- NEVER FIRED
[covers]   c_overwrite_seen   line  27   count 0   <- NEVER FIRED
```

**What it means.** The antecedent `(full && wr_en)` held on 0 of 200 cycles.
The in-test count and the tool's count agree. Every implication with a dead
antecedent is true by default. This suite scores **7/8** with `ignore_full`
surviving, the same 7/8 and the same survivor as Week 5 Session 1. Back then
the diagnosis was "the stimulus never reaches full." Today it has its name:
**vacuity**. The cover is the instrument that detects it. A green assert with a
zero cover is a claim nobody tested.

**Now close the loop — two runs, 60 seconds each:**

```bash
make -C demos/wk07-s1-sva STEP=2 DEMO_SEED=8                # same broken RTL
```

Seed 8 parks on `full` (Week 5's lottery table again). The moment the
antecedent finally fires, so does the assertion, at 480 ns
(`expected/step2_seed8.out`). The bug was there the whole time. The seed was
the blindfold.

```bash
make -C demos/wk07-s1-sva STEP=2 DEMO_SEED=8 DUT=$PWD/dut/fifo.sv   # clean RTL
```

Green again — but now `c_full` counts 39 and `c_overwrite_seen` counts 15
(`expected/step2_seed8_clean.out`). *This* green is evidence. The property was
armed 15 times and held. That is the discipline HW7 grades: every assert ships
with a cover, and a pass counts only when both are green.

> **Check yourself.** You have three green runs in this step. Rank them by how
> much evidence each one carries, and give the cover count that decides each
> rank.

---

## The bridge out

Write `empty |-> !do_rd` and its cover against the running smoke test. Session
2 takes the same discipline to a protocol DUT: the UART, where the properties
are about *time*, and the first security assertion.

> **Check yourself.** Predict whether that antecedent fires before you run it.
> Then run it and compare.

---

## If it breaks

| Symptom | Cause | Fix |
|---|---|---|
| step 1 or 2: `plant_bug: find-string not unique` or a compile error on the scratch DUT | `dut/fifo.sv` drifted from the released pool's find-strings | Re-sync `fifo.sv` and `tb/fifo_sva/mutants_released.yaml`; the harness itself would refuse the same way |
| step 2 prints no `[covers]` lines | Ran a raw cocotb target (`make sim`), which skips the post-run cover print, or coverage.dat was not written | Run plain `make STEP=2` — its default goal runs the sim *then* `show_covers.py` |
| step 2 covers > 0 with the default seed | `DEMO_SEED` exported in your shell | `unset DEMO_SEED`; the default is 5 |
| step 2 histogram differs from `expected/` | pyvsc version moved — the walk is the pinned stream | `bash code/setup/verify_env.sh`; the demo is verified against the pinned pyvsc |
| A fire in step 0, or the clean-DUT variant fires | Stale model: a build dir reused across DUT swaps | Build dirs are keyed `step<N>-<dutname>`; if you renamed things, `rm -rf sim_build` |
