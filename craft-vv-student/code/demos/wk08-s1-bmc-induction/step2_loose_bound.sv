// ============================================================
//  step2_loose_bound.sv -- a TRUE property that FAILS k-induction.
//
//  The property: count <= DEPTH+1. Every reachable count is 0..DEPTH, so
//  this is true -- strictly weaker than the count <= DEPTH the FIFO
//  guarantees. BMC agrees at any depth. k-induction rejects it: the
//  inductive step starts from ANY state satisfying the property, and
//  count == DEPTH+1 satisfies it. That state is unreachable from reset,
//  but induction does not know reachability. Parked there, full reads
//  false (count != DEPTH), so a write is accepted and count steps to
//  DEPTH+2 -- violation. The solver can idle at DEPTH+1 for as many
//  cycles as the depth asks before taking that step, so no k converges.
//
//  The lesson: "true" and "inductive" are different properties of a
//  property. Weakening a claim can make it UNPROVABLE by induction,
//  because the induction hypothesis weakens with it. No depth fixes this
//  (watch the log try every k); only strengthening does -- step 3.
// ============================================================
module fifo_bound #(
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
    // Same one-cycle reset assumption as fifo_formal.sv, so the base case
    // starts from a defined count.
    reg f_past_valid = 1'b0;
    always @(posedge clk) f_past_valid <= 1'b1;
    always @(posedge clk) if (!f_past_valid) assume (!rst_n);

    always @(posedge clk) begin
        if (rst_n && f_past_valid) begin
            // TRUE (reachable counts stop at DEPTH) -- but NOT inductive.
            assert (count <= DEPTH + 1);
        end
    end
`endif
endmodule
