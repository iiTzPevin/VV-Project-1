# Coverage Closure — Project #1 — Minh Hoang Ho, Matias Guillen, William Wright, Adrian Emeterio

## 1. The Number

| Measure | Result |
|---|---|
| Coverpoints that were fully hit | 3 / 3 for occupancy, operations, and corner events |
| Pairs of how full the FIFO was and what it was asked to do | 20 / 20 bins |
| Coverage goal from our vplan | 90% minimum with 100% as the goal |
| Coverage we actually got | 100% with 37 / 37 bins |
| Cycles it took to hit every bin | Not tracked since our coverage file only reports the final result |
| Cycles that kept running after every bin was hit | The whole suite keeps running after closure, which is 9 directed tests, 5 plain random seeds of 400 cycles, and 15 pyvsc seeds of 500 cycles |


**How the report was produced:**

```bash
$ source /opt/course/cocotb-env/bin/activate
$ cd project_testing/code
$ just test project_one icarus
$ cat tb/project_one/coverage_report.txt
FIFO Coverage: 37/37 Bins (100.0%)
Occupancy: 5/5
Operations: 4/4
Occupancy X Operation: 20/20
Corner Events: 8/8
Ignored Requests (Defined By Spec): ['read_empty', 'write_full']
Reset/Write Overlap: Hit
Missing Crosses: []
Missing Events: []
```

## 2. The Convergence Argument

**Shape Of The Curve:** We did not record coverage over time so we do not have a curve, but every bin was hit by the end of the full run.

**The Last Bins To Close, And What It Took:** We did not record which bins closed last. These are the hardest bins to reach and what hits them.

| Bin | Why It Was Rare | What I Changed To Hit It |
|-----|-----------------|--------------------------|
| Idle at full and idle at empty | Both wr_en and rd_en have to be 0 while the FIFO is sitting at full or empty | Both the fill and drain phases only write or read part of the time so some cycles have neither and the Phase class keeps the FIFO at full or empty for a few cycles before switching |
| Both at full and both at empty | Both enables have to be on while the FIFO is full or empty | The overlap in each phase keeps reading and writing while the Phase class holds the FIFO at the edge |
| Write during reset | Reset has to be on while wr_en is held high and this never happens in normal random cycles | A directed test because random stimulus never turns on reset so test_reset_in_use holds the enables high during reset on purpose |
| Write wrap and read wrap | The pointers only wrap after 8 writes or reads in a row since the last reset | test_wrap starts from every spot and the fill and drain phases push 8 or more writes and reads through before switching |

**Why I Stopped Where I Stopped:** All 37 bins were hit so the model was finished and the rest of the regression keeps running after that so a bad value written early could still get caught when it was read back out later

## 3. Bin Justification

| Bin | Illegal / Ignore | The Claim | Authority (Spec Line, Or The Argument) |
|-----|------------------|-----------|----------------------------------------|
| None | None | Everything done is legal no matter how full the FIFO is | The spec's write rule, read rule, and simultaneous read and write rule cover each request and even writing while full and reading while empty should follow the spec |

**Corner Bins That Are Legal And Must Be Covered, Not Excluded:** Writing while full and reading while empty are both legal since the spec says the write gets dropped and the read gets ignored. The coverage report lists these as ignored requests but that only means the FIFO ignores them, and they are still counted and were both hit.

## 4. What The Cross Is Aimed At

**The Bug The Occupancy X Operation Cross Is Aimed At:** It is aimed at bugs that only happen at the edges like the full flag turning on one entry too early or the FIFO accepting a write when it is already full because these bugs only show up when the FIFO is asked to do something while it is full or empty

**A Bug It Would *Not* See, Even Fully Closed:** It would not see wrong data because the cross only tracks how full the FIFO was and what it was asked to do, not whether the value that came out was correct, which is what the scoreboard checks

## 5. Coverage VS. Correctness — The Blind Spots

1. **The Data Values:** Coverage only records that a write happened, not what data was written so a FIFO that corrupts its data could still hit every bin and only the scoreboard would catch it.
2. **Where The Pointers Are:** The FIFO can hold 4 entries with the pointers sitting at any of the 8 spots and the coverage does not track which spots were used so test_wrap covers this by starting from every spot.
3. **Other WIDTH And DEPTH Values:** The coverage bins are only built for the 8 deep FIFO so a bug that only happens at a different size would never show up.

**Transients In Particular:** Our model would miss a glitch where an output is wrong for a moment and then goes back to the right value because we only read the outputs once right after each clock edge. To catch this, we would need a check in the middle of the cycle or call an assertion inside the RTL.

## 6. Correlation With Mutation

Cross-reference `FINDINGS.md`. The interesting case is divergence.

| | found / total |
|---|---|
| Before closing holes | Not measured since coverage was already at 100% on the first full run |
| After closing holes | 8 / 8 |

**Did Closing Holes Raise The Score?** We did not have any holes left to close on our full run since all 37 bins were hit and all 8 released mutants were found so the coverage and the mutation score agree.

---

- [ X ] Every `illegal` and `ignore` bin in section 3 cites an authority.
- [ X ] Section 5 names blind spots of this design, not of coverage in general.
- [ X ] The numbers here agree with `coverage_report.txt` and `FINDINGS.md`.
