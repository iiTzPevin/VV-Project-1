# Week 13 · Session 1 — the survivor-analysis clinic

This session is a clinic. You work through it in class rather than watch it.
Here is what happens, what to bring, what you will be asked, and what you can
work on your own afterwards.

**What it shows.** A survivor you have attributed — first broken link named,
exposing condition derived, disposition argued — is worth more than a slightly
larger `found/total` carrying no analysis. The analysis is what M4's sign-off
is built from.

## What to bring

**A fresh assertions-only released run.** This was announced in Week 12. You
silence the scoreboard so the assertions are the only observers, then score it
with the CtM-12 invocation, from `code/`:

```bash
python -m craft_mutate.mutate --tb capstone/riscv \
    --pool capstone/riscv/mutants_released.yaml --dut-dir capstone/riscv --sim icarus
```

Bring the survivor list that run produces. Your milestone contract is
`weeks/week13/week13-hw.tex` (M3, 25% of the capstone). The session plan is
`weeks/week13/week13.tex`.

The clinic runs on the released RV32I pool for everyone, whatever your track.
The method is the deliverable, exactly as in Week 11's worked read. Two files
stay open the whole session: `code/capstone/riscv/mutants_released.yaml` and
`code/capstone/riscv/rv32i_core.sv`, side by side.

## What happens

1. One SURVIVED row, read three ways.
2. The find chain, and how to name its first broken link.
3. The anatomy of a survivor row, which is the table you build this week.
4. A worked derivation of an exposing condition, on `jal_link_wrong`.
5. The three legal dispositions, and the grader's test for "accept".
6. Why `found/total` is a sample, and what it does not generalize to.
7. You work `load_writeback_addr`, then your own survivors.

## One row, three readings

Here is the row, sitting under a green CI badge:

```text
load_writeback_addr --- SURVIVED     (assertions-only released run)
```

What does that row *mean*? There are three readings, and only three:

- (a) the stimulus never made the fault matter,
- (b) the fault mattered and nothing was watching,
- (c) the exposing case cannot legally occur.

The three readings demand three different deliverables by Sunday: a
constraint, a check, or a written argument.

Every homework since Week 5 carried the survivor and residual-risk rubric row
as a paragraph. M3 promotes it to the deliverable itself. Every surviving
mutant gets a row, an attribution, and a disposition.

> **Check yourself.** Pick one survivor from your own run. Say which of the
> three readings you believe, and what you would have to show to prove it.

## The find chain, and its first broken link

*Found* requires all four links:

```text
reach  ->  corrupt  ->  propagate  ->  compare
```

*Reach:* stimulus activates the mutated logic in the state that matters.
*Corrupt:* mutant and clean design now differ locally. *Propagate:* the
difference survives to an output somebody checks. *Compare:* a check fires.

A survivor is a break in that chain. Your analysis names the **first** broken
link. A **reachability** gap ends at *reach*. An **observability** gap gets
there and dies unseen.

This is Week 1's controllability and observability, at sign-off stakes. Under
assertions-only observation, observability has a familiar alias: **vacuity**.
The case fired, and no assertion was watching that case.

## Anatomy of a survivor row

This is the table you build this week, one row per assertions-only survivor:

| id | what it breaks | reachable? (evidence) | observable? (evidence) | first broken link | disposition |
|----|----------------|-----------------------|------------------------|-------------------|-------------|

**House rule.** Every cell cites evidence a grader can rerun: a coverage bin, a
cover count, a log line. "We believe" is not a cell value. The *reachable?*
cell wants the bin or cover count proving the case fired. The *observable?*
cell wants the specific check that would see the difference.

## Worked example — derive an exposing condition for `jal_link_wrong`

Read the diff first, verbatim from `code/capstone/riscv/mutants_released.yaml`:

```yaml
  - id: jal_link_wrong
    desc: "JAL writes the ALU result instead of the return address (pc+4)"
    find: "2'b10:   wb_data = pc_plus4;"
    replace: "2'b10:   wb_data = alu_result;"
```

Now chase it through `rv32i_core.sv`, three stops:

1. *Who selects that arm?* The writeback mux case `2'b10` is selected only
   when `wb_sel == 2'b10`, and the decoder sets that only in the `OP_JAL`
   arm — so **every `jal` reaches it**. Reachability is never this
   survivor's story.
2. *What value arrives instead?* For `jal` the decoder leaves the defaults
   `alu_src = 0` and `ALU_ADD`, so `alu_result = rs1_val + rs2_val`. And in
   a J-type instruction, `instr[19:15]` and `instr[24:20]` are *immediate
   bits* — the link register receives the sum of two registers indexed by
   slices of the jump offset.
3. *Why does every test pass?* Control flow is untouched:

   ```verilog
   assign pc_next   = (jump | beq_taken) ? pc_target : pc_plus4;
   ```

   `pc_next` never reads `wb_data`, so every taken/skip check passes.

**The exposing predicate:** `rd != x0`, that sum `!= pc+4`, and the link value
*reaching a check*. The fix here is not stimulus. Every `jal` already reaches
the fault. The fix is an **observer**.

