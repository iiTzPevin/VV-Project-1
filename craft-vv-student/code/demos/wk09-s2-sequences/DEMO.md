# Week 9 · Session 2 — stimulus is a library; the factory is the reuse lever

You watched this in class. Here it is again so you can run it yourself.

**What it shows.** One factory line swaps the driver under an unchanged test,
and the checking still holds. The homework's stub runs that same agent with no
reference model, and catches 1 of 8. Structure carries the data. The reference
model does the finding.

Run everything from `code/`.

| Step | File | What you should get |
|------|------|---------------------|
| 0 | `step0_sequences.py` | **7/8** — three sequences, 37 reads checked; survivor `ctrl_reset_nonzero` |
| 1 | `step1_factory.py` | 7/8 — one override line, 15 corrupted writes, still 0 mismatches |
| 2 | `step2_score.py` | stub **1/8** · reference **8/8** |

Here is step 0, in both forms:

```bash
just demo 09 s2 0        # or:  make -C demos/wk09-s2-sequences STEP=0
```

The environment in `demo_common.py` is Session 1's agent, imported untouched.
The step files contain only what is new. All numbers measured on
`dut/axil_regfile.sv` with Icarus, `DEMO_SEED=5`, against
`tb/axil_uvm/mutants_released.yaml` (8 mutants). Captured output in
`expected/`.

---

## Step 0 — build the sequence library

Write the three sequences yourself, smallest first. The `wr`/`rd` helpers in
`RegSeqBase` are the idiom to learn: `start_item` / `finish_item` on the
sequence side, the driver's `get_next_item` / `item_done` on the other, and
the sequencer brokering the rendezvous.

```bash
just demo 09 s2 0
```

**You should see:**

```
after SingleWriteSeq   :   1 writes,  0 reads checked, 0 mismatches
after ReadAfterWriteSeq:   4 writes,  3 reads checked, 0 mismatches
after RandomBurstSeq   :  50 writes, 37 reads checked, 0 mismatches
driver in the build: RegDriver
```

**What it means, in two parts.** First: the driver did not change and will
never change again. New behavior means another sequence.

Second, the score: **7/8**, and the survivor is `ctrl_reset_nonzero`.

> **Check yourself.** Three sequences, all green, and one mutant still alive.
> Say which sequence hid it, and what it did.

`SingleWriteSeq` writes CTRL as the first transaction of the day, so no read
ever sees CTRL's reset value. One sequence's convenience deleted another's
observation — a library has an order, and the order is stimulus too.
(A sequence that reads the whole reset map *before* it writes anything never
has this problem — and that ordering is one of the reasons the reference suite
holds 8/8.)

---

## Step 1 — pull the factory override

Open `step1_factory.py` and count what is in it: one driver subclass that
flips one wdata bit on a quarter of writes, one import of step 0's test, and
one line —

```python
uvm_factory().set_type_override_by_type(RegDriver, ErrInjectDriver)
```

> **Check yourself.** The scoreboard compares every read against the model.
> This step corrupts 15 writes on their way to the bus. How many mismatches do
> you expect? Write the number down before you run it.

```bash
just demo 09 s2 1
```

**You should see:**

```
INJECT # 1: flipped wdata bit 11 on WR a=0x0
...
after RandomBurstSeq   :  50 writes, 37 reads checked, 0 mismatches
driver in the build: ErrInjectDriver
corrupted writes injected by the driver: 15
```

**Zero mismatches, and the answer is the architecture.** The monitor samples
the wires, and the scoreboard predicts from what the monitor *saw* — not from
what the sequences intended. Corrupt stimulus is still legal bus traffic, so
the model tracks it. Checking that keeps working when the stimulus lies is
what lets the same environment score mutants — where the corruption comes
from the RTL instead of the driver. (The score stays 7/8, same survivor:
injection cost nothing.)

Now compare the two `driver in the build:` lines from step 0 and step 1.
The test printed them, and the test never learned which driver it got:
`RegDriver.create("driver", ...)` in the agent asked the factory, and the
factory answered differently. That one line is the reuse lever — env, agent,
sequences, test: untouched.

---

## Step 2 — score the week: stub vs reference

```bash
just demo 09 s2 2        # ~1m40s, 18 Icarus runs
```

**You should see:**

```
  [found  ] rvalid_stuck0        (test-failed)  -- rvalid never asserts ...
==== found/total = 1/8  =  12.5%  ====

--- reference environment (model scoreboard) -- recorded ---
    Not in your packet. Its score on this pool is shown below.

  environment                     score
  starter    (stub scoreboard)   found/total = 1/8
  reference  (model scoreboard)  found/total = 8/8   (recorded)
```

Only the starter runs here. The reference environment is the instructor's, so
its 8/8 is printed from record rather than re-measured. `expected/step2.out`
holds the full transcript of that two-environment run if you want to read it.

**What it means.** The stub is your HW9 starting point. It is a correctly
wired agent — driver, monitor, sequencer, analysis port, all working — and it
catches one mutant, because its scoreboard checks `rvalid` and nothing else.
Green on clean RTL, 1/8 on the pool. Structure carries the data; the reference
model does the finding. Your homework is the distance between those two
numbers.

While it runs, scroll the stub's `RegScoreboard.write()` — the TODO comment
marks exactly where the model belongs.

> **Check yourself.** The stub is green on clean RTL and scores 1/8. Name the
> one mutant it does catch, and say what that tells you about what its
> scoreboard reads.

---

## If it breaks

| Symptom | Cause | Fix |
|---|---|---|
| Step 1 prints `driver in the build: RegDriver` | the override line was dropped, or moved after `run_test` | It must run before `run_test`; the factory is consulted at build time |
| Step 1 shows mismatches > 0 | injection moved after `super()._drive(item)` — the corruption missed the bus but stayed in the item | Flip the bit before delegating; the monitor must see what the DUT saw |
| ConfigDB error in `build_phase` | `keep_singletons=True` dropped from `run_test` | The kwarg is load-bearing; `run_test` otherwise clears ConfigDB |
| Step 2: `testbench does not pass on clean RTL` | leftover edits in `tb/axil_uvm` | Restore the starter file; the harness refuses to score a failing baseline |
| Step 2 crawls | it is 18 compile+sim runs | Show `expected/step2.out`; the numbers are the same ones the harness will print |
| Step 0 tallies differ from `expected/` | `DEMO_SEED` exported somewhere | `unset DEMO_SEED` (default 5); the injection stream in step 1 is pinned separately |
