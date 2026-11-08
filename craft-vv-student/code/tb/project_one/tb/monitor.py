"""
The monitor reads the FIFO's signals and puts them into a record.
"Passive" means it observes signals without driving or changing them.
The test calls capture() after each driver transaction.

Matias Guillen - Project 1
"""

from dataclasses import dataclass
from typing import Optional

@dataclass
class Observed:
    """
    A snapshot of the input pins and resulting FIFO outputs.
    """

    cycle: int # Observation number, monitoring starting at 1.
    wr_en: int # Write request read from the input pin.
    rd_en: int # Read request read from the input pin.
    wr_data: int # Write data read from the input pin.
    count: int # Number of stored items reported by the FIFO.
    full: bool # True when the FIFO reports that it is full.
    empty: bool # True when the FIFO reports that it is empty.
    rd_data: Optional[int] # Current head data, or none when reported empty.

class FifoMonitor:
    """
    A passive monitor that observes the FIFO's input and output pins.
    """

    def __init__( self, dut ):
        """
        Start observation counter at 0 and store the FIFO's DUT.
        """

        self.dut = dut # Saves access to simulated FIFO.
        self.cycle = 0 # Starts counter at 0.

    def capture( self ):
        """
        Take one snapshot of FIFO. Runs on mon.capture() call after each driver transaction.
        """

        d = self.dut
        self.cycle += 1 # Increments the observation counter.
        empty = bool( int( d.empty.value ) ) # Convert the FIFO's empty signal.

        return Observed( # Return a record of the FIFO's state.
            cycle = self.cycle, # Counter of how many times the FIFO has been observed.
            wr_en = int( d.wr_en.value ), # Write request read from the input pin.
            rd_en = int( d.rd_en.value ), # Read request read from the input pin.
            wr_data = int( d.wr_data.value ), # Write data read from the input pin.
            count = int( d.count.value ), # Number of stored items reported by the FIFO.
            full = bool( int( d.full.value ) ), # True when the FIFO reports that it is full.
            empty = empty, # True when the FIFO reports that it is empty.
            rd_data = None if empty else int( d.rd_data.value ), # If FIFO is empty, rd_data is none. Otherwise read/store rd_data as integer.
        )