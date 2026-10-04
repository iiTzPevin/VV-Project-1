# Coverage closure — <DUT> · <your name>

<!-- HW6, deliverable 3. Copy to your tb/ directory as closure.md.
     Delete every comment block before you submit. -->

> Coverage is a measure of what you *looked at*, never of what is *correct*.
> A closed model with a weak checker reports 100% and proves nothing. This file
> is the argument that your number means something — and the honest list of
> what it still cannot mean.

## 1. The number

| | |
|---|---|
| Coverpoints closed | __ / __ |
| Cross `top.occ_x_op` closed | __ / __ bins |
| Target declared in my vplan | __% |
| Reached | __% |
| Vectors to closure | |
| Vectors soaked past closure | |

**How the report was produced:**

```bash
# coverage_db.report_coverage(...) — also exports coverage.yml
```

## 2. The convergence argument

<!-- Not "I ran it until it closed." Why does the curve flatten where it does?
     Which bins were cheap, which were rare, and what did you change in the
     stimulus to reach the rare ones? -->

**Shape of the curve:** <where it climbed fast, where it stalled>

**The last bins to close, and what it took:**

| Bin | Why it was rare | What I changed to hit it |
|-----|-----------------|--------------------------|
|     |                 |                          |

**Why I stopped where I stopped:**

<!-- And why soaking past closure matters: a mutant whose corruption propagates
     late is only observable if the run continues after the bin is ticked. Say
     how far you soaked and what that bought. -->

## 3. Bin justification

Every `illegal` and `ignore` bin is a claim about the design. Each one needs an
authority — a line of `dut/specs/fifo.md`, or an argument you would defend.

| Bin | illegal / ignore | The claim | Authority (spec line, or the argument) |
|-----|------------------|-----------|----------------------------------------|
|     |                  |           |                                        |

**Corner bins that are legal and must be covered, not excluded:**

<!-- Read the spec carefully. Write-while-full is DROPPED and read-while-empty
     is IGNORED — both legal behaviors. So (full, write) and (empty, read) are
     corners you must COVER. Anything you moved to `ignore` that the spec
     actually permits is a hole you have hidden from yourself. -->

## 4. What the cross is aimed at

A cross earns its place only if the interaction is where a bug would hide.

**The bug `top.occ_x_op` is aimed at:**

**A bug it would *not* see, even fully closed:**

## 5. Coverage vs. correctness — the blind spots

<!-- The graded core of this file. Name what a closed model cannot establish
     about THIS design. Be specific enough that a reader could go write the
     check you are saying is missing. -->

My model is closed and my suite is green. That still establishes nothing about:

1. **<blind spot>** — <why the model cannot see it>
2. **<blind spot>** — <...>
3. **<blind spot>** — <...>

**Transients in particular:** <a one-cycle glitch whose end-state is correct
ticks no end-state bin and fails no end-state check — say whether your model
would see one, and if not, what would.>

## 6. Correlation with mutation

Cross-reference `FINDINGS.md`. The interesting case is divergence.

| | found / total |
|---|---|
| Before closing holes | |
| After closing holes | |

**Did closing holes raise the score?**

- If **yes** — which survivor did which bin catch?
- If **no** — you have found a mutant the coverage model cannot see. Name it,
  and say whether the gap is *reachability* (stimulus never creates the state)
  or *observability* (the corruption never reaches a checked output).

---

- [ ] Every `illegal` and `ignore` bin in section 3 cites an authority.
- [ ] Section 5 names blind spots of this design, not of coverage in general.
- [ ] The numbers here agree with `coverage.yml` and `FINDINGS.md`.
