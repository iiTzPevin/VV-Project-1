# AI Log — Project #1

## Entry #1

**Prompt For Claude Opus 5.5:**

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

**Output For Claude Opus 5.5:**

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

**Prompt For Claude Opus 5.5:**

```text
Can you make me a Python file that generates a graph? It needs to be a simple line graph of coverage versus transactions for seed 42 over 500 cycles. The x-axis should be transactions (cycles) and the y-axis should be bins hit out of 37.

```

**Output For Claude Opus 5.5:**

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