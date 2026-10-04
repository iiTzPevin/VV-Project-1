# FINDINGS — <lab / project> · <your name>

> The number is the start of the argument, not the end of it. This file is
> where you say what the number means and what it does not cover.

## Score

| Pool | found | total | % |
|------|------:|------:|--:|
| released (practice) | | | |
| hidden (reported at grading) | | | |

**Command run:**

```bash
```

## Survivors

One row per mutant your suite did not find. `Reachable?` is the important
column: a survivor you never reached is a *stimulus* problem, a survivor you
reached but did not notice is a *checking* problem, and they have different
fixes.

| Mutant | What it changes | Reachable by my stimulus? | Observable by my checks? | Why it survived |
|--------|-----------------|---------------------------|--------------------------|-----------------|
|        |                 | yes / no                  | yes / no                 |  |

## What I changed, and what it bought

| Change | Score before | Score after | Which survivors it caught |
|--------|-------------:|------------:|---------------------------|
|        |              |             |  |

## Residual risk

What this suite still cannot catch, stated plainly. Name a fault class, not a
mutant id — the pool is a sample, not the population.

1.
2.

**If I had another day:** <the one thing you would do next, and why that one>
