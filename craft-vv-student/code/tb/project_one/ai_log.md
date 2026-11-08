# AI Log — Project #1

## Entry #1

**Prompt For Claude:**

```text
Here are all our python files

 - test_fifo.py
 - coverage.py
 - driver.py
 - monitor.py
 - scoreboard.py
 - seeded_regression.py
 - transactions.py

Can you check it and change any files so they work with each other?
```

**Output For Claude:**

```text
All the files work togetehr, but I had to rebuilt seeded_regression.py. The rest of the files didn’t need any changes.

What changed in seeded_regression.py

The file handles the switching itself: Phase starts in fill and flips to drain after the FIFO has stayed full for a few cycles, then back again at empty. So I removed the old four-option picking (FILL/DRAIN/BOTH/FREE, the weights, and the cycle countdown).
```

```python
import random

from crv.transactions import FifoTxn, Phase

SEEDS = [ 1, 2, 3, 7, 13, 42, 99, 256, 1234, 2026 ]
CYCLES = 500 # Cycles per seed.

async def run_seed( drv, mon, model, seed, run_cycle ):
    """
    Runs all the random cycles for one seed.
    """

    random.seed( seed ) # Makes the run repeatable since pyvsc uses Python's random.
    txn = FifoTxn( ) # The random transaction.
    phase = Phase( ) # Keeps track of whether it should be filling or draining.

    for i in range( CYCLES ):
        txn.phase = phase.update( model.count ) # Switches between filling and draining at full and empty.
        txn.randomize( )
        await run_cycle( drv, mon, model, int( txn.wr_en ), int( txn.rd_en ), int( txn.wr_data ) )
```

---

## Entry #2

**Prompt For Claude:**

```text
Can you make me a Python file that generates a graph? It needs to be a simple line graph of coverage versus transactions for seed 42 over 500 cycles. The x-axis should be transactions (cycles) and the y-axis should be bins hit out of 37.

```

**Output For Claude:**

```python
import ast
import random
import re

from crv.transactions import FifoTxn, Phase
from crv.seeded_regression import CYCLES
from tb.coverage import FifoCoverage
from models.fifo_model import FifoModel

DEPTH = 8
SEED = 42 # Seed used for Figure 2.

class Obs:
    def __init__( self, wr_en, rd_en ):
        self.wr_en = wr_en
        self.rd_en = rd_en

def read_report( cov ):
    text = cov.report( )
    hit, total = re.search( r"(\d+)/(\d+)", text ).groups( )
    missing = set( )
    for line in text.splitlines( ):
        if line.lower( ).startswith( ( "missing crosses", "missing events" ) ):
            missing |= set( map( str, ast.literal_eval( line.split( ":", 1 )[ 1 ].strip( ) ) ) )
    return int( hit ), int( total ), missing

random.seed( SEED ) # Same order as the real test so the cycles match.
txn = FifoTxn( )
phase = Phase( )
model = FifoModel( )
cov = FifoCoverage( DEPTH )
hit, total, missing = read_report( cov )
xs, ys, closed = [ 0 ], [ hit ], [ ]

for i in range( CYCLES ):
    txn.phase = phase.update( model.count )
    txn.randomize( )
    wr, rd = int( txn.wr_en ), int( txn.rd_en )
    cov.sample( model.count, Obs( wr, rd ) )
    model.step( wr, int( txn.wr_data ), rd )
    new_hit, total, new_missing = read_report( cov )
    if new_hit != hit:
        closed.append( ( i + 1, new_hit, sorted( missing - new_missing ) ) )
    hit, missing = new_hit, new_missing
    xs.append( i + 1 )
    ys.append( hit )

print( "seed", SEED, "cycles", CYCLES, "final", hit, "of", total )
print( "cycle, bins hit, bins that closed on that cycle" )
for c in closed:
    print( c[ 0 ], c[ 1 ], c[ 2 ] )
print( "still missing", sorted( missing ) )

try:
    import matplotlib
    matplotlib.use( "Agg" )
    import matplotlib.pyplot as plt
except ImportError:
    print( "matplotlib is not installed so no picture was saved, paste the lines above instead" )
else:
    fig, ax = plt.subplots( figsize = ( 7, 3.4 ) )
    ax.step( xs, ys, where = "post", color = "#1f4e9c", lw = 1.8, label = "Bins hit by seed " + str( SEED ) )
    ax.axhline( total, color = "#888888", ls = "--", lw = 1 )
    ax.text( CYCLES, total + 0.4, str( total ) + " bins total", ha = "right", va = "bottom", fontsize = 8, color = "#555555" )
    late = closed[ -4: ] # Number the last few holes that closed and list them in a key.
    key = [ ]
    for j in range( len( late ) ):
        c = late[ j ]
        names = [ n.strip( "()" ).replace( "'", "" ).replace( ", ", " x " ) for n in c[ 2 ] ]
        ax.plot( c[ 0 ], c[ 1 ], "o", color = "#c0392b", ms = 4 )
        ax.annotate( str( j + 1 ), ( c[ 0 ], c[ 1 ] ), textcoords = "offset points", xytext = ( 0, -11 ), ha = "center", fontsize = 8, color = "#c0392b", weight = "bold" )
        key.append( str( j + 1 ) + ".  Cycle " + str( c[ 0 ] ) + ": " + ", ".join( names ) )
    if missing:
        key.append( "Not hit by this seed: " + ", ".join( sorted( missing ) ) )
    ax.text( 0.97, 0.06, "\n".join( key ), transform = ax.transAxes, ha = "right", va = "bottom", multialignment = "left", fontsize = 7.5,
        bbox = dict( fc = "white", ec = "#cccccc", boxstyle = "round,pad=0.4" ) )
    ax.set_xlim( 0, CYCLES )
    ax.set_ylim( 0, total + 3 )
    ax.set_xlabel( "Transactions (cycles)" )
    ax.set_ylabel( "Bins hit" )
    ax.grid( alpha = 0.3 )
    fig.tight_layout( )
    fig.savefig( "fig2_coverage.png", dpi = 200 )
    print( "saved fig2_coverage.png" )
```

