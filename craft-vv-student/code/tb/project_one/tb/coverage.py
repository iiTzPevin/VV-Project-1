"""
Small functional-coverage tracker for an 8-entry FWFT FIFO.

Adrian Emeterio - Project 1
"""

class FifoCoverage:
    def __init__( self, depth = 8 ):
        self.depth = depth
        self.levels = { self._level( n ) for n in range( depth + 1 ) }
        self.operations = { "idle", "write", "read", "both" }
        self.events = {
            "write_full", "read_empty", "both_empty", "both_full",
            "both_middle", "write_wrap", "read_wrap",
            "write_during_reset"
        }

        # These requests are handled by the FIFO spec.
        self.ignored_requests = { "write_full", "read_empty" }

        self.hit_levels = set( )
        self.hit_operations = set( )
        self.hit_crosses = set( )
        self.hit_events = set( )
        self.writes = 0
        self.reads = 0

    def _level( self, count ):
        if count == 0:
            return "empty"
        if count == self.depth:
            return "full"
        if count == 1:
            return "near_empty"
        if count == self.depth - 1:
            return "near_full"
        return "middle"

    def sample( self, before, obs, rst_n = 1 ):
        """Sample pre-edge occupancy, requests, and active-low reset."""
        wr, rd = bool( obs.wr_en ), bool( obs.rd_en )

        if not rst_n:
            if wr:
                self.hit_events.add( "write_during_reset" )
            self.writes = 0
            self.reads = 0
            return  # Reset takes priority; no FIFO transaction occurs.
        operation = "both" if wr and rd else "write" if wr else "read" if rd else "idle"
        level = self._level( before )

        self.hit_levels.add( level )
        self.hit_operations.add( operation )
        self.hit_crosses.add( ( level, operation ) )

        if wr and before == self.depth:
            self.hit_events.add( "write_full" )
        if rd and before == 0:
            self.hit_events.add( "read_empty" )
        if wr and rd:
            event = "both_empty" if before == 0 else "both_full" if before == self.depth else "both_middle"
            self.hit_events.add( event )

        # Count accepted transactions to detect pointer wraps.
        if wr and before < self.depth:
            self.writes += 1
            if self.writes % self.depth == 0:
                self.hit_events.add( "write_wrap" )
        if rd and before > 0:
            self.reads += 1
            if self.reads % self.depth == 0:
                self.hit_events.add( "read_wrap" )

    def report( self ):
        all_crosses = { ( level, op ) for level in self.levels for op in self.operations }
        covered = ( len( self.hit_levels ) + len( self.hit_operations )
                   + len( self.hit_crosses ) + len( self.hit_events ) )
        total = len( self.levels ) + len( self.operations ) + len( all_crosses ) + len( self.events )

        return "\n".join( [
            f"FIFO Coverage: {covered}/{total} Bins ({100 * covered / total:.1f}%)",
            f"Occupancy: {len(self.hit_levels)}/{len(self.levels)}",
            f"Operations: {len(self.hit_operations)}/{len(self.operations)}",
            f"Occupancy X Operation: {len(self.hit_crosses)}/{len(all_crosses)}",
            f"Corner Events: {len(self.hit_events)}/{len(self.events)}",
            f"Ignored Requests (Defined By Spec): {sorted(self.hit_events & self.ignored_requests)}",
            f"Reset/Write Overlap: {'Hit' if 'write_during_reset' in self.hit_events else 'Missing'}",
            f"Missing Crosses: {sorted(all_crosses - self.hit_crosses)}",
            f"Missing Events: {sorted(self.events - self.hit_events)}",
        ] )