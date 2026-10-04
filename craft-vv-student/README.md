# CRAFT · Verification & Validation of Digital Systems — student starter code

You downloaded this packet from Webcourses. It has everything you need to build
and **self-check** your testbenches locally before you turn them in. Your grade
is not computed here — you submit through Webcourses (see *Submitting*, below).

Check `VERSION.txt` for which build you have; mention it if you ask for help.

## Set up your tools

Full instructions are in `INSTALL.md`. Pick the row that matches your machine:

- **UCF / eustis lab machines:** `source /opt/course/cocotb-env/bin/activate`
- **Your own machine, with Nix:** from this folder run **`nix-shell`**. (Use
  `nix-shell`, not `nix develop`, here — this is an extracted folder, not a git
  checkout, and the classic `shell.nix` path does not need git. The first run
  builds a local `.venv` from `code/requirements.txt`.)
- **Your own machine, no Nix:** install the tools per `INSTALL.md`, then
  `python3 -m venv .venv && source .venv/bin/activate && pip install -r code/requirements.txt`.

Verify: `bash code/setup/verify_env.sh` (every tool `OK` + an ALU smoke test).

## Run and score a lab

```bash
cd code
just test alu            # run the ALU testbench (or: make -C tb/alu SIM=icarus)
just waves alu           # ...and write a waveform, then print the file to open
just mutate alu          # score YOUR suite as found/total vs the released practice pool
just formal fifo         # a SymbiYosys proof (Week 8)
```

**Waveforms are off by default** — a plain run writes no trace at all, and the
flag differs by simulator (`WAVES=1` for Icarus, `VERILATOR_TRACE=1` for
Verilator, and `WAVES=1` under Verilator is *silently ignored*). `just waves`
picks the right one and tells you the path; use it rather than the raw flag.

`just` is optional — each recipe is a one-line command you can run by hand
(`just --list` shows them). Prefer a browser? The class practice portal does the
same released-pool scoring with no local setup; your instructor will share the
link and access code.

## What the score means

We report **found / total**: how many injected faults ("mutants") your testbench
catches. A mutant is *found* when your test **fails** on it. Full credit is at the
threshold shown for each lab (typically 90%). The released pool here is for
practice; the graded pool is different but tests the same behaviors, so a suite
that only chases these specific mutants will not generalize.

## What you write — and the starters for it

Most graded work in this course is a Markdown file you write next to your code:
a verification plan, a findings report, a weekly Check-the-Machine entry. Every
one of them has a fill-in-the-blank starter in **`templates/`**.

| You write | First due | Starter |
|---|---|---|
| `gap_memo.md` — the verification-gap memo | Week 1 | `templates/gap_memo.md` |
| `ctmNN.md` — Check the Machine, weekly | Week 2 | `templates/ctm.md` |
| `vplan.md` — the verification plan | Week 2 | `templates/vplan.md` |
| `FINDINGS.md` — found/total + survivor analysis | Week 5 | `templates/FINDINGS.md` |
| `closure.md` — the coverage-closure argument | Week 6 | `templates/closure.md` |
| `nonvacuity.md` — per-property antecedent evidence | Week 7 | `templates/nonvacuity.md` |
| `CONTRIBUTIONS.md` — the capstone team record | Week 11 | `templates/CONTRIBUTIONS.md` |

Copy the starter next to your work, keep its headings, fill it in, and delete
the `<!-- comment blocks -->` before you submit. Several rubrics are scored row
by row against those headings, so renaming them costs you points.

`templates/INDEX.md` is the full map, including the deliverables that have no
starter yet. **New to Markdown?** `templates/MARKDOWN.md` covers editors,
previewing, and editing files that live on eustis.

## Submitting

When you are happy with your score, **zip your test file for that lab and upload
the zip to the matching Webcourses assignment.** For example, for the ALU lab, zip
`test_alu.py` and submit it. You only submit your testbench module — not the RTL
or the pools. Grading re-runs your suite against the trusted design and a hidden
pool, so editing the provided RTL locally will not change your grade (your suite
must still pass on the clean, unmodified design first).

## Working with AI — "Check the Machine"

You may use AI assistants, but treat anything they produce as **untrusted IP**:
you are the verification engineer, and your job is to catch its mistakes, not to
trust them. Read the course policy in your syllabus.

## Layout

```
code/dut/        the designs under test (+ specs)     -- do not edit for grading
code/lib/        golden models + the craft_mutate scorer
code/tb/<lab>/   your testbench starter + the released practice pool + Makefile
code/formal/     SymbiYosys proofs (Week 8)
code/capstone/   capstone starters
templates/       fill-in-the-blank starters for every .md you submit
                 + MARKDOWN.md (editors, preview, editing on eustis)
                 + INDEX.md    (which deliverable, which week, which starter)
INSTALL.md       toolchain setup   |   nix files: shell.nix / flake.nix
```
