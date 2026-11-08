"""
Seeded regression for the pyvsc transactions. Same seed gives the same cycles
every time.

It starts out filling the FIFO. Once the FIFO stays full for a few cycles it
switches to draining. Once it stays empty for a few cycles it switches back to
filling.

Minh Hoang Ho - Project 1
"""

import random

from crv.transactions import FifoTxn, Phase

SEEDS = [ 1, 2, 3, 7, 13, 42, 99, 256, 453, 783, 923, 1234, 2026, 4215, 8923 ]
CYCLES = 500 # Cycles per seed.

async def run_seed( drv, mon, sb, seed, run_cycle ):
    """
    Runs all the random cycles for one seed.
    """

    random.seed( seed ) # Makes the run repeatable since pyvsc uses Python's random.
    txn = FifoTxn( ) # The random transaction.
    phase = Phase( ) # Keeps track of whether it should be filling or draining.

    for i in range( CYCLES ):
        txn.phase = phase.update( sb.model.count ) # Switches between filling and draining at full and empty.
        txn.randomize( )
        await run_cycle( drv, mon, sb, int( txn.wr_en ), int( txn.rd_en ), int( txn.wr_data ) )