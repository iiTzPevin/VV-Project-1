// ============================================================
//  uart.sv  --  CRAFT V&V unifying example #3 : UART (tx + rx)
//  8N1 framing: idle-high line, start bit (low), 8 data bits LSB-first,
//  one stop bit (high).  Both engines share a clock; the bit period is
//  CLKS_PER_BIT clocks (default 8 -- fast simulation, even mid-point).
//  Used Week 7 (assertion-based verification) and Week 9 (pyuvm).
//  Spec: dut/specs/uart.md.  Synthesizable; Verilator 5.020 and Icarus.
// ============================================================
module uart #(
    parameter int CLKS_PER_BIT = 8,
    parameter int WIDTH        = 8
) (
    input  logic             clk,
    input  logic             rst_n,

    // transmit side: valid/ready handshake in, serial line out
    input  logic             tx_valid,
    input  logic [WIDTH-1:0] tx_data,
    output logic             tx_ready,
    output logic             txd,

    // receive side: serial line in, pulse interface out
    input  logic             rxd,
    output logic [WIDTH-1:0] rx_data,
    output logic             rx_valid,   // 1-cycle pulse: frame received, stop bit good
    output logic             frame_err   // 1-cycle pulse: stop bit sampled low
);
    localparam int MID = CLKS_PER_BIT / 2;

    // ---------------- transmit engine ----------------
    typedef enum logic [1:0] {T_IDLE, T_START, T_DATA, T_STOP} tstate_t;
    tstate_t                 t_state;
    logic [WIDTH-1:0]        t_shift;
    logic [$clog2(CLKS_PER_BIT)-1:0] t_baud;
    logic [3:0]              t_bit;

    assign tx_ready = (t_state == T_IDLE);

    always_ff @(posedge clk) begin
        if (!rst_n) begin
            t_state <= T_IDLE;
            txd     <= 1'b1;             // line idles high
            t_baud  <= '0;
            t_bit   <= '0;
            t_shift <= '0;
        end else begin
            case (t_state)
                T_IDLE: begin
                    txd    <= 1'b1;
                    t_baud <= '0;
                    t_bit  <= '0;
                    if (tx_valid) begin
                        t_shift <= tx_data;
                        t_state <= T_START;
                        txd     <= 1'b0;   // start bit begins immediately
                    end
                end
                T_START: begin
                    if (t_baud == CLKS_PER_BIT-1) begin
                        t_baud  <= '0;
                        t_state <= T_DATA;
                        txd     <= t_shift[0];          // first data bit, LSB
                    end else t_baud <= t_baud + 1'b1;
                end
                T_DATA: begin
                    if (t_baud == CLKS_PER_BIT-1) begin
                        t_baud <= '0;
                        if (t_bit == WIDTH-1) begin
                            t_state <= T_STOP;
                            txd     <= 1'b1;            // stop bit
                        end else begin
                            t_bit   <= t_bit + 1'b1;
                            t_shift <= {1'b0, t_shift[WIDTH-1:1]};
                            txd     <= t_shift[1];      // next bit (post-shift LSB)
                        end
                    end else t_baud <= t_baud + 1'b1;
                end
                T_STOP: begin
                    if (t_baud == CLKS_PER_BIT-1) begin
                        t_baud  <= '0;
                        t_state <= T_IDLE;
                        txd     <= 1'b1;
                    end else t_baud <= t_baud + 1'b1;
                end
                default: t_state <= T_IDLE;
            endcase
        end
    end

    // ---------------- receive engine ----------------
    typedef enum logic [1:0] {R_IDLE, R_START, R_DATA, R_STOP} rstate_t;
    rstate_t                 r_state;
    logic [WIDTH-1:0]        r_shift;
    logic [$clog2(CLKS_PER_BIT)-1:0] r_baud;
    logic [3:0]              r_bit;

    always_ff @(posedge clk) begin
        if (!rst_n) begin
            r_state   <= R_IDLE;
            r_baud    <= '0;
            r_bit     <= '0;
            r_shift   <= '0;
            rx_data   <= '0;
            rx_valid  <= 1'b0;
            frame_err <= 1'b0;
        end else begin
            rx_valid  <= 1'b0;           // pulse interface: default low
            frame_err <= 1'b0;
            case (r_state)
                R_IDLE: begin
                    r_baud <= '0;
                    r_bit  <= '0;
                    if (rxd == 1'b0)     // falling edge: candidate start bit
                        r_state <= R_START;
                end
                R_START: begin
                    if (r_baud == MID-1) begin
                        r_baud <= '0;
                        if (rxd == 1'b0) r_state <= R_DATA;   // confirmed at mid-bit
                        else             r_state <= R_IDLE;   // glitch: reject
                    end else r_baud <= r_baud + 1'b1;
                end
                R_DATA: begin
                    if (r_baud == CLKS_PER_BIT-1) begin
                        r_baud  <= '0;
                        r_shift <= {rxd, r_shift[WIDTH-1:1]}; // sample mid-bit, LSB first
                        if (r_bit == WIDTH-1) r_state <= R_STOP;
                        else                  r_bit   <= r_bit + 1'b1;
                    end else r_baud <= r_baud + 1'b1;
                end
                R_STOP: begin
                    if (r_baud == CLKS_PER_BIT-1) begin
                        r_baud  <= '0;
                        r_state <= R_IDLE;
                        if (rxd == 1'b1) begin                // stop bit good
                            rx_data  <= r_shift;
                            rx_valid <= 1'b1;
                        end else
                            frame_err <= 1'b1;                // stop bit low
                    end else r_baud <= r_baud + 1'b1;
                end
                default: r_state <= R_IDLE;
            endcase
        end
    end
endmodule
