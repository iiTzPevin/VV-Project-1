# Week 6 · Session 2 — the hole is a constraint, the number is a model

You watched this in class. Here it is again so you can run it yourself.

**What it shows.** The coverage hole was created by a constraint and closed by
deleting it. found/total moved 6/8 to 8/8 for a reason you can point at. Then
the same stimulus, measured against a model with no cross, reads 100% and
leaves the same two mutants alive.

Run everything from `code/`.

| Step | File | What you should get |
|------|------|---------------------|
| 0 | `step0_hole.py` | cross **66.7%**, trace flat, **6/8** |
| 1 | `step1_close.py` | cross **100.0%**, **8/8** |
| 2 | `step2_correlate.py` | 66.7 → 100.0 · 6/8 → 8/8 |
| 3 | `step3_weak_model.py` | occ **100%** · op **100%**, **6/8** |

Each step is one command. Here is step 0, in both forms:

```bash
just demo 06 s2 0        # or:  make -C demos/wk06-s2-closure STEP=0
```

Coverage numbers measured on `dut/fifo.sv` with Verilator 5.020 (`SIM=icarus`
prints the same numbers); found/total measured with the mutation harness under
Icarus against `tb/fifo_cov/mutants_released.yaml` (8 mutants), with the
commands shown in step 2 (~55 s each). `DEMO_SEED=5`, 250 cycles per step.
Captured output in `expected/`.

---

## Step 0 — the plateau, and how to read one

```bash
just demo 06 s2 0
```

**You should see:**

```
  top.occ_x_op   8/12 bins hit    66.7%
  empty bins (4): (empty,read)  (empty,simul)  (full,write)  (full,simul)

  cycle        50    100    150    200    250
  cross%     66.7   66.7   66.7   66.7   66.7
```

Flat from the first sample. What would another thousand cycles buy? Another
seed? Nothing, and that is measured: `DEMO_SEED=7` reads the same 66.7%.

**What it means.** A plateau is ambiguous on its own. It could be closure, bad
luck, or a bin the constraints cannot reach. The curve cannot tell you which.
**Reading the bin can.** Put the four empty cells next to the guard from
Tuesday:

```python
with vsc.implies(self.count == self.depth):
    self.wr_en == 0                   # a write while full is wasted
with vsc.implies(self.count == 0):
    self.rd_en == 0                   # nothing to read -- don't ask
```

Every empty cell needs an enable that `c_tidy` forces to zero in exactly that
occupancy state. The hole is not bad luck. It is a constraint with a comment
that says it is a favor.

> **Check yourself.** Take the four empty cells one at a time. For each, name
> the line of `c_tidy` that makes it unreachable.

---

## Step 1 — close it with a constraint change

The directed fix will occur to you first. Give it its due:

```python
# the tempting fix: fill the FIFO, then poke wr_en by hand for two cycles
```

It would light `(full, write)`, one cell of four. It patches the number instead
of the stimulus, and it leaves a sequence that has to be maintained forever. A
directed test bolted on to hit one bin is a smell. The report said four cells.
Step 0's diagnosis said one constraint forces all four off. So fix the
constraint. **The edit is a deletion.** `c_tidy` goes, and nothing is added:

```python
    # c_tidy deleted. It forced wr_en low at full and rd_en low at empty --
    # which is a sentence that names all four empty bins of step 0.
```

**Was the guard protecting something?** No. The DUT gates both enables itself,
the spec says driving them is legal, and the scoreboard checks the outcome
either way. The guard bought no correctness, only unreachability.

```bash
just demo 06 s2 1
```

**You should see:**

```
  occ \ op      idle   write    read   simul
  empty          10       1      28      11
  partial        43      43      42      33
  full            8      18       1      12
  cross top.occ_x_op: 12/12 bins hit = 100.0%   ('-' = empty bin)

  cycle        50    100    150    200    250
  cross%     91.7  100.0  100.0  100.0  100.0
```

The convergence row steps up and closes. The Week 5 shaping already carried a
10% enable overlap, so once the guards are gone the boundary cells fill on
their own. Look at the assert at the bottom of the file. Closure is a checked
claim now. Reopen the hole and the run fails instead of shipping. (Measured
across seeds 1–10 at this budget: worst closure at cycle 201.)

