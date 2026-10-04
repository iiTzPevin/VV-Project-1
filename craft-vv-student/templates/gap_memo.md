# Verification-gap memo — <DUT> · <your name>

<!-- HW1, Task 2. One page. Copy this file to the root of your submission as
     gap_memo.md and fill it in. Delete every comment block before you submit. -->

> A green test tells you the design did not fail *the thing you checked*. This
> memo is where you say what you did not check, and why it stayed out of reach.
> Naming your own blind spot is the first verification skill in the course.

## 1. The bug class the provided test cannot catch

<!-- A CLASS of bug, not one typo. "Line 33 has a + where a - belongs" is an
     instance; "sign-overflow on ADD is never distinguished from carry-out" is
     a class. Read code/dut/alu.sv and the provided directed test first. -->

**The class:**

**Where it would live in `alu.sv`:**

## 2. Why the test cannot catch it

Pick exactly one and delete the other. If you believe it is both, say which one
you would have to fix *first* to catch the bug, and argue for that one.

- [ ] **Controllability failure** — the stimulus never drives the design into
      the condition where the bug manifests.
- [ ] **Observability failure** — the design *does* enter the buggy condition,
      but the wrong value never reaches an output the test checks.

**The argument:**

<!-- Tie it to the actual test. Which vectors does it drive? Which outputs does
     it compare? The gap lives in the difference between those two lists. -->

## 3. The concrete example

| | |
|---|---|
| Inputs (`a`, `b`, `op`) | |
| What the design would produce with the bug | |
| What the golden model says | |
| Does the provided test drive these inputs? | yes / no |
| Does it check the output that differs? | yes / no |

**One vector that would close the gap:**

<!-- If yours is an observability failure, the fix is usually a check you are
     not making, not a vector you are not driving. Say which. -->

## 4. What this does NOT verify

<!-- REQUIRED, and graded as its own row. A generic disclaimer — "this test is
     not exhaustive", "more testing is needed" — scores nothing. Name specific
     behaviors of THIS design that the sanity test leaves untouched, and for
     each one say why it stays out of the test's reach. Three or four is
     plenty; make each one load-bearing. -->

The passing sanity test establishes nothing about the following, because:

1. **<behavior>** — <why it is out of reach: never driven / never checked>
2. **<behavior>** — <...>
3. **<behavior>** — <...>

---

## Evidence

**Transcript of the green run** (`just test alu`) is submitted alongside this
memo — paste the `TESTS=… PASS=…` banner here as well:

```text
```

- [ ] The bug class in section 1 is a class, not a single instance.
- [ ] Section 2 commits to one failure mode and argues for it.
- [ ] Section 4 names specific behaviors of this design, not testing in general.
