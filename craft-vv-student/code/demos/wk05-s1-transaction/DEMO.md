# Week 5 · Session 1 — randomizing bought one mutant, checking bought four

You watched this in class. Here it is again so you can run it yourself.

**What it shows.** Swapping hand vectors for a randomized transaction moves
found/total by exactly one mutant. Then the same stimulus, with three more
things checked, moves it by four more. Where you go matters less than what you
look at when you get there.

Run everything from `code/`.

| Step | File | What you should get |
|------|------|---------------------|
| 0 | `step0_hand.py` | **2/8** |
| 1 | `step1_txn.py` | **3/8** |
| 2 | `step2_scoreboard.py` | **7/8** |
| — | seed sweep | `expected/seed-lottery.txt`, `full` reached 0–39 cycles |

Each step is one command. Here is step 0, in both forms:

```bash
just demo 05 s1 0        # or:  make -C demos/wk05-s1-transaction STEP=0
```

Every number below was measured on `dut/fifo.sv` with Icarus, `DEMO_SEED=5`,
against `tb/fifo_crv/mutants_released.yaml` (8 mutants). Captured output for
each step is in `expected/`. If your run differs, the DUT or the pool moved.

---

## Step 0 — where Week 4 left us

```bash
just demo 05 s1 0
```

This is your homework from last week, and it passes.

**Look at the histogram.** Occupancy tops out at 4 on an 8-deep FIFO. `empty`
is visited once. `full` is never visited.

**Predict before you read on.** What fraction of the mutant pool can this
possibly find? Write a number down. The answer is **2/8**. The six survivors
are `full_offbyone`, `ignore_full`, `ignore_empty`, `rd_data_wrptr`,
`mem_corrupt`, `wrptr_wrap_early`.

> **Check yourself.** Take three of those six survivors. For each one, name
> the occupancy this stimulus never visits that the mutant needs.

---

## Step 1 — the transaction

Type it yourself. `@vsc.randobj` is new, so build the fields one at a time and
name what each one is for. The whole change is this. The eight-element list
becomes an object you draw from 200 times.

```bash
just demo 05 s1 1
```

**You should see:** green, a wider histogram — and **3/8**.

**What it means.** Most people expect randomization to be transformative. It
moved the score by one mutant. Sit in that for a second before you read step 2.
Do not rescue it.

**If your instinct is "run it longer",** run it longer. `for _ in range(2000)`.
The score does not move, because the surviving mutants are not a stimulus
problem.

> **Check yourself.** You just widened the histogram and gained one mutant.
> Write down, in one sentence, why more cycles cannot buy a second one.

---

## Step 2 — what you check, not what you drive

Answer this before you run anything. `rd_data_wrptr` corrupts the read pointer
so `rd_data` returns the wrong entry. How many cycles of stimulus does it take
to find that?

No amount of stimulus finds it. Nothing in the testbench ever looks at
`rd_data`. Write `check()` yourself:

```python
def check(dut, model):
    assert int(dut.count.value) == model.count
    assert bool(dut.full.value)  == model.full
    assert bool(dut.empty.value) == model.empty
    if not model.empty:                # FWFT: head valid only when !empty
        assert int(dut.rd_data.value) == model.head
```

```bash
just demo 05 s1 2
```

**You should see: 7/8.** Same stimulus, four more mutants.

**What it means.** Week 1 called these controllability and observability. Step
1 was controllability with no observability. You went to more places and looked
at nothing. A constrained-random environment with a weak scoreboard is an
expensive way to not find bugs.

> **Check yourself.** Cover the four asserts. For each of the four mutants
> step 2 gained, name the assert that catches it.

---

## The bridge into Session 2

One mutant still survives: `ignore_full` — writes accepted while the FIFO is
full. With this seed, `full` is never reached, so the bug is never exercised.

Open `expected/seed-lottery.txt`:

```
  seed   empty-cycles   full-cycles   both boundaries?
     4              4            26   yes
     5              9             0   NO
     8              7            39   yes
    10             17             0   NO
```

Whether this regression would have caught an overflow bug was decided by a
number nobody chose on purpose. Session 2 takes that back.

> **Check yourself.** Your suite scores 7/8 on seed 5. Predict its score on
> seed 8, and say which line of the table you used.

---

## If it breaks

| Symptom | Cause | Fix |
|---|---|---|
| `ModuleNotFoundError: models.fifo_model` | `PYTHONPATH` not picking up `code/lib` | Run from `code/`, or `export PYTHONPATH=$PWD/lib` |
| Histogram differs from `expected/` | seed not pinned | `DEMO_SEED=5` is the default; check nothing exported it |
| `iverilog: command not found` | wrong shell | `source /opt/course/cocotb-env/bin/activate` |
| Step 2 fails on clean RTL | typo in `check()` — usually `model.head` when empty | The `if not model.empty` guard is load-bearing; FWFT `rd_data` is undefined when empty |