**The score is 8/8.** Now be suspicious of the sentence "closing coverage found
the bugs". That claim is what step 2 pins down and step 3 breaks.

> **Check yourself.** You deleted a constraint and the score rose. Write the
> one sentence that says why, and make sure it names a stimulus, not a check.

---

## Step 2 — correlate: coverage vs found/total

```bash
just demo 06 s2 2
```

Both environments run back to back in one process. Same seed, same budget, same
scoreboard. The only diff is `c_tidy`:

```
  env                          cross    found/total (harness)
  ---------------------------  ------   ---------------------
  before: guarded (step 0)      66.7%   score step 0
  after:  c_tidy deleted       100.0%   score step 1
```

Fill in the third column yourself. The harness scores a demo step directly, at
about 55 s each:

```bash
STEP=0 python3 -m craft_mutate.mutate --tb demos/wk06-s2-closure \
    --dut dut/fifo.sv --pool tb/fifo_cov/mutants_released.yaml --sim icarus
STEP=1 python3 -m craft_mutate.mutate --tb demos/wk06-s2-closure \
    --dut dut/fifo.sv --pool tb/fifo_cov/mutants_released.yaml --sim icarus
```

**You should get:**

| env | cross | found/total | survivors |
|---|---|---|---|
| step 0 — guarded | 66.7% | **6/8** | `ignore_full`, `ignore_empty` |
| step 1 — `c_tidy` deleted | 100.0% | **8/8** | — |

**What it means.** The two numbers moved together, and not by coincidence. The
empty bins were the only stimulus that reaches those two faults. Closing
coverage raised found/total because the hole was a *reachability* hole. That is
the correlation HW6 asks you to report on the hidden pool. Now the warning. It
is a correlation you must argue, not a law you may assume, and the
counterexample is one step away.

> **Check yourself.** Before you run step 3, write down what you think would
> happen to found/total if coverage closed and the stimulus did not change.

---

## Step 3 — 100% of a weak model

Same guarded stimulus as step 0. One change: the model loses its cross. This is
the shape you will most often be handed, and the shape CtM-06 predicts an AI
will hand you.

```bash
just demo 06 s2 3
```

**You should see:**

```
  top.occ        3/3  bins hit   100.0%
  top.op         4/4  bins hit   100.0%
coverage model closed: every bin in the model was hit
```

The run passes, and two asserts certify closure. Scored against the same pool:
**6/8**, with `ignore_full` and `ignore_empty` alive. Nothing diverged.
Coverage climbed to 100% while finds sat still, because this model contains no
bin the missing stimulus would have left empty.

**What it means.** The number certifies the *model*, never the design. Same
stimulus, same live bugs as step 0. One report admitted it at 66.7%, the other
said done. That gap is the whole case for `closure.md`. Not "the number is 100"
but "here is what my model can see, here is what it cannot, and why the
difference is acceptable." Here is one blind spot to reuse in HW6. No occupancy
or operation bin sees a one-cycle glitch on `full` that leaves the end state
correct, and no coverpoint in *any* of today's models does. Holding a property
on the exact cycle is next week's tool.

> **Check yourself.** Step 1 and step 3 both report a closed model. Write the
> two sentences you would put in `closure.md` to tell an honest reader which
> one to trust.

---

## If it breaks

| Symptom | Cause | Fix |
|---|---|---|
| The closure assert (step 1) fires | seed outside 1–10 with late closure | budget is 250 cycles; worst measured closure (seeds 1–10) is cycle 201 — rerun with `DEMO_SEED` in 1..10 |
| Flat trace missing in step 0 / reads 100% | guards missing from step 0's `FifoTxn` | `c_tidy` must be present in step 0; the plateau is the exhibit |
| Harness: "testbench does not pass on clean RTL" | wrong dir, or `STEP=` prefix dropped so it scored a different step | the `STEP=N` must be on the same command line, run from `code/` |
| Both harness runs print the same score | pool or DUT moved, or stale `sim_build` | `rm -rf demos/wk06-s2-closure/sim_build`; confirm the pool still lists 8 mutants |
| `%Error ... WIDTHEXPAND` at compile | Verilator makes fifo.sv's width compare fatal | the Makefile waives it (verilator only); restore the guard rather than editing the DUT |
| First step takes ~15 s | cold Verilator build | warm `sim_build` with one run first; warm steps ≈ 6 s |