## Entry #3

**Prompt For Claude:**

```text
Explain the section of this PowerPoint on verification of digital systems using cocotb that mentions phase and hysteresis. What is phase used for? What do drift + 0.75 and drift - 0.75 mean?

- bonus-crv-s2-slides.ppx
```

**Output For Claude:**

```text
These three slides (10–12) cover the FIFO stimulus design. Phase is the piece that makes the constrained-random stimulus reach the full and empty corners of the FIFO.

What phase is for

phase is a mode flag that can be FILL or DRAIN. It chooses which set of bias constraints applies on the current cycle:

FILL: P(write) = 0.85, P(read) = 0.10, so the FIFO tends to fill up.
DRAIN: P(write) = 0.10, P(read) = 0.85, which is the mirror image, so it tends to empty.

Slide 10’s main point is that phase is not declared rand. The solver never chooses its value. The driver (testbench code that runs between transactions) sets phase before every randomize() call, and the constraints only read it. This matters for two reasons:

The solver has no memory. Each randomize() call is independent, so on its own the solver can’t follow a plan like “keep filling until full, wait there, then drain.” The driver can keep that state across cycles.
It keeps the probabilities honest. If phase were a random variable, the solver would treat it as one more thing to solve. Slides 16–17 show how that distorts the rates (0.73 measured where 0.85 was written). Keeping phase out of the solver is why slide 12 measures 0.85/0.10, exactly what was specified.
What “drift +0.75” and “drift −0.75” mean

Drift is the expected change in FIFO occupancy per cycle in each phase. Each cycle, occupancy changes by:

+1 if there’s a write and no read
−1 if there’s a read and no write
0 if there are both or neither

So the expected change is:

E[Δ] = P(wr)(1 − P(rd)) − P(rd)(1 − P(wr)) = P(wr) − P(rd)

(The “both” terms cancel.) Plugging in the numbers:

FILL: 0.85 − 0.10 = +0.75. On average occupancy climbs about ¾ of an entry per cycle, so an 8-deep FIFO goes from empty to full in roughly 8 / 0.75 ≈ 11 cycles.
DRAIN: 0.10 − 0.85 = −0.75. It falls just as fast. Slide 12’s live run measured 0.10 − 0.86 = −0.76.

If you plot occupancy over time, it ramps up, flattens, ramps down, flattens, and repeats. That’s the “sawtooth” in the slide title.

Where hysteresis comes in

The question is when the driver flips the phase. The slides compare two policies:

Bounce (Tuesday’s policy): flip as soon as occupancy gets near the corner. Slide 26 shows that at occupancy 7 the biases have already turned around, so the walk reverses one entry before reaching full. It almost never arrives: 3 cycles at full in a 3,000-cycle run.
Hysteresis with dwell: only flip after the FIFO has sat at the target corner (full or empty) for 3 cycles. This produced 519 cycles at full in the same 3,000-cycle run.

The point of dwelling is what happens while the FIFO is parked at a corner. In FILL at full, the 85% write rate keeps trying to write, so the RTL’s “drop writes when full” gating gets exercised. In DRAIN at empty, reads while empty test the “ignore reads when empty” logic. That’s what slide 11’s key insight means by “dwell is what turns a visit into a test.” Just touching a corner for one cycle barely tests anything.

The slide-12 counter wr_while_full=43 is measuring exactly these events.
```

