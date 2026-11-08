"""
Check the FIFO against the provided reference queue model.

Adrian Emeterio - Project 1
"""

from models.fifo_model import FifoModel

class FifoScoreboard:
    def __init__( self ):
        self.model = FifoModel( )

    def check( self, obs ):
        # Update the reference queue for this clock edge.
        self.model.step( obs.wr_en, obs.wr_data, obs.rd_en )

        assert obs.count == self.model.count, (
            f"count: expected {self.model.count}, got {obs.count}"
        )
        assert obs.full == self.model.full, (
            f"full: expected {self.model.full}, got {obs.full}"
        )
        assert obs.empty == self.model.empty, (
            f"empty: expected {self.model.empty}, got {obs.empty}"
        )

        # In FWFT mode the output always shows the first queued item.
        if not self.model.empty:
            assert obs.rd_data == self.model.head, (
                f"rd_data: expected {self.model.head}, got {obs.rd_data}"
            )