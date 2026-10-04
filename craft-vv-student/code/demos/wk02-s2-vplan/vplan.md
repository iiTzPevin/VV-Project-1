# ALU mini vplan — built live in Week 2, Session 2

The five columns are the HW2 template's columns. VP-1 is the row we derive on
screen, start to finish; VP-2 and VP-3 follow the same pattern faster; VP-4
and VP-5 arrive in the We Do; VP-6 is the risk row that earns its place with
no test at all. Spec: `dut/specs/alu.md`. Tests: this directory,
`step1_traceable.py` and `step2_plan_complete.py`.

| ID | Requirement (sharpened) | Feature / coverage points | Test (traces to) | Risk — why a bug here matters |
|----|-------------------------|---------------------------|------------------|-------------------------------|
| VP-1 | ADD: `result = (a+b) mod 2^WIDTH`; `overflow` = signed sum outside `[-2^(WIDTH-1), 2^(WIDTH-1)-1]`; `carry` = `a+b >= 2^WIDTH` | Wrap boundaries, exactly at and one either side, signed and unsigned; equal operands; overflow-without-carry and carry-without-overflow both witnessed | `test_vp1_add_flags` | Tuesday's session in one row: two teams read the old overflow sentence two ways and both shipped. Silent wrong arithmetic corrupts every consumer downstream. |
| VP-2 | SLT: `result = 1` iff `a < b` comparing both as **signed** two's-complement | One negative operand, both orders; sign corners `0x7F`/`0x80`; equal operands | `test_vp2_slt_signed` | An unsigned comparison passes every positive-operand test and decides branches wrong the first time a negative value arrives. |
| VP-3 | `zero` = 1 iff `result` is all zeros, updated by **every** operation | Zero asserted and deasserted; at least 5 distinct ops asserting it | `test_vp3_zero_flag` | Flags feed control flow. The check is a relation between two outputs, so it rides along free on any vector — cheap coverage, high consequence. |
| VP-4 | AND/OR/XOR: bitwise per truth table; `carry = overflow = 0` | Overlapping, disjoint, all-zero masks; equal operands (`a^a`, `a&a`) | `test_vp4_logical_ops` | Added in the We Do. A wrong gate is the easiest bug to find and the most embarrassing to miss — it survived step 1 because no row asked. |
| VP-5 | SLL/SRL: shift by `b[2:0]` only; vacated bits 0; upper bits of `b` ignored (`b = 8'd9` shifts by 1) | Shift by 0, by `WIDTH-1`, by `b >= WIDTH`; a walked bit each direction | `test_vp5_shifts` | Added in the We Do. The `b >= WIDTH` case is where the spec surprises people — untested, it becomes an off-by-eight waiting for software. |
| VP-6 | Undefined opcodes: the spec reserves behavior for "opcodes not listed" | — none reachable: `op` is 3 bits and the table lists all 8 encodings | — (no test can reach it) | The sentence is dead letter **today**; the row records why, so the RTL's unreachable `default` branch is never trusted and the day `op` widens this becomes a planned hole, not a surprise. Unspecified behavior is attacker-specified behavior — Week 8 makes that precise. |

Two readings of the same table:

- **Forward:** every requirement row names the test that covers it, or says
  why none can. A row with a blank test column and no reason is unfinished
  work, visible at a glance.
- **Backward:** every test in the suite names its row. A test no row claims
  is scope creep or a misunderstanding — either way, a finding.

The scoreboard for this plan is the released mutant pool
(`tb/alu/mutants_released.yaml`): step 1's three rows found 5/8, and the three
survivors — `and2or`, `xor2and`, `sll2srl` — sat exactly in the rows not yet
written. The plan predicted the score before the harness reported it.
