# Week 11 · Session 1 — inheriting a design you did not write

This session is a clinic. You work through it in class rather than watch it.
Here is what happens, what to bring, what you will be asked, and what you can
do on your own.

**What it shows.** Every feature row, coverage bin and assertion of the next
four weeks traces to a spec line you read this week. A row you cannot cite is a
risk row, not a feature row.

## What to bring

- Your team's track, already picked. The pick locks before Session 2.
- Your own track's spec, open and ready to annotate:
  `code/capstone/riscv/SPEC.md`, `code/capstone/axi_subsystem/SPEC.md` or
  `code/capstone/trojan/SPEC.md`.
- The course vplan template, `dist/templates/vplan.md`, open in a second tab.

Your milestone contract for the work this feeds is
`weeks/week11/week11-hw.tex` (M1, 15% of the capstone) plus
`capstone/capstone.tex`. The session plan itself is
`weeks/week11/week11.tex`. There is no separate slide lecture. The capstone
weeks run as clinics and studios, and the clinic is the session.

## What happens

1. Why the verifier is never the author. The stakes of the next four weeks.
2. A worked read of `code/capstone/riscv/SPEC.md`, six stops, annotated live.
3. Risk triage. Three sorting keys applied to twenty candidate features.
4. One spec line turned into one vplan row, live on the course template.
5. You draft your own rows from your own track's spec.

## Why the verifier is never the author

Nobody in industry verifies their own design. Separation of author and verifier
is the point of the job. On day one of a design-verification team you get a
spec, RTL you did not write, and a deadline. Interview loops test exactly this
skill: here is a spec fragment, what would you verify first?

The capstone packet says it plainly. The hardest part of verification is
inheriting an unfamiliar design and deciding what "verified enough to sign off"
means. That decision, argued with coverage and `found/total` evidence, is the
next four weeks.

**Name the trap.** After ten weeks of tooling the instinct is "we know the
tools, so skim the spec and start typing." That is backwards. Teams that start
coding on a skimmed spec spend M2 discovering scope they should have priced in
M1. And green smoke means *the DUT is alive*, nothing more.
`code/capstone/README.md` says exactly that.

Your deadline: M1, Sunday 23:59, repo tagged `m1`. That tag holds a vplan, an
environment skeleton, green smoke in CI, plus one extension that can fail.

## The worked read — six stops

The read is done on `code/capstone/riscv/SPEC.md` for everyone, whatever your
track. The method is the deliverable, not the annotations. You apply the same
method to your own contract later in the session, while it is fresh.

At each stop: circle the line, name the contract type, say what the plan must
do about it.

| Spec heading | Circle | It becomes |
|--------------|--------|------------|
| *Supported instruction subset (the contract)* | 12 instructions in; everything else "decodes to a NOP" | An undefined-behavior contract you must verify — the Week-2 ALU lesson at full scale |
| *Register model* | `x0` hardwired to 0; a writeback "visible on the **next** clock edge" | A timing contract: it dictates the cycle the scoreboard samples on |
| *Memory map* | index = `(addr >> 2) mod WORDS`, so `0x100` maps to word index 0; "the ISS mirrors this exactly" | An aliasing contract — decide *now* whether a mismatch there is a DUT bug or a model bug |
| *Reset* | "The register file is not reset" | A spec gap: read-before-write must be resolved in writing — constrain stimulus, or declare it unchecked |
| *Observability hooks (harness)* | `dbg_sel`/`dbg_reg`, `dbg_dmem_idx`/`dbg_dmem_data` | How a scoreboard sees architectural state without hierarchical peeking — plan against these, not internals |
| *What the smoke test exercises (and what it does NOT)* | "It is a **bring-up** test only" | The honest boundary of the provided test; the plan starts on the far side of it |

The spec hands you its own risk list if you read it with the Week-2 question:
*why would a bug here matter, and who observes it?* Lines that survive that
question become feature rows. Lines that cannot answer it become risk rows.