---

## Entry #4

**Prompt For Claude:**

```text
Explain the use of rolls and if then over vsc.dist with weights.
```

**Output For Claude:**

```text
These are Part 3 of the deck (slides 14–18) plus the HW5 slides (24–25). The short version: a vsc.dist placed inside an if_then doesn’t do what it looks like it does. The deck’s fix is to turn each weight into a threshold on a uniform random number (a “roll”) and use hard constraints instead.

The problem: a dist under a guard

You’d naturally write the HW5 recipe like this (slide 25, left side):
```

```python
with vsc.if_then(self.count <= 1):
    vsc.dist(self.wr_en, [vsc.weight(1, 5), vsc.weight(0, 1)])
with vsc.else_if(self.count >= DEPTH - 1):
    vsc.dist(self.wr_en, [vsc.weight(1, 1), vsc.weight(0, 2)])
```

```text
The intent is “near empty, write 5:1. Near full, write 1:2.” Per the SystemVerilog LRM, that’s what should happen: the guard gates the dist. But the measurements show that in pyvsc 0.9.5, a dist ignores the if_then around it. Every branch’s dist applies on every draw, and they blend together:

Slide 16: 9:1 in one branch and 1:9 in the other cancel out to about a coin flip (0.49 / 0.50) in both phases.
Slide 24: the three HW5 branches blend to about 0.64 everywhere, whatever the count. “Flat is the tell.”

Verilator is no better. It drops dist entirely and prints a CONSTRAINTIGN warning (slide 15).

The worst part is that nothing errors out. It solves fine and shapes nothing. The homework still passes, because 3,000 roughly uniform cycles wander everywhere eventually, but you don’t get the boundary bias you wrote.

The key observation: hard constraints under a guard do work

Slide 16 notes that pyvsc gates hard constraints (like == or implies) correctly. So the trick is to express the probability without dist:

Add a rand “roll” variable, constrained to be uniform over 0–99.
Turn the weight into a threshold. Weight w₁:w₀ means P(1) = w₁/(w₁+w₀), so:
5:1 → 5/6 ≈ 83% → roll < 83
1:2 → 1/3 ≈ 33% → roll < 33
Under the guard, use a hard constraint that ties the enable to the roll:
```

```python
with vsc.if_then(self.count <= 1):
    self.wr_en == (self.roll_w < 83)
```

