# Week 8 · Session 2 — proving a backdoor absent, and reading the fine print

You watched this in class. Here it is again so you can run it yourself.

**What it shows.** A green proof certifies the absence of what you specified,
inside the world your assumes allow. It certifies nothing more. That
difference is where backdoors live.

Run everything from `code/`.

| Step | File | What you should get |
|------|------|---------------------|
| 0 | `step0_good.sby` | **PASS** — the honest arbiter, proven by k-induction |
| 1 | `step1_trojan.sby` | **FAIL, step 1** — the solver hands back the trigger pattern |
| 2 | `step2_assume_env.sby` | **PASS ×2** — one assume, and the same search proves clean |

Here is step 0, in both forms:

```bash
just demo 08 s2 0        # or:  make -C demos/wk08-s2-absence STEP=0
```

Steps are `.sby` files, not cocotb, so they need `sby`, `yosys` and `z3`. If a
command is not found, that is an environment problem and not a broken demo —
setup and property notes are in `code/formal/README.md`.

The safety contract is compiled inside the DUTs themselves (`ifdef FORMAL` in
`dut/arbiter.sv` and `dut/arbiter_trojan.sv` — the same three asserts in
both):

```systemverilog
assert ((grant & ~req) == {N{1'b0}});               // grant subset of req
assert ((grant & (grant - ONE)) == {N{1'b0}});      // one-hot-or-zero
if (|req)
    assert (|grant);                                // progress
```

All verdicts and the trigger pattern below were measured on this repo's RTL
(course container; every run lands in under a second). Captured output in
`expected/`; steps 0 and 1 are the `good`/`trojan` tasks of
`formal/arbiter/arbiter.sby`, run from the demo dir.

---

## Step 0 — prove absence

```bash
just demo 08 s2 0
```

**You should see:**

```
[step0_good] summary: successful proof by k-induction.
[step0_good] DONE (PASS, rc=0)
```

Session 1's question was *is this property true*. This session's is the
security question: *is there any input, however magic, that makes this arbiter
grant a line that never asked?* For `dut/arbiter.sv` the proof answers no —
not "none found", but *there is none*. That sentence is not available from
simulation at any cycle count.

Why so fast: the contract is a combinational function of `req`/`grant`, so it
holds for every value of the internal `mask` — the induction closes almost
immediately. Contrast with Session 1's FIFO, where the invariant had to carry
state.

> **Check yourself.** Write the PASS as one sentence that starts "there is no
> input such that...". Say which words you would have to soften if this were a
> simulation run instead.

---

## Step 1 — ask the same question of a trojaned DUT

Same three asserts, different netlist. `dut/arbiter_trojan.sv` is the
round-robin core plus a few lines someone hopes you will not read. Do not open
the trojan source yet.

```bash
just demo 08 s2 1
```

**You should see:**

```
[step1_trojan] summary: engine_0 (smtbmc z3) returned FAIL
[step1_trojan] summary:   failed assertion arbiter_trojan.$assert$arbiter_trojan.sv:53$37 at ... step 1
[step1_trojan] DONE (FAIL, rc=0)
```

then `show_trigger.py` reads the trace back:

```
  edge  rst_n   req    grant   grant&~req
     0    1    1010    0100    0100  <- VIOLATION: line 2 granted, never requested

  trigger: req = 4'b1010  ->  grant = 4'b0100
```

**What it means, in two beats.**

*Beat one — the needle.* The trigger is one request pattern out of sixteen,
and it has to be exact: lines 1 and 3 asserted, nothing else. A directed test
drives the patterns you thought of; Week 5 showed a seed deciding whether
random stimulus reaches a corner at all. BMC checks *all* input values at
*every* step by construction — the magic pattern is found at step 1, in under
a second, by a solver nobody told what to look for.

*Beat two — the reversal.* Now open `dut/arbiter_trojan.sv` and find
`wire magic = (N == 4) && (req == 4'b1010);`. The tool recovered the exact
constant from the property alone. Falsification and verification are the same
machinery: pointed at a clean design it proves absence (step 0); pointed at a
dirty one it prints the trigger. HW8's backdoor verdict wants one of exactly
these two artifacts — a converged proof or this trace.

> **Check yourself.** Sixteen request patterns exist. Estimate your odds of
> hitting `4'b1010` with random stimulus in a hundred cycles, then say why the
> solver needed one step.

---

## Step 2 — see what "absent" is quoted against

Here is the integration note. Master 3 is the debug unit, fused off in
production silicon. `req[3]` can never rise. Is step 1's counterexample even
reachable in that system?

> **Check yourself.** Decide what one line you would add to the `.sby` before
> you read the next block.

The answer is already written for you (`step2_assume_env.sv`, and the whole
step is one line):

```systemverilog
// THE ENVIRONMENT MODEL. One line. This is the whole step.
always @(posedge clk) assume (!req[3]);
```

```bash
just demo 08 s2 2
```

**You should see:**

```
[step2_assume_env_bmc] DONE (PASS, rc=0)
[step2_assume_env_prove] summary: successful proof by k-induction.
[step2_assume_env_prove] DONE (PASS, rc=0)
```

The bmc task is the *same search that produced the counterexample* — same
depth, same engine, same trojaned netlist. The trigger needs `req[3]==1`;
every trace the solver may now consider has `req[3]==0`; the counterexample
is no longer in the search space. Both verdicts are true statements.

**Now the two questions, in order:**

1. *Did we fix the model or hide a bug?* If the fuse claim is a fact of the
   silicon, we modeled the environment — that is what assume is *for*, and
   without it formal drowns you in unreachable counterexamples. If the claim
   is wrong — debug SKU, glitched fuse, an attacker electrically driving the
   bus — we filed the backdoor under "cannot happen" and signed off.
2. *What does PASS now claim?* Not "no backdoor." It claims: no state
   violating **these three asserts** is reachable **under this assume**. Both
   halves are the fine print. Session 1's pool sweep showed the property half —
   three data-path mutants invisible to count-only invariants. This step is
   the assume half. Same boundary, approached from both sides.

**What it means.** An assume moves a behavior from *checked* to *trusted*.
Every assume in your `.sby` is a sentence in your signoff that nobody proved.
HW8 asks for the assume-set accounting in `backdoor_report.md` for exactly this
reason — a verdict without that accounting earns nothing.

> **Check yourself.** List every assume your own HW8 `.sby` carries. For each
> one, name the physical fact that makes it true, and what breaks if that fact
> is wrong.

---

## If it breaks

| Symptom | Cause | Fix |
|---|---|---|
| `show_trigger: no trace at ...` | step 1 not run yet, or its run did not fail | `make STEP=1`; if sby said PASS, the DUT is not the trojaned one — check `step1_trojan.sby` still reads `arbiter_trojan.sv` |
| `DONE (PASS, rc=1)` on step 1 | the backdoor was *not* caught — someone edited the contract or the magic constant | rc=1 is sby reporting `expect fail` unmet; diff `dut/arbiter_trojan.sv` against the repo |
| FAIL on step 2 | the assume was edited out, or `[script]` lost `-DFORMAL` (the assume compiles only under it) | restore `step2_assume_env.sv`; the wrapper needs exactly one assume |
| Trigger differs from `4'b1010` | `show_trigger.py` exits non-zero by design | the RTL's magic constant moved; fix the RTL or the slide, not the script |
| No GTKWave on your machine | — | `show_trigger.py` prints the whole trace; the VCD is only for opening in a viewer |
| yosys errors on the SVA | concurrent-SVA syntax crept in | yosys 0.33 wants immediate assertions in a clocked block — property style notes in `code/formal/README.md` |
