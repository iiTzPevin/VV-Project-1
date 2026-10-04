# Week 12 · Session 2 — standups, five CRV failures, and the M2 door

This session is a studio, not a lecture. You spend all 75 minutes on your own
environment. Here is what happens, what to bring, what you will be asked, and
what has to be true before you leave.

**What it shows.** On track for M2 means randomized *legal* stimulus running
under your M1 scoreboard, plus a coverage model whose axes cite the vplan. The
snapshot is graded on honesty, not on the percentage.

## What to bring

- Your environment, running, with the M1 scoreboard still checking.
- Your coverage model, however partial, with the vplan open beside it.
- One named blocker you can say in a sentence.
- Your next step before Sunday, already decided.

Dates on the board all session: **CtM-11 due Wednesday 23:59, M2 due Sunday
23:59, tagged `m2`.** The milestone contract is `weeks/week12/week12-hw.tex`
(M2, 20% of the capstone). The session plan is `weeks/week12/week12.tex`.

CtM-11 is due Wednesday. That is this week, not a next-week problem. Its
transcript can double as M2's required assistant task, so doing that work twice
is self-inflicted.

## What happens

1. A frame: what on-track looks like today.
2. Standups. Three minutes per team, hard-timed.
3. Five ways the CRV week dies, named before you rediscover them.
4. Studio. Your coverage model gets a five-minute review.
5. The exit check at the door, team by team.

## What you will be asked at standup

Three minutes, whole team standing, one speaker. The speaker changes this week.
The rotation was set in Week 11. The format does not change:

- **status** — what ran since last time.
- **one named blocker.**
- **next step before Sunday.**

Your blocker goes on the board as it lands. That list is the rotation order for
the studio block.

**Graduate teams:** your paper data-collection checkpoint (`paper-status.md`)
is standup material too. It gets five minutes of the studio rotation. The gate
this week is *data*. An experiment that has produced no file in the repo by
Sunday is the risk section's first line.

## What on-track looks like

M2 in one sentence, per the capstone packet: a constrained-random stimulus
environment and a functional-coverage model derived from the vplan, both
running, with an initial coverage report and a first `found/total` against the
released practice pool.

On-track today means three things:

1. Randomized *legal* stimulus driving the DUT under the M1 scoreboard. Legal
   per the *spec's* definition of legal.
2. A coverage model whose axes are traceable to vplan rows.
3. The released-pool harness run at least once end to end, from `code/`:

```bash
python -m craft_mutate.mutate --tb capstone/riscv \
    --pool capstone/riscv/mutants_released.yaml --dut-dir capstone/riscv --sim icarus
```

(`axi_subsystem` and `trojan` swap in the same way — the invocation is
printed in `code/capstone/README.md`.)

**Closure is not required today.** The snapshot is graded on honesty: what
closed, what did not, and what changes next. It is not graded on the number.
Chasing a percentage because a number feels like progress is this week's most
common failure. Closure is M4's gate.

## Five ways the CRV week dies on unfamiliar RTL

1. **Shaping that cancels.** Distribution weights placed under guards that do
   not gate them — the Week-5 lesson, with numbers: the code promised +0.65
   drift and the instrument measured **−0.01**
   (`code/demos/wk05-s2-constraints/DEMO.md`). Shape by hand — one uniform
   roll field plus plain implications — then *measure* the histogram instead
   of trusting the constraint text.
2. **No state feedback.** Randomizing blind instead of assigning DUT state
   into a non-random field before each `randomize()`. On Track B the
   occupancy your constraints need is only honestly visible through the bus
   status read — the status word at FIFO offset `0x4` (address `0x2004`),
   `{ .., count[3:0], full<<1, empty }` per the Track B spec, no side effect.
3. **The random walk.** Unshaped reads and writes cancel, so boundary states
   are reached a seed-decided amount. If a corner matters, bias toward it
   and prove residency with a histogram — Week 5's lottery table is the
   cautionary exhibit.
4. **Covering ports instead of behavior.** A model that samples module
   internals reads closed while the through-the-bus corner stays dark.
   Sample what a transaction-level observer sees; on Track B, FIFO
   boundaries count only when reached *through the bus*.
5. **The too-perfect score.** A broken testbench fails on *every* mutant and
   reports a perfect `found/total`. The harness's clean-RTL baseline line is
   what catches it — read the baseline before celebrating the number. The
   released floor is 8/8/7 by track, already held by the shipped smoke
   tests; a drop below it means the environment broke the baseline, not
   that the mutants got harder.

> **Check yourself.** Take failure 1 to your own constraints. Find one weight
> and name the guard above it. Then run the histogram and see whether the
> weight survived.

## What your coverage model will be asked

The studio rotation this week is a review, five minutes per team, hard cap.
Four questions, the same four at every bench:

1. Which vplan row or spec line does each axis cite?
2. Which bins demand something the stimulus does not already do?
3. Where are the crosses for the interaction rows?
4. Which corner is a proof obligation rather than a coverage target — and
   does the model say so?

Answer them crisply and you have done half of CtM-12 already. That packet asks
you to freeze review criteria for exactly this artifact.

**Question 4 has teeth, and they differ by track.** Track C's backdoor trigger
is one key in 2^32. Randomized keys will next to never present it, and the
honest model says so with near-miss key classes (low-half match, one bit off)
instead of reading closed while the security question goes unasked. Tracks A
and B carry the same shape. The privileged and locked corners from your M1
security rows need bins *now*. What stimulus cannot reach becomes M3's proof
obligation.

> **Check yourself.** Answer question 1 for every axis you have, out loud,
> before the review reaches you. An axis with no citation is the review's first
> finding.

## The door criterion

At the door, team by team: your randomized stream runs against the DUT with the
scoreboard checking, and a coverage report prints with nonzero hits on at least
one axis.

If you leave without it, you leave with a named blocker and a scheduled
office-hours slot. You do not leave in silence.

## If you get stuck

| Problem | Why it happens | Fix |
|---|---|---|
| You have no running environment (M1 debt) | Bring-up never finished | Take the fix-it table for the whole block. Milestones are graded individually, so M2 can still be strong |
| The harness fails on clean RTL | Your environment broke the baseline the smoke test held | That *is* failure (5), live. Read the baseline line first, and fix the testbench before anyone reads a score |
| Your `found/total` is below the 8/8/7 floor | Same cause, quieter | The floor is held by the shipped smoke tests. Below it, the finding is about your environment, not the pool |
| Your model mirrors the vplan's structure exactly | Both artifacts share the same blind author | Interaction rows the vplan lacks become crosses the model lacks. Go back to the *spec*, not to the model |
| Your Track B regression serializes the masters | Contention is annoying to debug | Ask for the both-request bin's count. The serialized-masters regression is the classic silent gap |
| You are chasing the coverage percentage | A number feels like progress | The M2 snapshot is graded on honesty. Closure is M4's gate |
| You have not started CtM-11 | M2 eclipses it | It lands Wednesday, and its transcript doubles as M2's required assistant task. One artifact, two obligations |
