"""

Test cases for the FIFO. Each cycle the FIFO runs and then the scoreboard
updates its model and compares the results with it every cycle.

Minh Hoang Ho - Project 1
"""

import os
import random

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, ReadOnly, RisingEdge, Timer

from tb.driver import FifoDriver, FifoTxn
from tb.monitor import FifoMonitor
from tb.scoreboard import FifoScoreboard
from tb.coverage import FifoCoverage
from crv.seeded_regression import SEEDS, run_seed

WIDTH = 8 # Data width in bits.
DEPTH = 8 # Number of entries the FIFO holds.
MASK = 0xFF # Max 8 bit value.

cov = FifoCoverage( DEPTH ) # One coverage tracker shared by every test so the report covers the whole run.

async def setup( dut ):
    """
    Starts the clock and resets the FIFO.
    """

    drv = FifoDriver( dut ) # Driver also starts the clock.
    mon = FifoMonitor( dut )
    sb = FifoScoreboard( ) # Scoreboard holds the reference model the FIFO gets checked against.
    await drv.reset( )
    sb.check( mon.capture( ) ) # Check the reset state.
    return drv, mon, sb

async def run_cycle( drv, mon, sb, wr, rd, data = 0 ):
    """
    Runs one clock cycle and checks it against the model.
    """

    before = sb.model.count # Count from before this cycle for coverage.
    await drv.drive( FifoTxn( wr, rd, data ) )
    obs = mon.capture( )
    sb.check( obs ) # Scoreboard updates its model and checks the outputs.
    cov.sample( before, obs ) # Record the cycle for coverage.

async def reset_during_test( dut, mon, sb, cycles = 1, wr = 0, rd = 0 ):
    """
    Resets the FIFO in the middle of a test. Write and read can be left on to
    make sure reset still clears the FIFO.
    """

    before = sb.model.count # Count from before the reset for coverage.
    await FallingEdge( dut.clk ) # Inputs change on the falling edge.
    dut.rst_n.value = 0 # Assert reset.
    dut.wr_en.value = wr
    dut.rd_en.value = rd
    dut.wr_data.value = 0x5A # Junk data that should not get written.

    for i in range( cycles ):
        await RisingEdge( dut.clk )
        await ReadOnly( ) # Wait for the outputs to settle.
        obs = mon.capture( )
        cov.sample( before, obs, rst_n = 0 ) # Record a write or read held during reset.
        sb.model.reset( ) # Reset the model too.
        assert obs.count == 0 # FIFO should be empty during reset.
        assert obs.empty
        assert not obs.full

    await FallingEdge( dut.clk )
    dut.rst_n.value = 1
    dut.wr_en.value = 0
    dut.rd_en.value = 0

async def write( drv, mon, sb, values ):
    """
    Writes each value in the list one cycle at a time.
    """

    for i in range( len( values ) ):
        await run_cycle( drv, mon, sb, 1, 0, values[ i ] )

async def read( drv, mon, sb, times ):
    """
    Reads the given number of times one cycle at a time.
    """

    for i in range( times ):
        await run_cycle( drv, mon, sb, 0, 1 )

async def fill( drv, mon, sb, start = 0 ):
    """
    Keeps writing until the FIFO is full.
    """

    for i in range( DEPTH - sb.model.count ):
        await run_cycle( drv, mon, sb, 1, 0, start + i )
    assert sb.model.full

async def drain( drv, mon, sb ):
    """
    Keeps reading until the FIFO is empty.
    """

    for i in range( sb.model.count ):
        await run_cycle( drv, mon, sb, 0, 1 )
    assert sb.model.empty

@cocotb.test( )
async def test_smoke( dut ):
    """
    Starter test. Writes three values and the count should be 3.
    """

    cocotb.start_soon( Clock( dut.clk, 10, units = "ns" ).start( ) ) # 10 ns clock.
    dut.wr_en.value = 0
    dut.rd_en.value = 0
    dut.wr_data.value = 0
    dut.rst_n.value = 0 # Assert reset.

    for i in range( 3 ): # Hold reset for 3 cycles.
        await RisingEdge( dut.clk )

    dut.rst_n.value = 1
    await FallingEdge( dut.clk )

    for i in range( 3 ):
        dut.wr_en.value = 1
        dut.wr_data.value = 0x40 + i
        await RisingEdge( dut.clk )
        await Timer( 1, units = "ns" ) # Let the outputs settle.

    dut.wr_en.value = 0
    assert int( dut.count.value ) == 3

