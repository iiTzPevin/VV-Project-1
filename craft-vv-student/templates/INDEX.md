# Deliverable templates — index

Every Markdown file you submit this semester, when it first appears, and where
the starter lives. Copy a starter next to your work, keep its headings, fill it
in, and delete the `<!-- comment blocks -->` before you submit.

**New to Markdown?** Start with [`MARKDOWN.md`](MARKDOWN.md) — editors, live
preview, and how to edit files that live on eustis without living in `vim`.

---

## Starters provided

| Deliverable | What it argues | First due | Recurs | Starter |
|---|---|---|---|---|
| `gap_memo.md` | one bug the provided test cannot catch, and whether that is a controllability or an observability failure | Wk 1 | — | [`gap_memo.md`](gap_memo.md) |
| `ctmNN.md` | your prediction, the tool output, and the verdict — Check the Machine | Wk 2 | weekly, Wks 1–14 | [`ctm.md`](ctm.md) |
| `vplan.md` | that "done" was definable before you wrote tests | Wk 2 | revised each capstone milestone | [`vplan.md`](vplan.md) |
| `FINDINGS.md` | what your `found/total` means, and what it still cannot mean | Wk 5 | Wks 5–14 + both projects | [`FINDINGS.md`](FINDINGS.md) |
| `closure.md` | why the coverage curve flattened where it did, and the model's blind spots | Wk 6 | — | [`closure.md`](closure.md) |
| `nonvacuity.md` | that every assertion's antecedent actually fired | Wk 7 | — | [`nonvacuity.md`](nonvacuity.md) |
| `CONTRIBUTIONS.md` | who did what, at each milestone, checkable against the git history | Wk 11 | M1–M4 | [`CONTRIBUTIONS.md`](CONTRIBUTIONS.md) |

## No starter — write these from the assignment text

These follow the same contract as everything else in the course — **a verdict,
the evidence that establishes it, and an honest boundary on what it does not
establish** — but the structure is yours to choose. That is deliberate: by the
time these are due, deciding what the argument needs is part of the work.

| Deliverable | What it argues | Due |
|---|---|---|
| `security_assert.md` | your information-flow assertion, what it guarantees, and what it cannot (sim-only) | Wk 7 |
| `backdoor_report.md` | the verdict for each design, each backed by a converged proof or a saved counterexample; plus the boundary of what formal establishes and your `assume` set | Wk 8 |
| `security_reg.md` | the locked-register verdict, citing the exact test that establishes it — not prose | Wk 10, Project 2 |
| `ai_log.md` | prompt, prediction, evidence, and every fix you made | Projects 1 & 2 |
| `paper-status.md` | data in the repo, what remains, the biggest risk | Wks 11–12, graduate teams |

If you want a scaffold for one of these, the closest shape is `FINDINGS.md`
(evidence-first) for the three security verdicts and `ctm.md` (predict, run,
compare) for `ai_log.md`.

## Provided *to* you — do not write these

| File | What it is |
|---|---|
| `code/dut/specs/*.md` | the specifications you verify against (`alu.md`, `fifo.md`, `uart.md`, `axil_regfile.md`) |
| `code/capstone/<track>/SPEC.md` | your capstone track's specification |
| `INSTALL.md`, `README.md` | setup and orientation |

---

## The three habits every one of these rewards

1. **Paste the output, do not describe it.** A fenced block with the real
   `found/total` line beats a sentence about what it said. A claim with no
   transcript behind it is graded as though the run never happened.
2. **Name what you did not establish.** Every template has a section for this,
   and in most of them it is the highest-weighted row. It is not a disclaimer —
   it is the part that shows you understand your own evidence.
3. **Keep the headings.** Rubrics are scored row by row against them.