`code/capstone/riscv/SPEC.md` lists "`jal` link register equals `pc + 4`" under
*properties worth proving*. As an assertion it goes to `sby`, and a proof
retires its vacuity question for good. That is the whole M3 arc in one mutant:
survivor, then missing observer, then assertion, then proof.

## Residual risk, or a hole

The disposition column has three legal values:

1. **Fix stimulus** — ends in a conversion: rerun, report `found` before → after.
2. **Fix a check** — same contract: before → after, in `FINDINGS.md`.
3. **Accept** — legal only with the exposing condition stated *and* an
   argument nobody can collapse: the condition is unreachable in-spec (best:
   an `sby` cover verdict; good: an argument from the spec's own
   constraints), or reachable but outside the scope the vplan declared. In
   that case the risk is priced: the field failure it corresponds to, why it
   is out of scope, who signed.

"We ran out of time" is an honest status. File it as an **open hole with an
owner**. Never dress it as a waiver.

**The grader's test for an accept row:** read the argument, then try to name a
legal stimulus that hits the condition. If one exists, the row was a hole
wearing a waiver.

> **Check yourself.** Run that test on your own best accept row. Try hard to
> break it. It is cheaper to fail here than in the M4 report.

## `found/total` is a sample

The pool is a finite draw of single-line edits from a fault model. Your score
is a sensitivity measurement against that draw. Generalizing from it takes two
steps, and they are different kinds of step:

- **Sample → model** is statistical. The hidden pool is a larger draw from the
  same model, so a suite tuned to the released eight can still land below the
  90% full-credit line on the hidden pool.
- **Model → bugs** is an *argument*, not a statistic. Sensitivity to small
  faults is evidence about compound ones, and the argument fails exactly where
  a fault is designed to sit outside the sampled distribution.

A Trojan triggered by one key in 2^32 is, by construction, the draw the model
never makes. That is why Track C's verdict cannot rest on `found/total`, and
why a 100%-found report still owes a residual-risk section. We say *found*,
never "killed."

## What you will be asked to work

First, this survivor, from `code/capstone/riscv/mutants_released.yaml`:

```yaml
  - id: load_writeback_addr
    desc: "LW writes back the effective address instead of the loaded word"
    find: "2'b01:   wb_data = dmem_rdata;"
    replace: "2'b01:   wb_data = alu_result;"
```

You answer in sequence, out loud, against the chain:

1. **Reachable?** Yes — every `lw` selects the mutated arm. Name the bin
   proving your suite retires loads.
2. **Corrupt value?** The effective address — the same number driving
   `dmem_addr` (in the RTL: `assign dmem_addr  = alu_result;`).
3. **Exposing predicate?** A load whose loaded word differs from its
   address, `rd != x0`, the loaded register reaching a check.
4. **Why does a green suite miss it?** Address-as-data initialization: a
   program that stores each word's own address as its content makes the two
   equal — invisible by construction.
5. **Disposition:** observability hole. Fix the data patterns or the check,
   convert, and show before → after.

Then you open your own assertions-only survivors and start your table. Track
B's contention family (`arb_last_stuck`, `rr_preference_invert`) and Track C's
parked-`data_in` leak case (`data_leak_when_locked`) follow the same script.

Session 2's studio reviews these tables at your bench, plus vacuity
spot-checks and verdict wording. Bring the table started, not blank.

## If you get stuck

| Problem | Why it happens | Fix |
|---|---|---|
| You arrive without the assertions-only run | The prerequisite got lost under M3 work | Start it at the door. 8 mutants under Icarus finishes before the working block, so your table starts on live numbers |
| Your assertions-only run reports zero survivors | Either a suite ahead of schedule or an assertion file that never bound | Check the bind before you believe either. Everything survives, or nothing was watching at all. Absent evidence is not passing evidence |
| Every survivor starts to look like vacuity | Vacuity is fresh, so it fits everything | The data-path family is **checker-class** under assertions-only observation. No assertion of any shape sees `add_becomes_sub` or `load_writeback_addr`, which is Week 7's structural lesson. Full credit attributes it as such |
| Your accept row does not survive its own argument | The argument sounds airtight in your own voice | Name a legal stimulus that hits the condition. `and_becomes_or` is the standing example: any `and` with unequal operands exposes it, because equal operands make `&` and `\|` agree |
| You plan to grind to 100% and skip the analysis | A number feels safer than an argument | Read the grading rows. The survivor analysis (25%) and verdict (15%) together outweigh the hidden-pool number (25%), and 100% found still owes the sample argument |
| Track C: you want to know whether your variant is the clean one | The verdict would be free | Nobody will confirm or deny. The variant map stays out of the class, because a nod converts a proof exercise into an answer-key lookup |
| The RTL chase loses you | Three files are open at once | Pin the three lines that matter: the `OP_JAL` decoder arm (`wb_sel = 2'b10`), the writeback mux, and the `pc_next` assign. Everything else is scenery |
