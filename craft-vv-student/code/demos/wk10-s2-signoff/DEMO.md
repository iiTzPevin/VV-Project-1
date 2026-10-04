# Week 10 · Session 2 — signoff is a dashboard, not a number

You watched this in class. Here it is again so you can run it yourself.

**What it shows.** Signoff is not one number. It is a dashboard of measured
gates: lint, coverage, `found/total`, and the locked-register policy. Every
number on this one is produced in front of you, live.

Run everything from `code/`.

| Step | File | What you should get |
|------|------|---------------------|
| 0 | `step0_lint.py` | clean RTL: **0 findings**. Planted `lint_latch`: `%Warning-LATCH`, gate FAIL |
| 1 | `step1_policy.py` | the policy check passes clean and fires on the mutant. This step alone scores **3/8** |
| 2 | `step2_dashboard.py` | the signoff one-pager, every row measured live, verdict **GO** |

Here is step 0, in both forms:

```bash
just demo 10 s2 0        # or:  make -C demos/wk10-s2-signoff STEP=0
```

Every number below was measured on `dut/axil_regfile.sv` — sim steps and the
harness with Icarus, lint and coverage with Verilator 5.020, `DEMO_SEED=5`,
pool `tb/axil_ral/mutants_released.yaml` (8 mutants). Captured output is in
`expected/`. Planting:

```bash
python3 demos/wk10-s2-signoff/plant.py <id>        # no argument lists the pool
                                                   # + the local lint_latch defect
```

**Tooling note.** The course plan lints with `verible`. This container does not
have it, so the demo runs `verilator --lint-only -Wall` as the stand-in. Same
gate, different tool. Step 0 prints *both* command lines. On a machine that has
verible, run the verible one.

---

## Step 0 — run the cheapest gate

```bash
just demo 10 s2 0
```

**You should see:**

```
  with verible (the course tool):  verible-verilog-lint axil_regfile.sv
  stand-in on this machine:        verilator --lint-only -Wall axil_regfile.sv

lint: CLEAN -- 0 findings.  gate: PASS
```

No clock, no stimulus, no testbench. Lint is still a mandatory tapeout gate.
This block gates clean. Now plant a defect and see what the gate is for.

```bash
python3 demos/wk10-s2-signoff/plant.py lint_latch
make -C demos/wk10-s2-signoff STEP=0 DUT=~/.vvtemp/wk10-mutants/lint_latch/axil_regfile.sv
```

**You should see:**

```
  %Warning-LATCH: .../axil_regfile.sv:81:5: Latch inferred for signal
      'axil_regfile.rd_mux' (not all control paths of combinational always
      assign a value)
lint: 1 finding(s) [LATCH].  gate: FAIL
```

**What it means.** The planted defect drops the read-mux `default` arm. That is
the same class of bug as `always @(*) if (en) q = d;` from the slides. Lint
named the latch, the signal and the always block in under a second.

You may notice that a reset test would also catch the stale unmapped read. In
this 6-register block it would. The argument is the price. One second, before a
testbench exists, with the defect named instead of inferred from a failing read.

> **Check yourself.** Say what the warning gave you that a failing read would
> not. Name both the signal and the reason.

---

## Step 1 — check the locked register against the policy mutant

Write the property down first: *protected state must not change under a
transaction that lacks privilege.* Then run it as a check:

```bash
just demo 10 s2 1
```

**You should see:**

```
  the access-control property, as a check:
  arrange: SECURE <= 0xa5a5a5a5, then LOCK <= 1
  act:     SECURE <= 0xdeadbeef with LOCK=1   (no privilege)
  assert:  SECURE still reads 0xa5a5a5a5   -> write dropped   ok
  assert:  INTR[0] latched (0x00000001)   -> violation visible   ok
```

Now plant the mutant HW10's mutationbox promises. It makes the locked register
quietly writable:

```bash
python3 demos/wk10-s2-signoff/plant.py secure_writable_locked
make -C demos/wk10-s2-signoff STEP=1 DUT=~/.vvtemp/wk10-mutants/secure_writable_locked/axil_regfile.sv
```

