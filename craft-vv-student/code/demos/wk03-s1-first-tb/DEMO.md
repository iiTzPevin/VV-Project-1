# Week 3 · Session 1 — your first self-checking testbench

You watched this in class. Here it is again so you can run it yourself.

**What it shows.** Where you sample decides what you test. One settle too
early and every check grades the previous vector's answer. The suite still
goes green, so nothing warns you.

Run everything from `code/`.

| Step | File | What you should get |
|------|------|---------------------|
| 0 | `step0_drive_only.py` | green, and **0/8** |
| 1 | `step1_sample_early.py` | red — 10/10 reads wrong, no score |
| 2 | `step2_settle_then_sample.py` | green, **5/8** |
| 3 | `step3_check_flags.py` | green, **7/8** |

Each step is one command. Here is step 0, in both forms:

```bash
just demo 03 s1 0        # or:  make -C demos/wk03-s1-first-tb STEP=0
```

Every number below was measured on `dut/alu.sv` with Icarus, `DEMO_SEED=5`,
against `tb/alu/mutants_released.yaml` (8 mutants). The found/total per step
is in `expected/pool-curve.txt`, reproducible with the `STEP=N python3 -m
craft_mutate.mutate ...` commands recorded there. Week 3 stimulus is directed,
so the seed pins nothing yet. It is logged to set the habit. Captured output
for each step is in `expected/`. The scores are only context today. Mutation
itself is Thursday's subject.

---

## Step 0 — run the testbench that cannot fail

```bash
just demo 03 s1 0
```

Ask an AI assistant for a cocotb test and this shape is what you will get most
often. It drives everything and checks nothing. It is also the shape of
`tb/alu/test_alu.py` before the TODOs are filled, so your homework starts
here.

**You should see:** a tidy results table, then

```
10 vectors driven, 0 values checked
** TESTS=1 PASS=1 FAIL=0 SKIP=0 **
```

**What it means.** It passed. So what do you now know about the ALU? Only
which vectors were driven. Nothing about whether any output was right. Every
`result` in that table could be garbage and the run stays green. Green means
"no check failed". With zero checks that is a statement about the testbench,
not the design. Scored against the released pool this suite finds **0/8**.
Hold that number for Thursday.

> **Check yourself.** Write down one sentence this green run entitles you to
> say about the ALU. Then cross out every word of it you cannot defend.

---

## Step 1 — the sampling off-by-one

Here is the checking loop, with the read where a programmer's reflex puts it,
on the line after the drive:

```python
drive(dut, a, b, op)
got = int(dut.result.value)    # BUG: sampled before the settle
await Timer(1, units="ns")     # the settle happens after we looked
```

Before you run it, predict what happens. The first vector is 3 + 4. What does
the read see? Most people say 7, or maybe X.

```bash
just demo 03 s1 1
```

**You should see:**

```
ADD a=0x03 b=0x04      read 0x00   model says 0x07   WRONG  <- the previous vector's answer
ADD a=0x7f b=0x01      read 0x07   model says 0x80   WRONG  <- the previous vector's answer
SUB a=0x2a b=0x2a      read 0x80   model says 0x00   WRONG  <- the previous vector's answer
...
10/10 reads wrong -- and 10/10 match the vector BEFORE the one we asked about
AssertionError: sampled one settle too early on 10 vectors
```

Look at the diagonal. The read column is the model column shifted down one
row. Nothing is corrupt. `0x07` is a perfect answer, to the question you asked
one vector ago.

**What it means.** Assignments are *scheduled*, not applied. `await` is where
the simulator gets control to apply them and settle the combinational cloud.
Sequential Python statements are not sequential simulated time. And the values
are wrong-but-plausible. `0xfe` for an AND is a fine-looking byte. Without the
model on the same line, nothing here looks broken.

The mutation harness refuses to score this testbench:

```
[baseline] running clean alu.sv through wk03-s1-first-tb ...
  ERROR: testbench does not pass on clean RTL (test-failed). Fix the testbench before scoring.
```

A testbench that fails on everything would otherwise "find" all 8 mutants.
The clean-RTL baseline exists exactly for this.

> **Check yourself.** Cover the model column and read only the values. Could
> you tell they were wrong? Name what made them wrong-but-plausible.

---

## Step 2 — the fix: settle, then sample

The fix is two lines trading places. Open the file:

```python
drive(dut, a, b, op)
await Timer(1, units="ns")     # let the combinational cloud settle
got = int(dut.result.value)    # NOW the value answers this vector
```

```bash
just demo 03 s1 2
```

**You should see:** `10/10 results checked against the model` — green.

**What it means.** The rule that generalizes is *sample after the event that
makes the value valid*. Here that event is a 1 ns settle. On Thursday's traces
and every clocked design after, it is the clock edge plus the read-only phase.
Same discipline, different trigger. This green is a different substance than
step 0's. Ten predictions were made and ten matched. Score: **5/8**.

> **Check yourself.** In your own testbench, name the event that makes the
> value you sample valid. If you cannot name it, you do not know when to read.

---

## Step 3 — check what the spec names

The spec names four outputs. Step 2 asserts one. What can hide in the other
three? Then run:

```bash
just demo 03 s1 3
```

**You should see:** `10 vectors x 4 outputs checked` — green.

**What it means.** Three released mutants live entirely in the flags. A
dropped carry, a dropped overflow, an inverted zero. Result-only checking can
never see them, however many vectors it drives. Four asserts per vector raise
the score from 5/8 to **7/8**. One mutant is still hiding, and Thursday opens
with it. This suite checks everything the spec names on every vector it
drives, and it is still missing something. Thursday you measure what.

> **Check yourself.** Your suite drives 10 vectors and checks 4 outputs on
> each. Name something it still cannot see. Then hold your answer until
> Thursday.

---

## If it breaks

| Symptom | Cause | Fix |
|---|---|---|
| The step 1 run passes | the two loop lines got typed in the fixed order | The bug *is* the order: read first, `await Timer` second. Compare against `step2_settle_then_sample.py` |
| First read in step 1 raises on an unresolvable value | the park-at-a-known-state drive+settle before the loop was dropped | Restore the two lines above the loop; at t=0 the outputs have never settled |
| Mismatches but not the neat diagonal | `VECTORS` edited or reordered | The diagonal depends on adjacent vectors having distinct answers; restore `demo_common.VECTORS` |
| `ModuleNotFoundError: models.alu_model` | step run outside the demo Makefile | Run via `make -C demos/wk03-s1-first-tb STEP=N` (it exports `PYTHONPATH`), or `export PYTHONPATH=$PWD/lib` from `code/` |
| `iverilog: command not found` | wrong shell | `source /opt/course/cocotb-env/bin/activate` |
