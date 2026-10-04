# Week 1 · Session 1 — the bug a green test walks right past

You watched this in class. Here it is again so you can run it yourself.

**What it shows.** Green means nothing you drove made anything you watched go
wrong. This test drives 6 input pairs out of 65,536. The bug lives in 128
pairs it never touches.

Run everything from `code/`.

| Step | File | What you should get |
|------|------|---------------------|
| 0 | `step0_looks_fine.py` | **PASS, 6/6** |
| 1 | `step1_the_vector.py` | **FAIL, on purpose** |
| 2 | `step2_observation.py` | PASS, **0 vs 128** |

Each step is one command. Here is step 0, in both forms:

```bash
just demo 01 s1 0        # or:  make -C demos/wk01-s1-first-look STEP=0
```

The DUT is `addc.sv` in this directory. It is the ADD slice of the ALU. The
planted bug: the `a == b` path takes an "optimization" (`a + a` is a shift),
and the 8-bit shift has nowhere to put the ninth bit, so on that path
`carry_out` can never be 1. The sum stays correct. The bug is wrong for
exactly 128 of 65,536 input pairs, every one on the `a == b` diagonal with the
top bit set.

All numbers below were measured with Icarus at `DEMO_SEED=5`. The vectors are
directed, so the seed is pinned out of habit. Captured output for each step is
in `expected/`. If your run differs, `addc.sv` moved.

---

## Step 0 — run the weak test everyone writes first

Open `addc.sv` before you run anything. The header comment says one line below
is wrong. It does not say which line. Then run:

```bash
just demo 01 s1 0
```

**You should see:**

```
     a     b       sum   carry_out
  ----  ----      ----   ---------
  0x01  0x02      0x03   0
  0x00  0x00      0x00   0
  0x37  0x28      0x5f   0
  0xff  0x01      0x00   1
  0x05  0x05      0x0a   0
  0x80  0x7f      0xff   0
6/6 vectors match the model
```

**What it means.** Eyeball the table. That is your waveform. 0xFF plus 1 wraps
to zero with a carry. It looks right. This test is also better than
eyeballing. Every row was checked against a golden model, carry included, and
there is even an equal-operands vector. It is the kind of test people sign off
on. Sit in that false confidence for a moment. It is the lesson.

> **Check yourself.** What do these six vectors have in common with each other
> and not with the other 65,530?

---

## Step 1 — add the vector that was missing

This step adds one vector: `(0x90, 0x90)`. Equal operands, top bit set.

```bash
just demo 01 s1 1
```

**You should see:**

```
  0x90  0x90      0x20   0   <-- WRONG (model says sum=0x20 carry_out=1)
AssertionError: a=0x90 b=0x90: got sum=0x20 carry_out=0, model says sum=0x20 carry_out=1
assert (32, 0) == (32, 1)
```

**What it means.** Read the assert line closely: `(32, 0) == (32, 1)`. The
first number matches, so the sum is right. Only the carry is wrong. A checker
watching `sum` alone stays green *on the exposing vector itself*. One line
holds two separate ways a test misses a bug. You never drive the condition, or
you never watch the output it corrupts.

Now look at the mechanism in `addc.sv`:

```systemverilog
assign ext = (a == b) ? {1'b0, a << 1}        // "a + a is a shift"
                      : {1'b0, a} + {1'b0, b};
```

Inside the concatenation, `a << 1` is 8 bits wide. The shifted-out bit lands
nowhere. The truncated sum is still the correct 8-bit sum, which is why no
`result` check can ever catch this. And `carry_out` is 0 forever on that path.
The "optimization" was reviewed, and it reads fine.

> **Check yourself.** Of the two ways to miss a bug, name which one step 0's
> six vectors ran into, and which one a checker watching `sum` alone runs into.

---

## Step 2 — measure controllability and observability

Before you run this, guess how many of all 65,536 input pairs this bug
corrupts. Write your number down. Then run:

```bash
just demo 01 s1 2
```

It takes about eight seconds wall-clock, roughly 2.5 s of it the test loop.
16 input bits is the last time exhaustive driving will be an option this
semester.

**You should see:**

```
  input pairs driven          : 65536  (exhaustive: 8+8 input bits)
  pairs where the DUT is wrong: 128   (128 of 128 on the a == b diagonal; first at a=0x80 b=0x80)
  observed at sum             : 0
  observed at carry_out       : 128

  controllability: 1 pair in 512 activates the bug -- a uniform random test needs ~355 vectors for a coin-flip chance of reaching it once
  observability:  the bug was activated 128 times; a checker watching only sum saw 0 of them
```

**What it means.** These are the two words from the core block, now measured.
Controllability: the buggy condition is 1 pair in 512. Six hand vectors had no
realistic shot. Even uniform random needs ~355 vectors for a coin flip at
reaching it once. Observability: the same stimulus was driven twice past two
probes. At `sum` the bug does not exist. At `carry_out` it is everywhere.
Where you look decides what you can know.

> **Check yourself.** Write down three stimulus sets. Predict which of them
> could observe this bug, and say why the others never can.

---

## If it breaks

| Symptom | Cause | Fix |
|---|---|---|
| Step 1 passes | the `(0x90, 0x90)` vector was dropped, or someone repaired `addc.sv` | the demo has no point with correct RTL — restore the `(a == b) ? {1'b0, a << 1}` line |
| Step 2 asserts "mismatch pattern moved" | `addc.sv` edited | same — restore from the repo |
| `iverilog: command not found` | course env not active | `source /opt/course/cocotb-env/bin/activate` |
| `make` exits 0 although the banner says FAIL | cocotb 1.9 does not propagate test failure to the exit code | read the `TESTS= PASS= FAIL=` banner, not `$?` |
| Strange rebuild errors after switching simulators | stale `sim_build/` | `rm -rf sim_build` in the demo dir |