**You should see:**

```
AssertionError: SECURITY: locked SECURE accepted a write (now 0xdeadbeef)
```

**What it means.** A happy-path RW test passes on this mutant. Session 1's
step 0 measured 3/8, with every policy mutant surviving. This check is the
difference between "the register stores data" and "the lock is a security
boundary."

Now put the score in course terms. The run takes about 50 s:

```bash
just mutate axil_ral         # student starter:  found/total = 1/8  =  12.5%
```

The reference suite scores **8/8 (100%)** on the same pool. That one is the
instructor's to run, so the number is quoted here rather than something you
type.

This step alone scores **3/8** (`secure_writable_locked`, `addr_secure_off1`,
`rvalid_stuck0`). A security check is one gate, not a suite. The reference gets
8/8 because reset, bit-bash and the policy walks each hold their own slice.

> **Check yourself.** The same pool scores 8/8 and 1/8 on the same RTL. Say in
> one sentence what that gap measures. It is not the design.

---

## Step 2 — watch the dashboard assemble itself

```bash
just demo 10 s2 2
```

Rows print as they are measured. Lint takes a second, coverage about 17 s, and
the two harness scores are the slow tail. Measured wall time: **1 min 56 s**. A
dashboard is a batch product, so expect to wait.

**You should see:**

```
  gate             measured                                        verdict
  lint             0 findings (verilator --lint-only -Wall)        PASS
  line coverage    97% -- 34/35 lines hit (reference suite)        PASS*
                   *uncovered: default: ; // unmapped: writes ignored
  mutation score   reference 8/8 (100%) on the released pool       PASS
                   starter tb 1/8 (12.5%) -- the gap is the week
  security         policy mutant secure_writable_locked FOUND      PASS
  checks           15 assert statements across 5 tests (ref suite) --
  signoff: GO -- no single number decides; the dashboard does
```

Walk the rows top to bottom:

- **Lint** is the gate from step 0. It is clean, so it earns one line and no
  meeting time.
- **97% line coverage** — and the dashboard *names the hole*: nobody ever
  wrote to an unmapped address.
- **8/8 vs 1/8** on the same pool is the whole course in one row: the metric
  measures the *suite*, not the design.
- **security** is its own row because HW10's hidden pool carries a policy
  mutant. In a signoff review, "the lock works" is a claim someone must back
  with the test that establishes it.
- **checks** (15 asserts across 5 tests) is context, not a gate. Assertion
  density tells you whether anything is being checked at all.

> **Check yourself.** Does that coverage hole block signoff? Argue it both
> ways, reachability against risk, then write down where you land and why.
> That argument is the FINDINGS.md survivor analysis HW10 grades.

**What it means.** Plan, stimulate, cover, assert, prove, wrap, sign off. Every
row on this dashboard is a week of this course. The capstone is this same
dashboard, produced for a design you did not write.

---

## If it breaks

| Symptom | Cause | Fix |
|---|---|---|
| `verible-verilog-lint: command not found` | Expected — verible is not in this container | The demo already runs the `verilator --lint-only` stand-in; the verible line is for machines that have it |
| Step 0 planted run shows extra findings | DUT copied to a file not named `axil_regfile.sv` | Use `plant.py`; it writes `~/.vvtemp/wk10-mutants/<id>/axil_regfile.sv` so the module/filename check stays quiet |
| Step 1 mutant run is green | Wrong mutant or wrong `DUT=` path | Paste the `DUT=` line `plant.py` prints; per-DUT build dirs rule out a stale binary |
| Dashboard row: "reference suite did not pass — no number" | Verilator missing or not 5.020 | `verilator --version`; fall back to showing `expected/step2.out` |
| Dashboard verdict NO-GO | The RTL or the reference suite moved under you | The dashboard is telling the truth — find the edit before you trust the verdict |
| Step 2 crawls past 3 min | Loaded machine (the harness compiles 8 mutants twice) | Let it finish and read the rows as they print, or compare against `expected/step2.out` |