> **Check yourself.** Read one of those six stops in your own track's spec
> instead. Name the contract type before you look at what the plan must do.

## Risk triage — three sorting keys

You have twenty candidate features and four weeks. What do you verify first?
Three keys, applied in order:

1. **Dependency** — the path every later result observes through: writeback
   and `x0` for the core, the arbiter grant for the interconnect, the unlock
   logic for the gate. If that path is wrong, every later "pass" is noise.
2. **Ambiguity** — lines the spec flags or leaves open: the modulo aliasing,
   the unreset register file. Bugs live where two readings diverge.
3. **Security weight** — the track's security requirement, cheap to plan now
   and expensive to retrofit at M3. Every track carries one: Track A's
   privileged-instruction rule, Track B's locked-register access control,
   Track C's absence-of-malicious-behavior properties.

Rank whatever remains by failure cost times likelihood. Corner immediates and
boundary states come before mid-range comfort.

On the RISC-V read, that ordering runs: writeback and `x0` first, by
dependency. Then the aliasing and reset gaps, by ambiguity. Then the security
row. Then the corners.

> **Check yourself.** Place two more features in that ordering: branch
> taken/not-taken, and the `sw`→`lw` round-trip. Name the key that put each one
> where it landed.

## From spec line to vplan row

Open `dist/templates/vplan.md`. The discipline is fixed. Every feature row
carries an ID, the behavior, a *spec citation* (`Req`), a priority, and how it
will be verified. A row you cannot cite belongs in section 5 (risk) as a spec
gap. It does not belong in the feature list.

Here is one line worked through. *"x0 always reads 0 and ignores writes"*, from
*Register model*, becomes

- a feature row: `F1 · x0 reads 0, ignores writes · SPEC "Register model" · H · CRV + assertion`,
- a coverage point: writes *targeting* `x0` — the discard case must be driven,
- a check the scoreboard performs on every retire.

One spec line, three artifacts. That fan-out is what "the vplan is derived from
the spec" means. M2 derives its coverage axes from these rows in turn.

## What you will be asked to produce

You sit with your team, open your own track's `SPEC.md`, and draft **three
feature rows plus two risk rows** on the template. Expect an instructor to push
every vague row toward a citation.

Then a couple of teams read a row aloud. The challenge is always the same:
*cite the section.* A row that cannot answer moves to the risk list in front of
everyone. That is the lesson working, not a penalty.

Nothing you draft here is throwaway. These rows go straight into the M1 vplan.

## On your own, before Session 2

Lock the track. Fork the repo. Then run the bring-up sanity check from `code/`:

```bash
make -s -C capstone/riscv SIM=icarus     # or axi_subsystem / trojan
```

1 test for the core, 3 for the interconnect, 2 for the gate. All green as
shipped. The studio door criterion in Session 2 is that same green, in your
team's repo and in your CI.

> **Check yourself.** Your smoke run is green. Say out loud what that does and
> does not prove. If your answer sounds like "the design works", read the
> *What the smoke test exercises* section again.

## If you get stuck

| Problem | Why it happens | Fix |
|---|---|---|
| Your team is still shopping for a track | The choice feels consequential. It is less so than losing bring-up time | Pick now. Session 2 assumes a chosen DUT, and a team still shopping during studio burns its bring-up block |
| Your rows have no citations | You paraphrased the spec from memory | Answer the one challenge: *cite the section*. No citation means the row is a risk row, so file it as one and move on |
| You plan to do the first read on Saturday | The session reads like a lecture to sit through | The drafting block exists to force the first read into class time. Draft the rows in the session |
| "The smoke test passes, so bring-up is done" | Green is persuasive | Green smoke means the DUT is alive, nothing more. The smoke tests are deliberately shallow, and the M1 packet grades a checker that can *fail* |
| You cannot settle whether a modulo-aliasing mismatch is a DUT bug or a model bug | The spec resolves it, and nobody looked | Point at the line: "the ISS mirrors this exactly." A disagreement with the ISS on aliasing is a bug in one of them. Your plan records which one you will believe, and why |
