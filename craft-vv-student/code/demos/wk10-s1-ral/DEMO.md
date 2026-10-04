# Week 10 · Session 1 — a register is a policy, not a signal

You watched this in class. Here it is again so you can run it yourself.

**What it shows.** Read-after-write scored 3/8, and every policy mutant
survived it. The same register map, driven through a register model, scores
8/8. The test everyone writes first proves storage, and storage was never the
risk.

Run everything from `code/`.

| Step | File | What you should get |
|------|------|---------------------|
| 0 | `step0_raw.py` | **3/8** — green, and all three policy mutants survive |
| 1 | `step1_reset.py` | **2/8** — the reset walk; one row flips to `MISMATCH` |
| 2 | `step2_bitbash.py` | **5/8** — bit-bash plus the RO and W1C checks |
| 3 | `step3_secure.py` | **3/8** — the locked SECURE register |
| — | steps 1–3 as one suite | **8/8** — the union is the whole released pool |

Here is step 0, in both forms:

```bash
just demo 10 s1 0        # or:  make -C demos/wk10-s1-ral STEP=0
```

Every number below was measured on `dut/axil_regfile.sv` with Icarus,
`DEMO_SEED=5`, against `tb/axil_ral/mutants_released.yaml` (8 mutants).
Captured output for each step is in `expected/`. To plant a pool mutant for
the red runs:

```bash
python3 demos/wk10-s1-ral/plant.py <mutant_id>     # no argument lists the pool
make -C demos/wk10-s1-ral STEP=N DUT=~/.vvtemp/wk10-mutants/<mutant_id>/axil_regfile.sv
```

---

## Step 0 — write it, read it back, and see what that misses

```bash
just demo 10 s1 0
```

This is the register test everyone writes first: write it, read it back, done.
It passes.

**You should see:**

```
  read-after-write, straight down the map (no model):
  CTRL     <= 0x9f767c45   read -> 0x9f767c45   ok
  SCRATCH  <= 0x4164d839   read -> 0x4164d839   ok
  SECURE   <= 0xbde5c099   read -> 0xbde5c099   ok
  LOCK     <= 0x00000001   read -> 0x00000001   ok   (the lock bit stores a 1 -- tested!)
  STATUS   read -> 0x5a5a0f0f   nonzero, looks alive (unchecked)
  4/4 read-after-write pairs match: PASS
```

> **Check yourself.** The pool has 8 planted bugs. How many does this find?
> Write the number down before you read on.

The score is **3/8**: `addr_secure_off1`, `scratch_read_ctrl`,
`scratch_lsb_stuck` — wiring bugs, the kind read-after-write is for. The five
survivors are `ro_writable`, `secure_writable_locked`, `w1c_as_rw`,
`ctrl_reset_nonzero`, `rvalid_stuck0`: every policy, the reset values, the
bus handshake. **The test proves storage, and storage was never the risk.**

Look again at the LOCK line: it shows the lock bit *stores* a 1. Nothing here
asks whether LOCK=1 protects anything — hold that thought for step 3.

---

## Step 1 — build the register model, and get reset for free

Build the table yourself — name, address, policy, reset value, one row per
register. Here is what the mirror is: `RegfileModel` tracks what the model
*believes* the hardware holds, so every read has a predicted value without
hand-deriving it per register.

```bash
just demo 10 s1 1
```

Green: 7 reads (6 registers + one unmapped address), dut == table == mirror.
Now plant the pool's reset mutant and run the same loop:

```bash
python3 demos/wk10-s1-ral/plant.py ctrl_reset_nonzero
make -C demos/wk10-s1-ral STEP=1 DUT=~/.vvtemp/wk10-mutants/ctrl_reset_nonzero/axil_regfile.sv
```

**You should see:**

```
  reg      addr  policy      dut         mirror
  CTRL     0x0   RW          0xffffffff  0x00000000  <- MISMATCH
  STATUS   0x1   RO          0x5a5a0f0f  0x5a5a0f0f  ok
  ...
  7 reads, 1 mismatch(es)
AssertionError: reset values wrong for: CTRL
```

**What it means.** The mismatch surfaced by *name*, from a loop nobody will
ever edit again. Step 0 could not see this bug at all — it wrote before it
read.

