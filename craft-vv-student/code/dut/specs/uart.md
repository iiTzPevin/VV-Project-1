# UART — specification (`dut/uart.sv`)

A universal asynchronous receiver/transmitter with 8N1 framing: idle-high
line, one start bit (low), **8 data bits, LSB first**, one stop bit (high),
no parity. Transmit and receive engines are independent and share `clk`;
the bit period is `CLKS_PER_BIT` clocks (default 8).

## Interface

| Port | Dir | Width | Meaning |
|------|-----|-------|---------|
| `clk`, `rst_n` | in | 1 | clock; active-low synchronous reset |
| `tx_valid` | in | 1 | request to send `tx_data` |
| `tx_data` | in | 8 | word to transmit |
| `tx_ready` | out | 1 | high exactly while the transmitter can accept a word |
| `txd` | out | 1 | serial line out (idles high) |
| `rxd` | in | 1 | serial line in (idle high) |
| `rx_data` | out | 8 | last correctly received word |
| `rx_valid` | out | 1 | **1-cycle pulse**: a frame was received with a good stop bit |
| `frame_err` | out | 1 | **1-cycle pulse**: a frame's stop bit sampled low |

## Transmit contract

1. A word is accepted on a clock edge where `tx_valid && tx_ready`. The start
   bit is on `txd` from the next cycle.
2. Frame timing: start (1 bit-time, low) → data bits 0..7, LSB first (1
   bit-time each) → stop (1 bit-time, high) → `tx_ready` high again.
   Every bit is held a full `CLKS_PER_BIT` clocks; `txd` changes only on
   bit boundaries.
3. `tx_ready` is low for the entire frame — exactly 10 bit-times per word.
   A `tx_valid` asserted while `tx_ready` is low is ignored (not queued).
4. Reconfiguration mid-frame is illegal: `tx_data` is latched at accept;
   later changes have no effect on the frame in flight.

## Receive contract

5. A falling edge on `rxd` while idle begins start-bit qualification: the
   line is re-checked at the middle of the start bit; if it has returned
   high the edge is treated as a glitch and discarded (no pulse, no data
   change).
6. Data bits are sampled at the middle of each bit-time, LSB first.
7. At the middle of the stop bit: if `rxd` is high, `rx_data` updates and
   `rx_valid` pulses for one cycle. If `rxd` is low, `frame_err` pulses for
   one cycle and `rx_data` is **not** updated. The two pulses are mutually
   exclusive.
8. `rx_data` changes only on an accepting `rx_valid` — never on noise,
   glitches, or rejected frames.

## Reset

9. Under reset: `txd` high, `tx_ready` high after release, both engines
   idle, no pulses.
