# Week 4 · Session 2 — find a planted FIFO bug and prove the fix

You watched this in class. Here it is again so you can run it yourself.

**What it shows.** The scoreboard names the cycle. Shrinking the test names
the operation. The waveform names the RTL line. A fix counts as verified only
when the minimal case *and* the regression that caught it both rerun green.
Guessing appears nowhere in that chain.

Run everything from `code/`.

| Step | File | What you should get |
|------|------|---------------------|
| 0 | `step0_plant.py` | green, on purpose |
| 1 | `step1_reproduce.py` | **RED — keep it red**, `first divergence: cycle 16` |
| 2 | `step2_isolate.py` | **RED — keep it red**, `head 0xA0 -> 0x5A` |
| — | waveform | `sim_build/fifo.fst`, marker at **110 ns** |
| 3 | `step3_fix.py` | green twice, then **8/8** |

Each step is one command. Here is step 0, in both forms:

```bash
just demo 04 s2 0        # or:  make -C demos/wk04-s2-debug STEP=0
```

Every number below was measured with Icarus, `DEMO_SEED=5`, on the planted
copy `~/.vvtemp/wk04-s2-bug/fifo.sv`. Step 0 creates that copy, and `dut/fifo.sv`
is never touched. The planted bug is `ignore_full` from
`tb/fifo/mutants_released.yaml`, which holds 8 mutants. A write while full is
accepted, so the oldest word is silently overwritten. Captured output is in
`expected/`. Tuesday's testbench comes in through `demo_common.py` — driver,
monitor, scoreboard, and the five sequences, verbatim from
`code/demos/wk04-s1-layered-tb/step3_layers.py`.

---

## Step 0 — plant the bug, then watch nothing notice

```bash
just demo 04 s2 0
```

**You should see:**

```
planted released mutant 'ignore_full' -- writes are accepted even when full (overflow)
  -  assign do_wr = wr_en & ~full;
  +  assign do_wr = wr_en;
[smoke] the Week-3-style test against the planted DUT (icarus):
...
green. A FIFO that overwrites its oldest word on a full-queue write
walks straight past a three-write smoke.
```

**What it means.** This is Tuesday's DUT with one character-level change a
tired engineer makes. The smoke test is green. Scored against the released
pool, that smoke finds 1 of 8. Feel how thin green can be before a debug
starts.

> **Check yourself.** Write down what a three-write smoke test can see, and
> what it cannot. Then hold your list next to the 1 of 8.

---

## Step 1 — reproduce it

```bash
just demo 04 s2 1
```

Read the test before the output. It is ten lines. Everything else is imported
from Tuesday. That is what Session 1 bought.

**You should see:**

```
  sequence clean: first in, first out  (7 txns, 7 judged so far)
first divergence: cycle 16 -- count 9 vs model 8, full 0 vs 1, empty 0 vs 0,
rd_data 0xE0 vs head 0xB0 | pins that cycle: wr_en=1 rd_en=0 wr_data=0xE0
AssertionError: cycle 16: count 9 != model 8
```

**What it means.** Form hypothesis 1, then kill it with the message.
Hypothesis 1 is the obvious one: simultaneous read plus write at the boundary,
which bit you on Tuesday. Now read the pins in the divergence line. `rd_en=0`.
No read was involved. Discard the hypothesis on purpose. The method is
valuable because it survives being wrong.

**What you know now.** A write cycle at the full boundary, cycle 16, count
went to 9, and `rd_data` shows the value you were writing. It reproduces on
demand, at the same cycle every run.

> **Check yourself.** Cover the divergence line. Name the one field in it that
> rules out a simultaneous read and write. Then uncover it and check.

---

## Step 2 — isolate it

Form hypothesis 2 first: count is off by a cycle somewhere. If that were true,
mixed traffic should not matter. So shrink to one operation type and find the
smallest failing sequence. Type it yourself. Eight writes, then a ninth.

```bash
just demo 04 s2 2
```

**You should see:**

