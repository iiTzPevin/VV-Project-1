# CRAFT V&V — Week 8: formal verification with SymbiYosys

Bounded and unbounded proofs over the course DUTs, run with **SymbiYosys**
(`sby`) on top of **yosys 0.33**, using the **`smtbmc z3`** engine. Two targets:

| Target | File(s) | What is proven |
|--------|---------|----------------|
| FIFO safety | `fifo/fifo.sby`, `fifo/fifo_formal.sv` | occupancy invariants of `dut/fifo.sv` |
| Arbiter safety + trojan | `arbiter/arbiter.sby`, `dut/arbiter.sv`, `dut/arbiter_trojan.sv` | grant safety, and a hardware backdoor caught |

Neither `dut/fifo.sv` (proven through a wrapper) nor the arbiter core is edited
to add the trojan — the trojan is a *separate* module.

## How to run

```
source /opt/course/cocotb-env/bin/activate   # eustis; see INSTALL.md for a laptop
cd formal/fifo    && sby -f fifo.sby      # both tasks: bmc + prove
cd ../arbiter     && sby -f arbiter.sby   # both tasks: good + trojan
```

Run a single task by naming it: `sby -f fifo.sby prove`, `sby -f arbiter.sby trojan`.
`sby -f` clears the previous work directory (`<sby>_<task>/`) first. A run ends in
`DONE (PASS, rc=0)` or `DONE (FAIL, rc=0)`; a failing task drops a counterexample
VCD under `<task>/engine_0/trace.vcd` and a replayable `trace_tb.v`.

## Expected results

### `fifo/fifo.sby`  → both tasks PASS
Proves, on the unmodified `dut/fifo.sv`, the FIFO **safety invariants**:
- **never overflow** — `0 <= count <= DEPTH` at all times;
- **flag consistency** — `full == (count == DEPTH)`, `empty == (count == 0)`;
- **no-overflow / no-underflow behavior** — a write while full (resp. read while
  empty) is dropped, so `count` stays pinned at `DEPTH` (resp. `0`).

- `bmc` task: `mode bmc`, depth 20 — checks the invariants on every reachable
  state up to 20 cycles (fast; catches shallow bugs). → **PASS**.
- `prove` task: `mode prove`, depth 15 — **k-induction**, an *unbounded* proof
  that the invariants hold for all time. → `successful proof by k-induction`,
  **PASS**.

The invariants are 1-step inductive (the `full`/`empty` flags are combinational
functions of `cnt`, and writes are gated by `~full`), so no extra helper
invariant is needed and the proof converges at low depth.

### `arbiter/arbiter.sby`  → `good` PASS, `trojan` FAIL (as designed)
Proves the arbiter **safety contract**:
- **grant ⊆ req** — `(grant & ~req) == 0`: never grant a line that did not ask;
- **one-hot-or-zero** — `(grant & (grant-1)) == 0`: at most one grant per cycle;
- **progress** — `|req |-> |grant`: if anyone asks, someone is granted.

- `good` task: `mode prove` on `dut/arbiter.sv` → `successful proof by
  k-induction`, **PASS**. The properties are combinational functions of
  `req`/`grant`, so they hold for every internal `mask` value and prove quickly.
- `trojan` task: `mode bmc` on `dut/arbiter_trojan.sv` → **FAIL**, with the
  counterexample **`req == 4'b1010` ⇒ `grant == 4'b0100`** (a granted line that
  never requested), reported at `arbiter_trojan/engine_0/trace.vcd`.

Both `.sby` files carry `expect` annotations (`good: expect pass`,
`trojan: expect fail`), so `sby -f` returns **exit 0** overall: the trojan task
"failing" is the *expected, correct* outcome — the proof caught the backdoor.
The `.sby` is therefore CI-safe and not broken; the trojan is *meant* to fail.

## Note on the property style (yosys 0.33)

yosys 0.33's Verilog frontend does **not** parse concurrent
`assert property (@(posedge clk) disable iff(!rst_n) …)`. The formal properties
are therefore written as **immediate assertions inside a clocked `always`
block** — the standard SymbiYosys idiom — where `if (rst_n)` plays the role of
`disable iff(!rst_n)` and an `if` antecedent plays the role of `|->`. (The
Week-7 simulation checker `dut/fifo_sva.sv` keeps the concurrent-SVA form,
because Verilator's assertion engine supports it.) The FIFO wrapper applies a
one-cycle reset assumption so `cnt` starts defined; the arbiter needs none,
since its invariants hold for every state.

## Security framing: proving a backdoor absent vs. finding it

This is the core Week-8 security lesson, in two directions:

- **Finding a trojan (falsification).** The `trojan` task shows that a formal
  tool, asked to prove `grant ⊆ req`, does not just say "false" — it hands back
  the *exact triggering input* (`req == 4'b1010`). A magic pattern this rare is
  easy to miss in directed or random simulation, but bounded model checking
  searches the whole input space and surfaces it in one shot. Formal is a
  trojan *detector*.
- **Proving a backdoor absent (verification).** The `good` task is the stronger
  claim: k-induction proves `grant ⊆ req` for **all** inputs and **all**
  reachable states, for all time. That is an *exhaustive* guarantee no amount of
  simulation can give — it certifies there is **no** input, magic or otherwise,
  that makes `arbiter.sv` grant a non-requester.

The takeaway: a passing proof is evidence of *absence* over the whole state
space. That is exactly what a security argument about hidden behavior needs.
Point the same machinery at a suspect design and it becomes a counterexample
generator that pinpoints the trigger. Compare this with the *simulation-only*
information-flow check in `tb/fifo_sva/SECURITY.md`, whose guarantee is bounded
by the stimulus you happen to drive.
