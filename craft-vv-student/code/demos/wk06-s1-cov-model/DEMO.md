# Week 6 · Session 1 — the coverage model: two coverpoints and the cross

You watched this in class. Here it is again so you can run it yourself.

**What it shows.** An environment can be green on the scoreboard, green on the
histogram, and green on both single coverpoints, and still never once have
written while full. Only the cross can say so. Coverage bounds what you know,
and the bound is the model.

Run everything from `code/`.

| Step | File | What you should get |
|------|------|---------------------|
| 0 | `step0_blind.py` | green, **6/8** |
| 1 | `step1_coverpoints.py` | occ **100%** · op **100%**, 6/8 |
| 2 | `step2_cross.py` | cross **66.7%**, 6/8 |

Each step is one command. Here is step 0, in both forms:

```bash
just demo 06 s1 0        # or:  make -C demos/wk06-s1-cov-model STEP=0
```

Coverage numbers measured on `dut/fifo.sv` with Verilator 5.020 (the Week 6
coverage flow; `SIM=icarus` prints the same numbers — the stream is seeded
Python, so it does not depend on the simulator). found/total measured with the
mutation harness under Icarus against `tb/fifo_cov/mutants_released.yaml`
(8 mutants). `DEMO_SEED=5`, 250 cycles per step. Captured output in
`expected/`. If your numbers differ, the DUT or the pool moved.

---

## Step 0 — the environment you inherit

```bash
just demo 06 s1 0
```

Week 5's shaped environment scored 8/8. This is that environment after a
weekend of tidying. Here are the two added guards. Accept each on its merits.
Both read like hygiene:

```python
with vsc.implies(self.count == self.depth):
    self.wr_en == 0                   # a write while full is wasted
with vsc.implies(self.count == 0):
    self.rd_en == 0                   # nothing to read -- don't ask
```

**Look at the histogram.** Both boundaries parked, with better residency than
Week 5 asked for:

```
  boundaries reached: 2/2   (empty=68 cycles, full=58 cycles)
```

By last week's standard this environment is healthy. **Then the score:** 6/8.
The survivors are `ignore_full` and `ignore_empty`, the two mutants Week 5
spent a session pinning down. They are back, the run is green, and the
histogram looks better than ever.

Which line of output could have told you? There isn't one. That absent
instrument is the session.

> **Check yourself.** The histogram says `full` was reached for 58 cycles. Say
> why that is not the same claim as "a write happened while full", and name the
> guard that makes the difference.

---

## Step 1 — two coverpoints from the vplan

Type the model yourself. Both axes come straight off the Week 2 plan: occupancy
states, and the operations the interface admits.

```python
@CoverPoint("top.occ", xf=lambda count, wr, rd: occ_bin(count), bins=OCC_BINS)
@CoverPoint("top.op", xf=lambda count, wr, rd: op_bin(wr, rd), bins=OP_BINS)
def sample_coverage(count, wr, rd):
    """One sample per cycle: pre-edge occupancy x requested operation."""
    pass
```

Spend a breath on the call site. The sampling discipline is half the content:

```python
sample_coverage(model.count, wr, rd)      # sample BEFORE the edge
model.step(wr, data, rd)
```

Record the state the operation was **issued in**, not the state it produced.
Swap the order and the cross lies in both directions. A write at count 7
records as `(full, write)`, and a fault-revealing write at full can vanish.

**Predict before you run.** Will these two show you what the histogram missed?

```bash
just demo 06 s1 1
```

**You should see:**

```
  top.occ        3/3  bins hit   100.0%
  top.op         4/4  bins hit   100.0%
```

Green. Every occupancy state visited, every operation issued. Both are true,
and the question "did a write ever meet full?" is answered by neither. Plenty
of shipped environments stop at this screen. CtM-06 has you measure what that
habit costs.

> **Check yourself.** Both coverpoints read 100%. Write down the cross
> percentage you expect before you open step 2, and keep the number.

---

## Step 2 — the cross

One added line:

```python
@CoverCross("top.occ_x_op", items=["top.occ", "top.op"])   # <- the added line
```

```bash
just demo 06 s1 2
```

**You should see:**

```
  top.occ_x_op   8/12 bins hit    66.7%

  occ \ op      idle   write    read   simul
  empty          63       5       -       -
  partial        31      35      35      23
  full           53       -       5       -
  empty bins (4): (empty,read)  (empty,simul)  (full,write)  (full,simul)
```

**Walk the grid.** Every row has hits and every column has hits. That is why
both coverpoints read 100%. Four cells are dark, and they are not four random
cells. They are the four boundary interactions. Two of them are addresses.
`(full, write)` is the only stimulus that can expose `ignore_full`, and
`(empty, read)` the only one for `ignore_empty`. The 6/8 now has a mechanism
you can point at on screen.

**The judgment call: illegal versus ignore.** On this FIFO the RTL gates both
enables, so driving a write at full is legal at the pins and *must* be
covered. It is how the gating bug gets found. On an interface where the same
stimulus corrupts state, you would declare the same cell an `illegal` bin
instead. Same cell, opposite verdict, and you defend yours in the coverage
review.

**What it means.** "Coverage bounds your ignorance" stopped being a slogan. The
bound is the model, and the model got sharper by one decorator. Session 2
closes these four cells without writing a single directed test, and found/total
moves when it does.

> **Check yourself.** Propose the cross that matters: `full` × `write`
> sharpened, and `empty` × `read`. For each one, name the bug it would reveal.

---

## If it breaks

| Symptom | Cause | Fix |
|---|---|---|
| `%Error ... WIDTHEXPAND` at compile | Verilator makes fifo.sv's count-vs-DEPTH width compare fatal | the Makefile waives it (`-Wno-WIDTHEXPAND`, verilator only) — restore the guard rather than editing `dut/fifo.sv` |
| `ModuleNotFoundError: models.fifo_model` | `PYTHONPATH` missing `code/lib` | run via make/just from `code/` — the Makefile exports it |
| Grid or histogram differs from `expected/` | seed not pinned | `DEMO_SEED=5` is the default; check nothing exported another |
| Coverpoints report 0% | `sample_coverage` dropped, or moved after `model.step` | the sample line sits before `model.step` — pre-edge state, requested enables |
| First step takes ~15 s | cold Verilator build | run any step once to warm `sim_build`; warm steps ≈ 6 s |