> **Check yourself.** Say in one sentence why step 0 is structurally blind to
> every reset-value bug, no matter how many registers you add to it.

---

## Step 2 — bit-bash, then walk the policies

```bash
just demo 10 s1 2
```

**You should see:**

```
  [RW ] CTRL     35 patterns (walking-1s, all-1s, zero, 0xa5a5a5a5)   ok
  [RW ] SCRATCH  35 patterns ...   ok
  [RW ] LOCK     35 patterns ...   ok
  [RO ] STATUS   held 0x5a5a0f0f across 3 junk writes           ok
  [W1C] INTR     all-ones write set nothing (bus can only clear)      ok
```

105 bit-bash writes and the two checks read-after-write cannot express: RO
*rejects*, W1C *cannot be set from the bus*. All generated from the table.

> **Check yourself.** How long would 105 hand-written read/write pairs take
> you? Now say what happens to that number when a register is added to the map.

Now plant the RO mutant and let the walk find it:

```bash
python3 demos/wk10-s1-ral/plant.py ro_writable
make -C demos/wk10-s1-ral STEP=2 DUT=~/.vvtemp/wk10-mutants/ro_writable/axil_regfile.sv
```

**You should see:**

```
AssertionError: RO STATUS changed to 0xffffffff after write 0xffffffff
```

**5/8 on the pool.** The three survivors are the reset mutant (step 1's job),
and the two SECURE mutants — which are next.

---

## Step 3 — test the locked SECURE register

Step 0 proved the lock bit stores a 1. Now ask the question that matters: does
LOCK=1 *protect* anything?

```bash
just demo 10 s1 3
```

**You should see:**

```
  [1] LOCK=0, SECURE <= 0xa5a5a5a5, read-back ok   (unlocked: writable)
  [2] LOCK=1, SECURE <= 0x5a5a5a5a   -> dropped, still 0xa5a5a5a5   ok
  [3] INTR[0] latched by hardware: INTR reads 0x00000001   ok
  [4] LOCK=0, SECURE <= 0xdeadbeef, read-back ok   (unlocked again)
  property held: protected state never moved without privilege
```

Then the security mutant — the one HW10's hidden pool grades:

```bash
python3 demos/wk10-s1-ral/plant.py secure_writable_locked
make -C demos/wk10-s1-ral STEP=3 DUT=~/.vvtemp/wk10-mutants/secure_writable_locked/axil_regfile.sv
```

**You should see:**

```
AssertionError: SECURITY: locked SECURE accepted a write (now 0x5a5a5a5a)
```

**What it means.** Access control is a property you can check, and a mutant
that makes a locked register writable is the bug it would be in silicon.

The run ends with `INTR[0]` still set.

> **Check yourself.** Write 1 to INTR[0]: is it clear? Write 0: is it clear?
> Predict both, then write the check. One check covers both: drive each write
> and assert the bit clears on exactly one of them.

**The union.** Steps 1–3 as one suite score **8/8** — the same 100% the
reference suite gets. Read-after-write plus a table of policies is the whole
pool; that is what "the model is the test plan" means.

---

## If it breaks

| Symptom | Cause | Fix |
|---|---|---|
| `ModuleNotFoundError: models.regfile_model` | `PYTHONPATH` missing `code/lib` | Run via `make`/`just` from `code/`; the Makefile exports it |
| `plant.py: find-string not present in DUT` | DUT edited since the pool was cut | `git diff dut/axil_regfile.sv`; the pool's `find` strings must match the source |
| Mutant run is green | The planted mutant is not one this step targets (each step finds its slice) | Match mutant to step: 1↔`ctrl_reset_nonzero`, 2↔`ro_writable`, 3↔`secure_writable_locked`. Paste the `DUT=` line `plant.py` prints; per-DUT build dirs rule out a stale binary |
| step 0 junk values differ from `expected/` | `DEMO_SEED` exported by an earlier demo | `unset DEMO_SEED` (default is 5) |
| step 2 fails on clean RTL at LOCK | bash order changed so SECURE is written while locked | Bit-bash only rows with policy `RW`; SECURE is `LOCKED_RW` and must stay out of the bash loop |
