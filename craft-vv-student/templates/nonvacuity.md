# Non-vacuity evidence — <DUT> · <your name>

<!-- HW7, deliverable 2. Copy to code/tb/fifo_sva/ as nonvacuity.md.
     Delete every comment block before you submit. -->

> An assertion whose antecedent never fired did not pass. It was never asked.
> `assert property (@(posedge clk) never_true |=> anything)` holds forever and
> guarantees nothing. This file is the evidence that each of your properties was
> actually put to the question — and a property with no evidence here earns no
> credit, however green the run.

## 1. Per-property evidence

One row per property in `dut/fifo_sva.sv`. Fill in **all** of it: a hit count of
zero is a finding, not an omission — it means the corner is unreached, and that
belongs in section 3 rather than being quietly deleted.

<!-- Evidence comes from either (a) a `cover property` beside each assertion,
     reported hit, or (b) a per-corner counter in the testbench asserted
     nonzero at end-of-test. Say which you used per row. -->

| # | Property | The bug it catches | Antecedent | Evidence kind | Hits | Non-vacuous? |
|---|----------|--------------------|------------|---------------|-----:|--------------|
| 1 | no overflow | | | cover / counter | | yes / no |
| 2 | no underflow | | | | | |
| 3 | `full` consistency | | | | | |
| 4 | `empty` consistency | | | | | |
| 5 | `count <= DEPTH` | | | | | |
| 6 | FWFT head stability | | | | | |
| 7 | single-step count delta (write) | | | | | |
| 8 | single-step count delta (read) | | | | | |
| 9 | <the ninth> | | | | | |
| 10 | <your own property — grad / optional> | | | | | |

**Raw evidence:**

```text
<paste the cover report or the end-of-test counter dump — trimmed to the
 relevant lines is fine, but do not paraphrase it>
```

## 2. Corner coverage

The stimulus must reach every corner, not just run without failing.

| Corner | Driven? | Times reached | Which properties it arms |
|--------|---------|--------------:|--------------------------|
| Fill to full, then over-write | yes / no | | |
| Drain to empty, then over-read | | | |
| Hold with no read while non-empty | | | |
| Simultaneous read + write | | | |
| Simultaneous read + write across a pointer wrap | | | |
| Seeded random interleaving (breadth) | | | |

**Seed(s) used:**

## 3. Antecedents that never fired

<!-- If every row above is nonzero, say so explicitly and delete the table.
     If any is zero, this is the most important section in the file: an
     unreached antecedent is a reachability gap, and naming it honestly is
     worth more than hiding it. -->

| Property | Why the antecedent never fired | Unreachable, or just undriven? | What would reach it |
|----------|--------------------------------|--------------------------------|---------------------|
|          |                                | unreachable / undriven         |                     |

## 4. What the bound contract does not watch

The SVA proves the **control** contract. It does not watch the bytes.

**What the scoreboard covers that no assertion does:**

<!-- The golden-model scoreboard (models.fifo_model.FifoModel) predicts and
     checks count / full / empty / head every cycle. That is what catches a
     dropped data bit or an off-by-one rd_data — corruption the control
     assertions cannot see. Name a specific bug in each category. -->

| Bug | Caught by | Why the other mechanism misses it |
|-----|-----------|-----------------------------------|
| <a control bug> | assertion #__ | |
| <a data bug> | scoreboard | |

**Still watched by neither:**

---

- [ ] Every property in `dut/fifo_sva.sv` has a row in section 1.
- [ ] Every row carries a hit count from a real run, not an expectation.
- [ ] Any zero-hit antecedent appears in section 3 rather than being dropped.
- [ ] On clean RTL, every assertion holds.
