# Week 2 · Session 2 — the plan predicts the score

You watched this in class. Here it is again so you can run it yourself.

**What it shows.** found/total follows the plan, not the effort. It is 1/8
with no plan, 5/8 with three rows, and 8/8 when the rows run out. At every
stage the survivors are exactly the rows nobody had written.

Run everything from `code/`.

| Step | File | What you should get |
|------|------|---------------------|
| 0 | `step0_no_plan.py` | **1/8** |
| 1 | `step1_traceable.py` | **5/8** |
| 2 | `step2_plan_complete.py` | **8/8** |

Each step is one command. Here is step 0, in both forms:

```bash
just demo 02 s2 0        # or:  make -C demos/wk02-s2-vplan STEP=0
```

All numbers were measured on `dut/alu.sv` with Icarus against
`tb/alu/mutants_released.yaml` (8 mutants), `DEMO_SEED=5`. A scoring run is
9 simulations, one baseline plus 8 mutants, and it took ~55 s here. Start it,
then keep reading. Captured step output is in `expected/`, and all three
scoring transcripts are in `expected/score-preview.txt`. Score a step in place
with:

```bash
STEP=1 PYTHONPATH=$PWD/lib python3 -m craft_mutate.mutate --tb demos/wk02-s2-vplan \
       --dut dut/alu.sv --pool tb/alu/mutants_released.yaml --sim icarus
```

---

## Step 0 — no plan, then the first row

```bash
just demo 02 s2 0
```

Green in two seconds. Now ask yourself the real question: green against what
standard? Start the scoring run with `STEP=0` in the command above and let it
grind.

**You should see:**

```
==== found/total = 1/8  =  12.5%  ====
surviving mutants: and2or, xor2and, slt_unsigned, drop_add_carry, zero_inverted, sll2srl, drop_add_overflow
```

**What it means.** One mutant. The instinct tested what was easy, not what
mattered.

Now open `vplan.md` and derive **VP-1** yourself, left to right. First the
requirement. That is Tuesday's R-ADD-OVF, already sharpened, so reuse it. That
reuse is the point of sharpening. Then the coverage points it implies: both
wrap boundaries, exactly at and one either side, equal operands, and the two
flag-split vectors. Then the test that will hold it. Then the risk sentence,
which answers *why would a bug here matter?* That one sentence is the risk
ranking, for free.

> **Check yourself.** Write VP-1's risk sentence in your own words. If you
> cannot say why a bug there would matter, the row is not ready.

---

## Step 1 — three rows, three traceable tests

Look at the trace annotation in `step1_traceable.py`. Every test opens with
the row it implements:

```python
@cocotb.test()
async def test_vp1_add_flags(dut):
    """traces: vplan.md VP-1 -- ADD result + overflow (signed) + carry (unsigned)"""
```

```bash
just demo 02 s2 1
```

Green, three tests. Read the link in both directions. Forward, every row names
its test. Backward, every test names its row. Orphans either way are the
finding. Then score it:

**You should see:**

```
==== found/total = 5/8  =  62.5%  ====
surviving mutants: and2or, xor2and, sll2srl
```

**What it means.** Put the survivor list next to `vplan.md`. `and2or` and
`xor2and` live in the logical-ops row, and `sll2srl` in the shifts row. Those
are the two rows the plan does not have. The harness did not discover a
weakness. The plan already said where the holes were. Coverage of a plan
bounds what you know. The plan's edges bound what you looked at.

> **Check yourself.** Cover the survivor list. From `vplan.md` alone, name the
> rows that are missing. Then uncover it and compare.

---

## Step 2 — the missing rows land

The missing features are the ones the survivor list points at: logical ops and
shifts. VP-4 and VP-5 are already drafted in `vplan.md`. Open
`step2_plan_complete.py` and look at the import:

```python
from step1_traceable import (          # rows VP-1..VP-3, byte for byte
    test_vp1_add_flags,
    test_vp2_slt_signed,
    test_vp3_zero_flag,
)
```

Growing a plan is additive. The old rows and their tests do not move.

```bash
just demo 02 s2 2
```

Five tests green. Score it:

**You should see:**

```
==== found/total = 8/8  =  100.0%  ====
```

**What it means.** Read that carefully. It is 8/8 against the *released
practice* pool, with a plan whose model is five rows deep. The number is a
preview, not a verdict. The graded pool is hidden and larger, and Week 2's
`gradext` is one long warning about confusing 100% of a model with
completeness of the model. HW2's habit starts now. Run your directed suite
against the released pool and report found/total in `FINDINGS.md`. We say
*found*, never "killed".

> **Check yourself.** Your plan is five rows deep and scores 100%. Name one
> thing about the ALU that no row covers, and decide whether that is a risk
> you are choosing to carry.

---

## If it breaks

| Symptom | Cause | Fix |
|---|---|---|
| `ERROR: testbench does not pass on clean RTL` | a live-edited expected value went wrong | The baseline is the guard: a broken testbench fails on every mutant and would score a perfect 8/8. Fix the test; the assert message names the vector |
| Score command runs step 0 regardless of STEP | `STEP=1` not in the command's environment | Prefix the variable on the same line: `STEP=1 PYTHONPATH=... python3 -m ...` |
| Step 2 reports TESTS=2 | the `from step1_traceable import ...` block was dropped | cocotb discovers imported tests; restore the import |
| `ModuleNotFoundError: demo_common` | test invoked outside make | Run via `make -C demos/wk02-s2-vplan STEP=N` from `code/` — the Makefile sets `PYTHONPATH` |
| Scoring feels slow on your machine | 9 sims per run (~55 s here) | Keep deriving the next row while it runs, or read `expected/score-preview.txt` |
