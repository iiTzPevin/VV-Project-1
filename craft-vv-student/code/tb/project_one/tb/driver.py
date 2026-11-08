"""
The driver sends read and write requests to the FIFO being tested.
It controls the clock, reset, and input signals. The separate scoreboard
checks whether the FIFO's response is correct.

Matias Guillen - Project 1
"""

from dataclasses import dataclass

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, ReadOnly, RisingEdge

@dataclass
class FifoTxn:
    """
    FIFO inputs are held for one clock cycle.
    """

    wr_en: int # Write request to the FIFO, 0 or 1.
    rd_en: int # Read request to the FIFO, 0 or 1.
    wr_data: int = 0 # 0 Ignored, otherwise data to write.

class FifoDriver:
    """
    Turns transaction values into changes on the FIFO's input pins.
    """

    def __init__( self, dut, period_ns = 10 ):
        """
        Setup FIFO driver with clock period to 10 ns.
        """

        self.dut = dut # Allows access to FIFO in driver.
        cocotb.start_soon( Clock( dut.clk, period_ns, "ns" ).start( ) ) # Create clock generate to FIFO clk signal, repeat behavior and schedule to run along test.

    async def reset( self ):
        """
        Apply reset before testing FIFO.
        """

        d = self.dut
        await FallingEdge( d.clk ) # Wait for the next falling edge before changing inputs.
        d.wr_en.value = 0 # FIFO Input Signal (do not write to FIFO).
        d.rd_en.value = 0 # FIFO Input Signal (do not read from FIFO).
        d.wr_data.value = 0 # FIFO Input Signal (data to write to FIFO).
        d.rst_n.value = 0 # FIFO Input Signal (reset signal).

        for _ in range( 3 ): # Loop, wait 3 clock cycles for reset to be applied to FIFO.
            await RisingEdge( d.clk ) # Wait for the next rising edge.

        await FallingEdge( d.clk ) # Wait for the next falling edge.
        d.rst_n.value = 1 # Release reset.

    async def drive( self, txn ):
        """
        Apply one transaction and return when its outputs have been observed.
        """

        d = self.dut
        await FallingEdge( d.clk ) # Wait for the next falling edge.
        d.wr_en.value = int( txn.wr_en ) # Set write enable signal.
        d.rd_en.value = int( txn.rd_en ) # Set read enable signal.
        d.wr_data.value = int( txn.wr_data ) # Set write data signal.
        await RisingEdge( d.clk ) # Wait for the next rising edge.
        await ReadOnly( ) # Wait for HDL updates to finish.