```text
The randomness now comes entirely from the roll, which is uniform. The guard only chooses which threshold applies, and that kind of hard implication is something the solver does honor. On slide 24 this restores 0.82 / 0.32 at count 0, against an intended 0.83 / 0.33.

You saw the same pattern in AluTxn (slide 6, where one roll picks the operand class) and FifoTxn (slide 10, where the roll sets wr_en according to the phase).

The second catch: solve the roll first

Rolls alone only get you partway. Slide 17 shows a 90% intent coming out as 0.73 without one more line:

python
vsc.solve_order(self.roll, self.wr)   # SV: solve roll before wr;

If roll and wr are solved together, pyvsc treats (roll, wr) as one solution set. Its solver doesn’t sample uniformly over that set, so the value it picks for wr pulls the roll away from uniform, toward 50/50. Solving the roll first locks in a uniform roll, and then the implication simply follows from it. That one line moves the result from 0.73 to 0.90 (slide 18, rows 3 and 4).

An even sturdier option is to draw the roll outside the solver, with random.randrange(100) in Python or $urandom_range(99) in SystemVerilog, and pass it in as a non-rand field. That measured 0.91 / 0.10. It’s the same idea as phase from the last question: anything the solver doesn’t choose, it can’t distort.

Summary of slide 18’s comparison (intended 0.90 / 0.10)
Approach	Measured
dist inside implies	0.49 / 0.50 (broken)
dist inside if_then / else	0.50 / 0.51 (broken)
roll + implications	0.73 / 0.25 (partway)
+ solve_order(roll, wr)	0.90 / 0.09 ✓
roll from random.randrange	0.91 / 0.10 ✓

The course’s rule (slide 16 notes): use dist only at the top level. Under a guard, use a roll plus hard implications, and solve the roll first. The broader habit from slide 18 is to measure the induced rates with the probe any time you change constraints, because the same constraint text gives different distributions in different tools.
```

## Entry #5

**Prompt For ChatGPT:**

```text
I have an existing test_fifo.py that contains my FIFO driver, monitor, and scoreboard. Can you separate the scoreboard and functional coverage into two independent Python files named scoreboard.py and coverage.py?

Make sure both files work with my existing FIFO testbench and reference model. Keep the implementations simple, readable, and avoid unnecessary complexity or changes to the existing verification logic.
```

**Output For ChatGPT:**

```python
from models.fifo_model import FifoModel

class FifoScoreboard:
    def __init__(self):
        self.model = FifoModel()

    def check(self, obs):
        self.model.step(obs.wr_en, obs.wr_data, obs.rd_en)

        assert obs.count == self.model.count
        assert obs.full == self.model.full
        assert obs.empty == self.model.empty

        if not self.model.empty:
            assert obs.rd_data == self.model.head
```

---

## Entry #6

**Prompt For ChatGPT:**

```text
Review my existing coverage.py against the Project 1 FIFO verification requirements.

Add a reset/control corner case to detect a write request during reset. Also clarify which FIFO control combinations are ignored by the specification rather than considered illegal.

Keep the existing occupancy, operation, cross-coverage, and corner-event tracking. Make only the necessary changes and keep the code simple.
```

**Output For ChatGPT:**

```python
self.events = {
    "write_full", "read_empty",
    "both_empty", "both_full",
    "both_middle", "write_wrap",
    "read_wrap", "write_during_reset"
}

self.ignored_requests = {"write_full", "read_empty"}
```

```python
def sample(self, before, obs, rst_n=1):
    wr = bool(obs.wr_en)
    rd = bool(obs.rd_en)

    if not rst_n:
        if wr:
            self.hit_events.add("write_during_reset")

        self.writes = 0
        self.reads = 0
        return
```

---

## Entry #7

**Prompt For ChatGPT:**

```text
Modify my existing test_fifo_integrated.py to work with the updated coverage.py and scoreboard.py.

Make sure coverage is collected after every checked FIFO transaction. Add a test that asserts a write request during reset, verifies the FIFO remains empty, and records the new reset coverage event.

Preserve my existing directed tests and scoreboard checks. Also print the final functional coverage results and save them to coverage.txt so they can be used in the project report.
```

**Output For ChatGPT:**

```python
before = scoreboard.model.count

scoreboard.check(obs)
coverage.sample(before, obs)
```

```python
coverage.sample(0, reset_obs, rst_n=0)
```

```python
report = coverage.report()
print(report)

with open("coverage.txt", "w") as f:
    f.write(report + "\n")
```