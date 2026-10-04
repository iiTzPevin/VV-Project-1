# Week 14 · Session 1 — demo day I, sign-offs under review

This session is demo day, run as a sign-off review. You are in it twice: once
as a presenting team, once as the pre-assigned discussant for another team.
Here is how the session runs, what to bring, and what you will be asked.

**What it shows.** You are not demoing the design. You did not write it. You
are demoing the verification. A bug demonstrated outscores an all-clear with no
evidence.

Two things stay on the board all session. That one-line law above, and the
capstone packet's standard: *"a design found to be buggy, with the bug
demonstrated, scores higher than a design declared 'correct' with no
evidence."*

## What to bring

- Your slot number. The running order is posted with the M3 feedback.
- Your numbers page, ready to open on.
- The `m4`-candidate tree, in a state where you can run one gate live on it.
- Your report's residual-risk and sign-off page, ready to put on screen at the
  end of your slot.
- Your discussant assignment, read in advance. You open the critique for one
  other team.

The milestone contract is `weeks/week14/week14-hw.tex` (M4, 25% of the
capstone), due Sunday 23:59, tagged `m4`, with CtM-14 inside the report. The
session plan is `weeks/week14/week14.tex`.

## How the session runs

Slots are hard-timed at ten minutes against a visible countdown: **7:00 of
demo, 3:00 of critique.** Five slots run today.

- The clock starts when your numbers page is up, not when you are ready.
  Readiness is part of the slot.
- At 7:00 it cuts to critique wherever your demo stands. Your discussant asks
  the two questions. Anyone else may add one.
- Every slot closes with one sentence on evidence quality: what was checkable,
  what was asserted. No grade talk.
- If you overrun or your demo breaks, you move to the top of Session 2. You are
  never squeezed into someone else's time.

The plan plans for eight teams: five today, three in Session 2. If there are
more teams, Session 2's careers slot converts to demo slots before anything
else moves. The slots themselves never shorten.

## The anatomy of a demo that scores

1. **Open on the numbers page:** final `found/total`, the coverage pair, the
   lint count, every proof verdict — each with the run it came from.
2. **Run one gate live** on the `m4`-candidate tree. The point is that the
   evidence reproduces on demand.
3. **Walk one finding end to end** — stimulus to trace to the check that
   caught it, or survivor to the argument for why it lives.
4. **Say the residual-risk statement out loud.**
5. **Close on the sentence you are willing to sign.**

The strongest demo of the day may star a bug: driven, caught, traced. The
weakest may be the one where everything is green and nothing can be checked. A
feature tour fails inside its first minute.

> **Check yourself.** Time your own run-through against 7:00 before you
> present. If the numbers page is not up in the first thirty seconds, cut
> something earlier, not later.

## What you will be asked

Every demo ends with your residual-risk and sign-off page on the screen. Your
discussant opens with two required questions. Both stay on the board all
session:

1. *Point to one claim — which evidence class backs it: **proved, measured,
   sampled, or unexamined**?*
2. *Name one thing on this page you would not sign.*

You answer with a number or a named risk. Never with reassurance. If neither
exists, the honest answer is "unexamined", and it scores better than the
reflex.

There is one more question you should expect if your demo drifts: *"which
number on this screen can I check?"* It gets asked once, early, in public.

**Ground rules.** Critique the argument, never the team. A gap found in
critique costs you nothing today and saves your report before Sunday.

This is rehearsal, not theater. CtM-14's claim table (`ctm/ctm14.tex`) asks you
to do to your own report exactly what the class does here. Your discussant work
is the participation grade's (5%) closing entry.

> **Check yourself.** Take your own sign-off page and answer question 1 for
> every claim on it. Any claim you cannot label proved, measured or sampled is
> unexamined. Label it that way before someone else does.

## What full credit looks like, by track

Track A runs the harness live at the tag and scopes the claim to the
12-instruction subset. "Implements RV32I" unqualified is the giveaway
overstatement. Track B shows the contention regression with the both-request
bin's count on screen and states the fairness verdict at its class. Track C
runs `sby` live, states the 2^32 argument, and scopes the verdict to P1–P3 as
written.

## Peer eval, and the calendar

Each member submits an *individual, confidential* peer eval. It covers every
teammate's main contributions across all four milestones, an equity judgment,
and one sentence of evidence each. It goes outside the team repo, by the M4
deadline. It is cross-checked against `CONTRIBUTIONS.md` and the repo history,
and it feeds the capstone's Professionalism row (15%). A missing eval is a
professionalism problem of its own.

The calendar from here: CtM-13 due Wednesday 23:59. M4 due Sunday 23:59, which
is the report, the recorded demo made on the tagged tree, the closure evidence
and the final numbers, with CtM-14 inside the report. The graduate paper rides
the same tag. Session 2 holds the remaining three demos, then the
retrospective.

## If it goes wrong

| Problem | Why it happens | Fix |
|---|---|---|
| Your demo drifts into a feature tour | Product instinct: make it look finished | Answer the reset question yourself: *"which number on this screen can I check?"* Then go to that number |
| Your live gate run breaks | Demo-week rewiring is exactly when testbenches break | Do not debug on the clock. You move to the top of Session 2, and it gets logged. The recorded demo must still reproduce at the tag |
| Numbers on screen do not match the repo | The slides were made before the last rewire | Note it yourself, without ceremony. Grading reruns everything at the `m4` tag, so the discrepancy resolves there |
| You answer with reassurance | "We're confident that..." is a reflex | Use the required form: a number, or a named risk. If neither exists, say "unexamined" |
| You call a bounded run a proof | The verdict vocabulary slips under pressure | The M3 wording caps still apply. "No counterexample to depth k" is the sentence. *Proven* means `prove` mode or an inductive argument |
| As discussant you softball, or go silent | Critiquing peers feels rude | Ask both questions at full strength. The protocol is the kindness. Vagueness is not |
