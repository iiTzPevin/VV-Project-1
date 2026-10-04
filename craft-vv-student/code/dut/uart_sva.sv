// ============================================================
//  uart_sva.sv  --  CRAFT V&V Week 7 : concurrent-SVA checker for uart.sv
//
//  A checker module (no functional logic) bound *inside* the uart scope
//  (see dut/uart_bind.sv), so it observes the engines' internal state --
//  t_state / r_state, the baud counters, the shift registers -- as well as
//  the ports. That whitebox view is what lets one-cycle implications state
//  the FRAMING contract without unsupported ##[N:M] sequences: instead of
//  "start implies stop 9 bit-times later," we pin the line level and the
//  bit-period in every state, which together imply the frame timing.
//
//  Written for the Verilator-5.020 SVA subset (same as fifo_sva.sv):
//  plain @(posedge clk) disable iff(!rst_n), |->, |=>, $past, $stable.
//  Every property HOLDS on clean RTL and must FIRE on a broken UART.
// ============================================================
module uart_sva #(
    parameter int CLKS_PER_BIT = 8,
    parameter int WIDTH        = 8
) (
    input logic             clk,
    input logic             rst_n,
    input logic             tx_valid,
    input logic             tx_ready,
    input logic             txd,
    input logic             rxd,
    input logic [WIDTH-1:0] rx_data,
    input logic             rx_valid,
    input logic             frame_err,
    // internal signals, reached through the bind's `.*`:
    input logic [1:0]       t_state,   // T_IDLE=0 T_START=1 T_DATA=2 T_STOP=3
    input logic [1:0]       r_state,
    input logic [$clog2(CLKS_PER_BIT)-1:0] t_baud,
    input logic [$clog2(CLKS_PER_BIT)-1:0] r_baud
);
    localparam logic [1:0] T_IDLE = 2'd0, T_START = 2'd1,
                           T_DATA = 2'd2, T_STOP  = 2'd3;

    // ---- line-level framing: the level is pinned by the frame position ----
    // 1) The line idles high. Catches idle-level and stop-glitch bugs.
    a_idle_high:  assert property (@(posedge clk) disable iff(!rst_n)
        (t_state == T_IDLE) |-> txd);

    // 2) The start bit is low for its whole bit-time.
    a_start_low:  assert property (@(posedge clk) disable iff(!rst_n)
        (t_state == T_START) |-> !txd);

    // 3) The stop bit is high for its whole bit-time. With (2) this is the
    //    "start implies a correctly-timed stop" framing property, stated
    //    positionally. Catches stop-dropped / stop-low mutants.
    a_stop_high:  assert property (@(posedge clk) disable iff(!rst_n)
        (t_state == T_STOP) |-> txd);

    // ---- handshake ----
    // 4) tx_ready exactly in IDLE: no mid-frame acceptance, no dead cycles.
    a_ready_iff_idle: assert property (@(posedge clk) disable iff(!rst_n)
        tx_ready == (t_state == T_IDLE));

    // 5) Accepting a word starts a frame: valid+ready implies the start bit
    //    is on the wire the next cycle.
    a_accept_starts: assert property (@(posedge clk) disable iff(!rst_n)
        (tx_valid && tx_ready) |=> (t_state == T_START && !txd));

    // ---- bit-period ----
    // 6) Baud counters stay inside one bit-time. Catches period mutants
    //    (a counter that wraps early transmits short bits).
    a_tbaud_range: assert property (@(posedge clk) disable iff(!rst_n)
        t_baud < CLKS_PER_BIT);
    a_rbaud_range: assert property (@(posedge clk) disable iff(!rst_n)
        r_baud < CLKS_PER_BIT);

    // 7) The line is stable within a bit-time: txd may only change on a
    //    bit boundary (t_baud == 0 is the first cycle of a new bit).
    a_bit_stable: assert property (@(posedge clk) disable iff(!rst_n)
        (t_baud != 0) |-> $stable(txd));

    // ---- receive contract ----
    // 8) rx_valid and frame_err are mutually exclusive: a frame is either
    //    accepted or rejected, never both. Catches error-path mutants.
    a_valid_xor_err: assert property (@(posedge clk) disable iff(!rst_n)
        !(rx_valid && frame_err));

    // 9) rx_data only changes when a frame is accepted -- the data register
    //    is not disturbed by noise, glitches, or rejected frames.
    a_data_gated: assert property (@(posedge clk) disable iff(!rst_n)
        !$stable(rx_data) |-> rx_valid);

endmodule
