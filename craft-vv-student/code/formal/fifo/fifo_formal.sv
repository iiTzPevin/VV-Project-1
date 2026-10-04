// ============================================================
//  fifo_formal.sv  --  CRAFT V&V Week 8 : formal wrapper for dut/fifo.sv.
//
//  A thin harness that instantiates the REAL fifo and asserts its safety
//  invariants, so dut/fifo.sv is never edited.  The FIFO's control inputs
//  (wr_en, rd_en, wr_data, rst_n) are left free, so SymbiYosys explores every
//  legal stimulus.  Properties are immediate assertions in a clocked block
//  (the yosys-0.33 formal idiom): `if (rst_n)` stands in for `disable
//  iff(!rst_n)`, an `if` antecedent stands in for `|->`.
//
//  Proven by formal/fifo/fifo.sby (bmc + k-induction, engine smtbmc z3):
//    * never overflow      -- 0 <= count <= DEPTH always,
//    * flag consistency    -- full==(count==DEPTH), empty==(count==0),
//    * no-overflow behavior -- a write while full leaves count at DEPTH,
//    * no-underflow behavior -- a read while empty leaves count at 0.
// ============================================================
module fifo_formal #(
    parameter int WIDTH = 8,
    parameter int DEPTH = 8
) (
    input logic                    clk,
    input logic                    rst_n,
    input logic                    wr_en,
    input logic                    rd_en,
    input logic [WIDTH-1:0]        wr_data
);
    logic [WIDTH-1:0]        rd_data;
    logic                    full;
    logic                    empty;
    logic [$clog2(DEPTH):0]  count;

    // The design under proof -- the unmodified FIFO.
    fifo #(.WIDTH(WIDTH), .DEPTH(DEPTH)) u_fifo (
        .clk    (clk),
        .rst_n  (rst_n),
        .wr_en  (wr_en),
        .wr_data(wr_data),
        .rd_en  (rd_en),
        .rd_data(rd_data),
        .full   (full),
        .empty  (empty),
        .count  (count)
    );

`ifdef FORMAL
    // Hold the FIFO in reset for the first step so cnt starts at a defined 0
    // (needed for the BMC base case and the k-induction base case).
    reg f_past_valid = 1'b0;
    always @(posedge clk) f_past_valid <= 1'b1;
    always @(posedge clk) if (!f_past_valid) assume (!rst_n);

    always @(posedge clk) begin
        if (rst_n && f_past_valid) begin
            // NEVER OVERFLOW: occupancy is always a legal depth, 0..DEPTH.
            // (count is unsigned so >=0 is structural; DEPTH is the upper bound.)
            assert (count <= DEPTH);

            // FLAG CONSISTENCY at all times.
            assert (full  == (count == DEPTH));
            assert (empty == (count == 0));

            // NO-OVERFLOW behavior: a write attempted while full is dropped,
            // so the count stays pinned at DEPTH.
            if ($past(rst_n) && $past(full) && $past(wr_en) && !$past(rd_en))
                assert (count == DEPTH);

            // NO-UNDERFLOW behavior: a read attempted while empty is ignored,
            // so the count stays pinned at 0.
            if ($past(rst_n) && $past(empty) && $past(rd_en) && !$past(wr_en))
                assert (count == 0);
        end
    end
`endif
endmodule
