# secure_gate -- SPEC (Track 3, security / hardware trojan)

A **key-comparator access gate**. It releases data only when the supplied key
matches the expected key; otherwise the data output is masked and the gate
reports *locked*. This track ships **two** RTL variants with an identical
interface and module name (`secure_gate`):

- `secure_gate_clean.sv` -- the golden, trojan-free reference (smoke + mutants).
- `secure_gate_trojan.sv` -- a planted variant with a hidden backdoor trigger.

Your job (M3) is to write a security property strong enough that it
**passes on the clean variant and fails on the trojan**. Prove it formally if
you can. The trigger is a single 32-bit value, so random stimulus will
essentially never hit it.

## Parameters
- `DW` (8) data width.
- `EXPECTED_KEY` (`0xA5A5_1234`) the one key that legitimately unlocks the gate.

## Ports
| Signal | Dir | Meaning |
|--------|-----|---------|
| `clk`, `rst_n` | in | clock, active-low synchronous reset |
| `key` | in | 32-bit key presented this cycle |
| `data_in` | in | `DW`-bit payload |
| `unlocked` | out | 1 iff access is granted this cycle |
| `data_out` | out | `data_in` when unlocked, else `0` (masked) |
| `access_count` | out | 8-bit count of cycles the gate has been unlocked |

`unlocked` and `data_out` are combinational in `key`/`data_in`; `access_count`
is a registered side effect.

## Intended behavior (the contract)
1. **Unlock:** `unlocked == 1` **iff** `key == EXPECTED_KEY`.
2. **Masking:** `data_out == data_in` when `unlocked`, otherwise `data_out == 0`.
3. **Counter:** on each rising edge, `access_count` increments **iff** `unlocked`;
   reset clears it to 0.

## Security properties to enforce (M3 -- these define "trojan-free")
- **P1 (no backdoor):** `unlocked |-> (key == EXPECTED_KEY)`.
  Equivalently `(key != EXPECTED_KEY) |-> !unlocked`.
- **P2 (no leak):** `(key != EXPECTED_KEY) |-> (data_out == 0)`.
- **P3 (counter integrity):** `access_count` changes only on unlocked cycles.

## The planted trojan (what you must catch)
`secure_gate_trojan.sv` adds a dormant trigger:

```
localparam logic [31:0] MAGIC_KEY = 32'hDEAD_BEEF;
assign unlocked = key_ok | (key == MAGIC_KEY);   // backdoor
```

For **every** input except `key == 0xDEAD_BEEF` it is bit-identical to the clean
gate. On the magic key it unlocks and leaks `data_in` although the correct key
was never supplied -- violating **P1** and **P2**. Because the trigger is one
value out of 2^32, undirected constrained-random testing has ~0 chance of hitting
it; an assertion/formal check of P1/P2 finds it immediately. That contrast is the
lesson of this track.

## What the smoke test exercises (and what it does NOT)
`test_smoke.py` runs on the **clean** variant. `test_security_property` checks
that wrong keys (including low-half / high-half near-misses, an off-by-one-bit
key, the magic key, and 200 random keys) all keep the gate locked with zero
output, and that the correct key unlocks and passes data. `test_access_count`
checks the counter increments only while unlocked. (Pointing the Makefile's `DUT`
at the trojan variant makes the magic-key vector fail -- a demonstration, not the
intended grading method.)

It is a **bring-up** test. It does not constitute the security proof: catching the
trojan robustly, and closing the released pool `mutants_released.yaml` (7 mutants,
all found by the reference smoke test), is the capstone work (M2-M4). The proper
solution proves P1/P2 formally rather than relying on hitting the trigger by luck.
