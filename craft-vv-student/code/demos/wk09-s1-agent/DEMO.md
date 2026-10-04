# Week 9 · Session 1 — the agent is your Week 4 testbench, standardized

You watched this in class. Here it is again so you can run it yourself.

**What it shows.** The agent drives the same traffic and finds the same
mutants as the flat test. UVM added structure, not power. The structure is the
part you keep.

Run everything from `code/`.

| Step | File | What you should get |
|------|------|---------------------|
| 0 | `step0_flat.py` | **8/8** — 38 reads checked, stream digest `6d801d8c` |
| 1 | `step1_phases.py` | 0/8 — the phase walk, no bus traffic |
| 2 | `step2_wired.py` | 0/8 — 5 of 5 transactions reach the subscriber |
| 3 | `step3_agent.py` | **8/8** — same 38 reads, same digest `6d801d8c` |

Here is step 0, in both forms:

```bash
just demo 09 s1 0        # or:  make -C demos/wk09-s1-agent STEP=0
```

Every number below was measured on `dut/axil_regfile.sv` with Icarus,
`DEMO_SEED=5`, against `tb/axil_uvm/mutants_released.yaml` (8 mutants).
Captured output for each step is in `expected/`. If your run differs, the DUT
or the pool moved.

---

## Step 0 — start where Week 4 left you

```bash
just demo 09 s1 0
```

This is the testbench you already know how to write, on the Week 9 register
file. It passes, and it finds all 8 released mutants.

**You should see:**

```
reads checked against the model: 38, mismatches: 0
stream digest = 6d801d8c  over 68 transactions
```

**Note the digest line before you move on.** It is an order-sensitive
fingerprint of every (direction, address, data) the bus carried. Write
`6d801d8c` down. It comes back in step 3.

> **Check yourself.** Which of these lines do you get to lift onto the UART
> next month? Count them before you read the next paragraph.

Walk the file top to bottom: the driving is welded to the checking, the
checking to the stimulus, all of it to this file. The count is zero lines.
That — not finding power — is the problem this week solves.

---

## Step 1 — read the phase schedule

Type the tree yourself: a test that builds an env, an env that builds an
agent, an agent that builds two leaves. Every phase method announces itself.

```bash
just demo 09 s1 1
```

**You should see:**

```
build_phase    uvm_test_top   -> creating env
build_phase    uvm_test_top.env   -> creating agent
build_phase    uvm_test_top.env.agent   -> creating driver, monitor
build_phase    uvm_test_top.env.agent.driver
...
connect_phase  uvm_test_top.env.agent.driver
connect_phase  uvm_test_top.env.agent   (driver/monitor already connected)
connect_phase  uvm_test_top.env
connect_phase  uvm_test_top
run_phase      uvm_test_top.env.agent.driver   (would drive the bus here)
```

**What it means.** Build walks down (parents create children), connect walks
back up (you cannot connect a port on a component that does not exist), then
every `run_phase` starts at once and simulated time passes only there. Week 4's
testbench had the same order — enforced by you remembering it. Here the
schedule is the framework's job.

> **Check yourself.** Say what would break if connect ran downward like build.
> Point at one line of the log that proves the order matters.

---

## Step 2 — wire the agent, watch transactions arrive

Build on the skeleton: the driver pulls items with `get_next_item`/`item_done`,
the monitor publishes what it sees on an analysis port, the DUT handle travels
through ConfigDB, and a subscriber prints whatever arrives.

```bash
just demo 09 s1 2
```

**You should see:**

```
subscriber got #3: RD a=0x0 d=0x00000011 rvalid=1
subscriber got #5: RD a=0x1 d=0x5a5a0f0f rvalid=1
transactions that reached the subscriber: 5 of 5 sent
```

**Look at #5.** The monitor read back STATUS's fixed pattern `0x5a5a0f0f` —
and nothing checked it. The plumbing carries data; there is not one line of
checking in the environment yet. The mutation score agrees: **0/8**. A wired
agent with no scoreboard is cabling, not verification.

This is the file you extend next. Connect the same analysis port to your own
subscriber and confirm arrival.

> **Check yourself.** The transactions all arrived and the score is still 0/8.
> Name the one component missing from this environment.

---

## Step 3 — run step 0's stimulus through the agent

The subscriber grows into a scoreboard (RegfileModel + the digest), and a
sequence replays step 0's exact transaction list.

> **Check yourself.** If the agent is wired right, what two numbers must come
> out? Name them before you run this step.

```bash
just demo 09 s1 3
```

**You should see:**

```
reads checked against the model: 38, mismatches: 0
stream digest = 6d801d8c  over 68 transactions
```

**What it means.** Same digest, same 38 reads, same simulated end time (1385 ns
in both runs), and the harness says **8/8 — identical to step 0**. Nothing
about the testbench's *behavior* changed today. What changed is that the
driver, monitor, and scoreboard are now parts with standard names and standard
seams. Session 2 swaps one of those parts without editing anything around it,
and next month the same shape drives the UART.

---

## If it breaks

| Symptom | Cause | Fix |
|---|---|---|
| `ModuleNotFoundError: models.regfile_model` | `PYTHONPATH` not picking up `code/lib` | Run via `just`/`make` from `code/`, or `export PYTHONPATH=$PWD/lib` |
| Step 2/3 dies in `build_phase` with a ConfigDB error | `keep_singletons=True` dropped from `run_test` — it clears ConfigDB before building | The kwarg is load-bearing; see the entry function |
| Step 0 and step 3 digests differ | `DEMO_SEED` exported somewhere, or `gen_stimulus` edited mid-demo | `unset DEMO_SEED` (default is 5); diff against `expected/` |
| Step 0 `rvalid not asserted` on clean RTL | read sampled before the 1 ns settle after the rising edge | The `Timer(1, units="ns")` before sampling is load-bearing (registered read) |
| Step 1 phases print in another order | children created in a different order in `build_phase` | Order follows creation order; match the file |