```
after 8 writes: count=8 full=1 head=0xA0
after the 9th write (0x5A): count=9 full=0 head=0x5A
0xA0 left the FIFO without a read -- head is 0x5A. The 9th write landed on
the oldest word: a silent drop.
AssertionError: a full FIFO must refuse the 9th write: count 9 != 8
```

**What it means.** Eight writes are clean. The ninth alone diverges.
Hypothesis 2 dies here. There are no reads anywhere, and the failure needs the
full boundary, not a cycle offset. Now look at the data loss. Count says 9 of
8, `full` dropped, and 0xA0 is gone without ever being read. From the
consumer's side this FIFO destroys the oldest word and calls it success.

> **Check yourself.** Your isolation case is nine writes. Name one thing you
> removed that the failure did not need, and say how you know it was not
> needed.

---

## The waveform

```bash
make -C demos/wk04-s2-debug STEP=2 WAVES=1
gtkwave demos/wk04-s2-debug/sim_build/fifo.fst
```

Add `clk`, `wr_en`, `full`, `do_wr`, `count`, `wr_ptr`, `rd_ptr`. Put the
marker at **110 ns**, the ninth write's rising edge. The failing log line
prints at 111 ns. One picture: `full=1`, `wr_en=1`, and `do_wr=1` in the same
cycle. `do_wr` is supposed to be the guarded version of `wr_en`. The guard is
not there. Open `~/.vvtemp/wk04-s2-bug/fifo.sv`, find the `do_wr` assign, and there
is the line. Symptom at the scoreboard, cause at one gate.

> **Check yourself.** Before you open the wave, predict the value of `do_wr`
> at 110 ns. Then read it. Say which signal you would have added next if that
> picture had not been enough.

---

## Step 3 — fix it, then prove the fix

Fix the line in the editor if you want the honest keystrokes, or let the step
do it. It detects a hand-edit and verifies either way:

```bash
just demo 04 s2 3
```

**You should see:**

```
the fix is one line:
  -  assign do_wr = wr_en;
  +  assign do_wr = wr_en & ~full;
byte-identical to dut/fifo.sv: yes
[1/2] the minimal failing sequence (step 2), on the fixed DUT:  ... PASS
[2/2] the full layered regression (step 1), on the fixed DUT:   ... PASS
```

**What it means.** The absence of the symptom is not a fix. The isolation case
must pass, and the regression that caught the bug must pass, and the corner
checklist at the end still shows digest `ae8971e8` — the same tests as
Tuesday.

Then the score:

```bash
STEP=1 PYTHONPATH=$PWD/lib python3 -m craft_mutate.mutate \
    --tb demos/wk04-s2-debug --dut dut/fifo.sv \
    --pool tb/fifo/mutants_released.yaml --sim icarus
```

**8/8** — the reused suite finds the released pool, `ignore_full` included.
The bug the smoke walked past is a bug this testbench cannot miss.

> **Check yourself.** You have one green run. Name the two runs that make it
> evidence, and say what each one rules out.

---

## If it breaks

| Symptom | Cause | Fix |
|---|---|---|
| `no DUT at ~/.vvtemp/wk04-s2-bug/fifo.sv -- run 'make STEP=0'` | steps 1–2 ran before the plant | `make STEP=0`; the Makefile refuses rather than simulate a missing file |
| A red step (1 or 2) runs green | an earlier step 3 already fixed the scratch copy | `make STEP=0` replants; step 0 is always safe to rerun |
| "already restored" from step 3 | you fixed the line by hand during the waveform block | Intended path — it verifies anyway |
| No `fifo.fst` | `WAVES=1` missing from the step 2 rerun | `make STEP=2 WAVES=1`; the file lands in `sim_build/` inside the demo dir |
| Divergence at a cycle other than 16 | `SEQUENCES` in `demo_common.py` drifted from Tuesday's | Digest must read `ae8971e8`; diff against `wk04-s1-layered-tb` |
| `ModuleNotFoundError: models.fifo_model` | `PYTHONPATH` not picking up `code/lib` | Run from `code/`, or `export PYTHONPATH=$PWD/lib` |