@cocotb.test( )
async def test_reset( dut ):
    """
    After reset the FIFO should be empty. Then wr_data changes while wr_en is
    low and nothing should get written.
    """

    drv, mon, sb = await setup( dut ) # The reset state is checked here.
    data = [ 0x33, 0xCC, 0xFF ]
    for i in range( len( data ) ):
        await run_cycle( drv, mon, sb, 0, 0, data[ i ] ) # Change wr_data with wr_en low.
    assert sb.model.count == 0 # Nothing should have been written.

@cocotb.test( )
async def test_fill_drain( dut ):
    """
    Fill and drain twice and then do a partial one. The second time through
    the pointers have already wrapped.
    """

    drv, mon, sb = await setup( dut )
    for i in range( 2 ):
        await fill( drv, mon, sb, start = 0x11 + i )
        await drain( drv, mon, sb )

    await write( drv, mon, sb, [ 0x01, 0x02, 0x03 ] ) # Partial fill.
    await read( drv, mon, sb, 3 )
    assert sb.model.empty

@cocotb.test( )
async def test_overflow( dut ):
    """
    Writes while the FIFO is full should get dropped.
    """

    drv, mon, sb = await setup( dut )
    await fill( drv, mon, sb, start = 0x20 )

    for i in range( 5 ): # Write 5 more while full.
        await run_cycle( drv, mon, sb, 1, 0, 0xE0 + i )
    assert sb.model.count == DEPTH # Count should stay at DEPTH.

    await drain( drv, mon, sb ) # Make sure none of the dropped values got in.
    await write( drv, mon, sb, [ 0x9A, 0x9B ] ) # Normal writes still work after.
    await read( drv, mon, sb, 2 )

@cocotb.test( )
async def test_underflow( dut ):
    """
    Reads while the FIFO is empty should get ignored.
    """

    drv, mon, sb = await setup( dut )
    await read( drv, mon, sb, 5 ) # Read 5 times while empty.
    assert sb.model.count == 0 # Count should not go below 0.

    await write( drv, mon, sb, [ 0xA5, 0x3C ] ) # First value written should be at the head.
    await read( drv, mon, sb, 2 )
    await read( drv, mon, sb, 3 ) # Underflow again.
    await write( drv, mon, sb, [ 0x77 ] )
    await read( drv, mon, sb, 1 )

@cocotb.test( )
async def test_read_write( dut ):
    """
    Reading and writing at the same time should keep the count the same.
    This gets checked at every level from empty to full.
    """

    drv, mon, sb = await setup( dut )

    await run_cycle( drv, mon, sb, 1, 1, 0x01 ) # At empty only the write happens.
    assert sb.model.count == 1

    await run_cycle( drv, mon, sb, 1, 1, 0x02 ) # At 1 entry both happen.
    assert sb.model.count == 1

    await write( drv, mon, sb, [ 0x10, 0x11, 0x12 ] ) # Get to the middle.
    for i in range( DEPTH * 2 ):
        await run_cycle( drv, mon, sb, 1, 1, 0x40 + i )
    assert sb.model.count == 4 # Count should not change.

    await write( drv, mon, sb, [ 0x20, 0x21, 0x22 ] ) # Get to one below full.
    for i in range( DEPTH ):
        await run_cycle( drv, mon, sb, 1, 1, 0x80 + i )
    assert sb.model.count == DEPTH - 1 # Count should not change.

    await write( drv, mon, sb, [ 0x30 ] ) # At full only the read happens.
    await run_cycle( drv, mon, sb, 1, 1, 0xF0 )
    assert sb.model.count == DEPTH - 1 # Count drops by one.

    await write( drv, mon, sb, [ 0x31 ] ) # Back to full.
    for i in range( 3 ): # Read and write at full a few more times.
        await run_cycle( drv, mon, sb, 1, 1, 0xF1 + i )
        await write( drv, mon, sb, [ 0x50 + i ] )

    await read( drv, mon, sb, DEPTH - 1 ) # Back down to 1 entry.
    await run_cycle( drv, mon, sb, 1, 1, 0x60 )
    await drain( drv, mon, sb )
    await run_cycle( drv, mon, sb, 1, 1, 0x61 ) # At empty again only the write happens.
    await drain( drv, mon, sb )

