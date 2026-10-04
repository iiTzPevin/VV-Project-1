# Week 2 · Session 1 — one sentence, two compliant parts

You watched this in class. Here it is again so you can run it yourself.

**What it shows.** An ambiguous requirement is a defect, and it has a witness
vector. Two parts that both satisfy the overflow sentence disagree at
`0x7F + 0x01`. No test written from that sentence can tell them apart.

Run everything from `code/`.

| Step | File | What you should get |
|------|------|---------------------|
| 0 | `step0_two_readings.py` | green — **both readings pass** |
| 1 | `step1_divergence.py` | **red, by design** — 118/272, first witness `0x7F + 0x01` |
| 2 | `step2_sharpened.py` | green, 6/6 |
| — | bridge | **3/8** |

Each step is one command. Here is step 0, in both forms:

```bash
just demo 02 s1 0        # or:  make -C demos/wk02-s1-ambiguity STEP=0
```

Every number below was measured with Icarus at `DEMO_SEED=5`. Steps 0–1 run
the two planted readings in this directory (`alu_pair.sv` wraps
`alu_ovf_signed.sv` and `alu_ovf_carry.sv`). Step 2 runs the course ALU,
`dut/alu.sv`. The bridge score is against `tb/alu/mutants_released.yaml`,
which holds 8 mutants. Captured output for each step is in `expected/`.

---

## Step 0 — read the sentence, and run the test it permits

Open `dut/specs/alu.md` at the Flags section and read this line:
*"overflow — set when the mathematical result of an arithmetic operation
(ADD, SUB) does not fit in WIDTH bits."* Fit **as what**? Signed or unsigned?
The sentence does not say. Both answers got built:

```bash
grep -n "ovf    =" demos/wk02-s1-ambiguity/alu_ovf_signed.sv \
                   demos/wk02-s1-ambiguity/alu_ovf_carry.sv
just demo 02 s1 0
```

The grep is the whole difference between the two parts. Engineer A computes
signed overflow. Engineer B returns the carry bit. Both are faithful to the
sentence.

**You should see:**

```
      a      b   ovf(A: signed)  ovf(B: carry)  expected
   0x03   0x04               0              0         0
   0x80   0x80               1              1         1
   two contradictory implementations, one test: BOTH PASS
```

**What it means.** The test is not wrong. It checked a fits case and the
biggest blow-up anyone thinks of first, and on those vectors the two readings
agree. Nothing on a green screen tells you your requirement has two meanings.

> **Check yourself.** If the sentence meant one thing, could two compliant
> parts disagree anywhere? Answer before you run step 1.

---

## Step 1 — hunt until you get a witness

This step runs the spec's own corner list. Wrap boundaries exactly at and one
either side, sign corners, extremes, plus a corner cross and 200
seeded-random vectors.

```bash
just demo 02 s1 1
```

**You should see:**

```
   0x7f   0x01               1              0   <- DIVERGE
   0xff   0x01               0              1   <- DIVERGE
  readings disagree on 118/272 vectors
AssertionError: one sentence, two compliant parts: readings diverge on
118/272 ADD vectors, first witness a=0x7f b=0x01 -- the defect is in the
spec, not in either part
```

**What it means.** The first probe on the list is the first witness:
`+127 + 1`. Almost half the sweep diverges. This is not a corner case. It is
two different flags wearing one name. Neither part has a bug. The sentence
does. The test stays red on purpose, because there is nothing to fix in RTL.

**The trap.** "So which part is right?" is the wrong question. The sentence
cannot say. Deciding by reading the RTL means the implementation has become
the spec, which is backwards.

> **Check yourself.** Pick any vector from the list that did *not* diverge.
> Say what has to be true about a vector for the two readings to agree on it.

---

## Step 2 — sharpen it until it has a definite expected value

Do the false start first. Write "the ALU handles overflow correctly" on paper
and try to fill in an expected value for `0x7F + 0x01`. You cannot. Now
sharpen it into R-ADD-OVF:

```
R-ADD-OVF: For ADD, `result` = (a + b) mod 2^WIDTH. `overflow` = 1 iff
the SIGNED (two's-complement) sum of a and b lies outside
[-2^(WIDTH-1), 2^(WIDTH-1)-1]. The unsigned does-not-fit fact is a
different flag: `carry` = 1 iff a + b >= 2^WIDTH.
```

Two facts were hiding in one sentence, so the contract needs two flags. The
course spec has both. Derive the coverage points from the requirement: both
wrap boundaries, exactly at and one either side, plus the vectors where the
flags split. Now every row has an answer you can write down **before** you run
anything:

```bash
just demo 02 s1 2
```

**You should see:**

```
      a      b   result  overflow  carry
   0x7f   0x01     0x80         1      0
   0xff   0x01     0x00         0      1
   6/6 definite expected values met -- dut/alu.sv implements the signed reading
```

**What it means.** `0x7F+0x01` overflows with no carry. `0xFF+0x01` carries
with no overflow. A requirement is testable exactly when you can write its
expected value down in advance. A test that pins one reading would have
rejected Engineer B's part before it shipped.

> **Check yourself.** Fill in `result`, `overflow` and `carry` for
> `0x80 + 0xFF` from R-ADD-OVF alone. Then check it against the run.

---

## The bridge into Session 2

Score the sharpened test against the released pool
(`expected/score-bridge.txt` has the transcript):

```
==== found/total = 3/8  =  37.5%  ====
surviving mutants: and2or, xor2and, slt_unsigned, zero_inverted, sll2srl
```

One requirement, sharpened, bought three mutants. The five survivors are not
harder. They are requirements nobody has written rows for yet. Session 2
builds the table that says which rows exist, which are covered, and which are
a risk you are choosing to carry.

---

## If it breaks

| Symptom | Cause | Fix |
|---|---|---|
| `Can not find root handle` after switching steps | a build dir left over from an override | `rm -rf demos/wk02-s1-ambiguity/sim_build_*` — the Makefile keeps one build dir per toplevel |
| Step 1 count differs from 118/272 | seed not pinned — the 200-vector random tail moved | `DEMO_SEED=5` is the default; check nothing exported it. The corner cross diverges regardless, so the witness survives any seed |
| Step 1 passes | you ran it against `dut/alu.sv` via a `DUT=` override | steps 0–1 need the pair; drop the override |
| Step 2 red on clean RTL | a typo in a hand-computed triple | `0x80 + 0xFF` is the one people get wrong: result `0x7F`, both flags set |
| `iverilog: command not found` | wrong shell | `source /opt/course/cocotb-env/bin/activate` |
