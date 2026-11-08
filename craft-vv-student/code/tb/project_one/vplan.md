# Verification Plan — Project #1

**Author:** Minh Hoang Ho, Matias Guillen, William Wright, Adrian Emeterio **Spec Version:**  20260831 REV 8B9D934 2026-08-31 **Date:** 11-04-2026

## 1. Scope

**In Scope:** We are testing the FIFO at its default size, with WIDTH = 8 and DEPTH = 8. This will cover reset, normal writes and reads, writing while the FIFO is full, reading while it is empty, and reading and writing at the same time. We also check the full and empty flags, the count, the head showing on rd_data, pointer wrap, and that data comes out in the same order it went in.

**Out Of Scope:** We are not testing other WIDTH and DEPTH values. We also are not testing the almost_full flag or the optional FWFT mode from the project page.

**Assumptions About The Environment:** The FIFO runs on a single 10 ns clock. Inputs change on the falling edge, and outputs are read right after the rising edge. Every test starts with a reset. Any mix of wr_en and rd_en counts as a legal input since the spec says what happens for all of them, even overflow and underflow.

## 2. Feature list

| ID | Feature | Req | Priority | How It Is Verified |
|----|---------|-----|----------|--------------------|
| F1 | Reset clears the FIFO so count goes to 0, empty goes to 1, and full goes to 0 | Reset rule | H | Directed tests and checks on every reset cycle |
| F2 | A write happens when wr_en is 1 and the FIFO is not full | Write rule | H | Directed tests and CRV |
| F3 | A write while the FIFO is full gets dropped and does not corrupt any data | Write rule | H | Directed tests and CRV |
| F4 | A read happens when rd_en is 1 and the FIFO is not empty | Read rule | H | Directed tests and CRV |
| F5 | A read while the FIFO is empty gets ignored so count never goes below 0 | Read rule | H | Directed tests and CRV |
| F6 | When the FIFO is not empty rd_data always shows the head | Read rule and ports table | H | Scoreboard checks every cycle |
| F7 | Reading and writing at the same time keeps the count the same, but at full only the read happens and at empty only the write happens | Write, read, and simultaneous read and write rules | H | Directed tests and CRV |
| F8 | The full flag is 1 only when count is DEPTH and the empty flag is 1 only when count is 0 | Flags rule | H | Scoreboard checks every cycle |
| F9 | Data comes out in the same order it went in | Ordering rule | H | Scoreboard checks every cycle and CRV |
| F10 | Both pointers wrap around correctly no matter where they start | Corner cases list | M | Directed tests and CRV |
| F11 | Every data bit can be stored and read back as both a 0 and a 1 | Parameters (WIDTH) | M | Directed tests |
| F12 | Reset still clears the FIFO even when wr_en or rd_en is held high during reset | Reset rule | M | Directed tests |

## 3. Coverage Model

| ID | Coverpoint | Bins | Why These Bins |
|----|-----------|------|----------------|
| C1 | How full the FIFO is before the cycle | Empty at 0, near empty at 1, middle from 2 to 6, near full at 7, and full at 8 | Most FIFO bugs happen right at the edges so 0, 1, 7, and 8 each get their own bin while 2 to 6 act the same and share one |
| C2 | What the FIFO was asked to do that cycle | To stay idle, write, read, or both | These are the only 4 possible options of wr_en and rd_en |
| C3 | Reset while an enable is held high | Write held during reset | Reset has to clear the FIFO even if a write is requested at the same time and this is our check for an illegal input |
| C4 | Corner events | Write while full, read while empty, both at empty, both at full, both in the middle, write pointer wrap, read pointer wrap, and write during reset | These are the spots where FIFO bugs usually hide so each one gets its own bin |

**Crosses**

| ID | Cross | The Interaction It Is Aimed At |
|----|-------|-------------------------------|
| X1 | C1 crossed with C2 for 20 bins | Bugs that only show up at the edges like writing while full to check for overflow, reading while empty to check for underflow, and reading and writing together at full or empty where the FIFO could accept something it should not |

**Illegal / Ignore Bins:** There should be none because the spec says what happens for every mix of wr_en and rd_en at every level so even writing while full and reading while empty are legal and every bin should be hit

## 4. Test matrix

| Test | Features | Kind | Pass criterion |
|------|----------|------|----------------|
| test_smoke | F2 | Directed | The count is 3 after three writes which is the starter test |
| test_reset | F1, F2 | Directed | The FIFO is empty after reset and stays empty when wr_data changes while wr_en is low |
| test_fill_drain | F2, F4, F8, F9, F10 | Directed | The FIFO fills to full and drains to empty twice with every output matching the model |
| test_overflow | F3, F8 | Directed | The count stays at DEPTH and none of the dropped values ever come out |
| test_underflow | F5, F8 | Directed | The count stays at 0 and the next value written is still the head |
| test_read_write | F7 | Directed | The count does not change in the middle, only the write happens at empty and only the read happens at full |
| test_wrap | F9, F10 | Directed | The FIFO fills and drains from every starting spot from 0 to 7 with every output matching the model |
| test_all_bits | F6, F11 | Directed | For all 0s and all 1s, alternating bits, and one bit on or one bit off patterns all come back out the same |
| test_reset_in_use | F1, F12 | Directed | The FIFO is empty during and after reset with the enables held high and the old data is gone |
| test_simple_random | F2, F3, F4, F5, F6, F7, F8, F9, F10 | Random | 5 seeds of 400 cycles each with plain Python random and no mismatches |
| test_seeded_regression | F2, F3, F4, F5, F6, F7, F8, F9, F10 | Random with pyvsc | 15 seeds of 500 cycles each with constrained random and no mismatches |

## 5. Risk and spec ambiguity

| # | Ambiguity Or Risk | Where In The Spec | How I Resolved It | Residual |
|---|-------------------|-------------------|-------------------|----------|
| 1 | The spec only says rd_data is valid when the FIFO is not empty | The rd_data row in the table of signals in fifo.md | We only check rd_data when the FIFO is not empty | A bug that only changes rd_data while the FIFO is empty would not get caught |
| 2 | Both WIDTH and DEPTH can be changed but we only test them at 8 | The Parameters section of fifo.md | We only test the default size | Bugs that only show up at other sizes would not get caught |
| 3 | The reference model was written to match the RTL so a mistake in the RTL could also be in the model | The comment at the top of fifo_model.py | The model should be correct after checking it against the spec | Low |
| 4 | The spec does not say what the outputs are before the first reset | The reset rule in fifo.md | Every test resets first and nothing is checked before that | Power up behavior is not verified |

## 6. Closure criteria

- Functional Coverage Target: **90%/100%**
- Mutation Target: **7/8**
- Assertions: We did not use SVA since our scoreboard checks count, full, empty, and rd_data against the reference model on every cycle
- What I Will Report As **Not Verified**: The almost_full flag and FWFT mode, any WIDTH or DEPTH other than 8, rd_data while the FIFO is empty, and anything before the first reset