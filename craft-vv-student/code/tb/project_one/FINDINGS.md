# FINDINGS — Project #1 — Minh Hoang Ho, Matias Guillen, William Wright, Adrian Emeterio

## Score

| Pool | found | total | % |
|------|------:|------:|--:|
| Released | 8 | 8 | 100% |
| Hidden | — | — | — |

**Command run:**

```bash
$ source /opt/course/cocotb-env/bin/activate
$ cd project_testing/code
$ just mutate project_one
python -m craft_mutate.mutate --tb tb/project_one --pool tb/project_one/mutants_released.yaml --sim icarus
[baseline] running clean fifo.sv through project_one ...
  clean RTL: 11 tests passed.

  [found  ] full_offbyone        (test-failed)  -- full asserts one entry too early (cnt == DEPTH-1)
  [found  ] empty_offbyone       (test-failed)  -- empty asserts one entry too early (cnt == 1)
  [found  ] ignore_full          (test-failed)  -- writes are accepted even when full (overflow)
  [found  ] ignore_empty         (test-failed)  -- reads are accepted even when empty (underflow)
  [found  ] count_wr_dec         (test-failed)  -- a write-only cycle decrements the count
  [found  ] rd_data_wrptr        (test-failed)  -- rd_data reads from the write pointer instead of the read pointer
  [found  ] mem_corrupt          (test-failed)  -- stored data is corrupted (+1) on write
  [found  ] wrptr_wrap_early     (test-failed)  -- write pointer wraps one slot early

==== found/total = 8/8  =  100.0%  (threshold 90%) ====
```

## Survivors

| Mutant | What It Changes | Reachable By My Stimulus? | Observable By My Checks? | Why It Survived |
|--------|-----------------|---------------------------|--------------------------|-----------------|
| Wrong rd_data while empty, not in the pool | The rd_data output shows the wrong value only when the FIFO is empty | Yes | No | We skip checking rd_data when the FIFO is empty since the spec says it is only valid when not empty so this is an observability gap |
| Bug only at a size other than 8, not in the pool | Something like the wrap logic breaking at DEPTH = 16 or WIDTH = 4 | No | Yes | We only test the FIFO at WIDTH = 8 and DEPTH = 8 so a bug that needs another size never happens which makes this a reachability gap |

## What I Changed, And What It Bought

| Change | Score Before | Score After | Which Survivors It Caught |
|--------|-------------:|------------:|---------------------------|
| Went from the starter smoke test to our full suite of 11 tests with the scoreboard checking every cycle | 1 / 8 | 8 / 8 | full_offbyone, empty_offbyone, ignore_full, ignore_empty, rd_data_wrptr, mem_corrupt, wrptr_wrap_early |

## Residual Risk

1. Our code would not catch a wrong rd_data while the FIFO is empty because we never check rd_data when the FIFO is empty which makes this an observability gap.
2. Our code would not catch bugs that only show up at other WIDTH or DEPTH values because we only test the FIFO at 8 and 8 which makes this a reachability gap.
3. Our code would not catch anything that goes wrong before the first reset because every test resets first which makes this a reachability gap.

**If I Had Another Day:** Run all the tests again at a couple other sizes.