@cocotb.test( )
async def test_wrap( dut ):
    """
    Start at every pointer position so both pointers wrap at every slot.
    """

    drv, mon, sb = await setup( dut )

    for i in range( DEPTH ): # Try each starting spot from 0 to 7.
        await reset_during_test( dut, mon, sb ) # Reset puts both pointers at 0.
        for j in range( i ): # Move the write pointer up to spot i.
            await write( drv, mon, sb, [ 0xC0 + j ] )
        await read( drv, mon, sb, i ) # Move the read pointer up to spot i.
        await fill( drv, mon, sb, start = i * 9 ) # Write pointer wraps around.
        await drain( drv, mon, sb ) # Read pointer wraps around.

    await write( drv, mon, sb, [ 0x01, 0x02, 0x03, 0x04 ] ) # Get to half full.
    for i in range( DEPTH * 4 ): # Read and write together so the pointers keep lapping.
        await run_cycle( drv, mon, sb, 1, 1, i * 7 )
    await drain( drv, mon, sb )

@cocotb.test( )
async def test_all_bits( dut ):
    """
    Every data bit goes through as a 0 and as a 1.
    """

    drv, mon, sb = await setup( dut )
    ones = [ 0x01, 0x02, 0x04, 0x08, 0x10, 0x20, 0x40, 0x80 ] # Only one bit is 1.
    zeros = [ 0xFE, 0xFD, 0xFB, 0xF7, 0xEF, 0xDF, 0xBF, 0x7F ] # Only one bit is 0.

    await write( drv, mon, sb, [ 0x00, 0xFF, 0xAA, 0x55 ] ) # All 0s and all 1s and alternating bits.
    await drain( drv, mon, sb )
    await write( drv, mon, sb, ones )
    await drain( drv, mon, sb )
    await write( drv, mon, sb, zeros )
    await drain( drv, mon, sb )

    await write( drv, mon, sb, [ 0x00, 0xFF ] ) # Same patterns with read and write together.
    for i in range( 8 ):
        await run_cycle( drv, mon, sb, 1, 1, ones[ i ] )
    for i in range( 8 ):
        await run_cycle( drv, mon, sb, 1, 1, zeros[ i ] )
    await drain( drv, mon, sb )

@cocotb.test( )
async def test_reset_in_use( dut ):
    """
    Reset while the FIFO is in use and the enables are held high.
    """

    drv, mon, sb = await setup( dut )
    await write( drv, mon, sb, [ 0x11, 0x22, 0x33, 0x44, 0x55 ] )
    await read( drv, mon, sb, 2 ) # Get the pointers off zero.
    await reset_during_test( dut, mon, sb, cycles = 2, wr = 1, rd = 1 ) # Reset with write and read both on.

    await write( drv, mon, sb, [ 0xA1, 0xA2, 0xA3 ] ) # Old data should be gone.
    await fill( drv, mon, sb, start = 0xB0 )
    await drain( drv, mon, sb )

    await fill( drv, mon, sb, start = 0x05 ) # Reset while full.
    await reset_during_test( dut, mon, sb, cycles = 1, wr = 1, rd = 0 ) # Reset with write on.
    await write( drv, mon, sb, [ 0xD1 ] )
    await read( drv, mon, sb, 1 )

@cocotb.test( )
async def test_simple_random( dut ):
    """
    Random test using plain python random. It switches between mostly writes
    and mostly reads and both.
    """

    drv, mon, sb = await setup( dut )
    chances = [ ( 0.9, 0.1 ), ( 0.1, 0.9 ), ( 0.95, 0.95 ), ( 0.5, 0.5 ) ] # Chance to write and chance to read.

    for seed in [ 1, 2, 3, 4, 5 ]:
        rng = random.Random( seed ) # Same seed gives the same cycles every time.
        await reset_during_test( dut, mon, sb ) # Start each seed from empty.
        cycles_left = 0 # Cycles left before picking again.

        for i in range( 400 ):
            if cycles_left == 0: # Pick what to focus on next.
                write_chance, read_chance = rng.choice( chances )
                cycles_left = rng.randint( 5, 30 ) # Keep it for 5 to 30 cycles.
            cycles_left -= 1
            wr = int( rng.random( ) < write_chance )
            rd = int( rng.random( ) < read_chance )
            await run_cycle( drv, mon, sb, wr, rd, rng.randint( 0, MASK ) )

@cocotb.test( )
async def test_seeded_regression( dut ):
    """
    Random test using pyvsc and the seeded regression.
    """

    drv, mon, sb = await setup( dut )

    for seed in SEEDS:
        await reset_during_test( dut, mon, sb ) # Start each seed from empty.
        await run_seed( drv, mon, sb, seed, run_cycle )

    report = cov.report( ) # Coverage for every test in the file.
    with open( os.path.join( os.path.dirname( __file__ ), "coverage_report.txt" ), "w" ) as f:
        f.write( report )