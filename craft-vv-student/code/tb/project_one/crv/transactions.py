"""
The transaction and constraints for the random FIFO stimulus. Each transaction
is one cycle of inputs. The phase decides if the FIFO should mostly be filling
or mostly be draining.

William Wright - Project 1
"""

import vsc

WIDTH, DEPTH = 8, 8
FILL, DRAIN = 0, 1

@vsc.randobj
class FifoTxn:
    """
    FifoTxn contains the data needed for one cycle of FIFO stimulus.
    Variables are random rather than driven and constrained to fit within the legal bounds of the FIFO spec.
    The phase variable should be updated and set before a randomize call.
    """

    def __init__( self, width = WIDTH ):
        self.phase = vsc.uint8_t( FILL )
        self.roll_w = vsc.rand_uint8_t( )
        self.roll_r = vsc.rand_uint8_t( )
        self.wr_en = vsc.rand_bit_t( 1 )
        self.rd_en = vsc.rand_bit_t( 1 )
        self.wr_data = vsc.rand_bit_t( width )

    @vsc.constraint
    def c_rolls( self ):
        self.roll_w in vsc.rangelist( vsc.rng( 0, 99 ) ) # Uniform rolls.
        self.roll_r in vsc.rangelist( vsc.rng( 0, 99 ) )
        vsc.solve_order( self.roll_w, self.wr_en ) # Solve the roll before the enable so we get the expected probability.
        vsc.solve_order( self.roll_r, self.rd_en )

    @vsc.constraint
    def c_shape( self ):
        # FILL: write 85% of cycles, read 10% (the overlap keeps simultaneous read+write alive).
        with vsc.if_then( self.phase == FILL ):
            with vsc.implies( self.roll_w < 85 ):
                self.wr_en == 1
            with vsc.implies( self.roll_w >= 85 ):
                self.wr_en == 0
            with vsc.implies( self.roll_r < 10 ):
                self.rd_en == 1
            with vsc.implies( self.roll_r >= 10 ):
                self.rd_en == 0
        # DRAIN: the mirror image.
        with vsc.else_then( ):
            with vsc.implies( self.roll_w < 10 ):
                self.wr_en == 1
            with vsc.implies( self.roll_w >= 10 ):
                self.wr_en == 0
            with vsc.implies( self.roll_r < 85 ):
                self.rd_en == 1
            with vsc.implies( self.roll_r >= 85 ):
                self.rd_en == 0

    @vsc.constraint
    def c_data( self ):
        # A top-level dist is honored: 1 in 5 words is an all-zeros or all-ones pattern.
        vsc.dist( self.wr_data, [ vsc.weight( 0, 10 ), vsc.weight( ( 1 << WIDTH ) - 1, 10 ), vsc.weight( vsc.rng( 1, ( 1 << WIDTH ) - 2 ), 80 ) ] )

class Phase:
    """
    The phase state needs to be aware of how long it spends at the corners in order to `dwell` there.
    This class is how it's able to do so.
    """

    def __init__( self, depth = DEPTH, dwell = 3 ):
        self.depth, self.dwell = depth, dwell
        self.phase, self.held = FILL, 0

    def update( self, count ):
        at_corner = ( self.phase == FILL and count == self.depth ) or ( self.phase == DRAIN and count == 0 )
        self.held = self.held + 1 if at_corner else 0
        if self.held > self.dwell:
            self.phase, self.held = ( DRAIN if self.phase == FILL else FILL ), 0
        return self.phase