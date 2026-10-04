// ============================================================
//  step3_strengthened.sv -- the strengthening that makes step 2 converge.
//
//  Identical to step2_loose_bound.sv except for ONE added assertion:
//      diff step2_loose_bound.sv step3_strengthened.sv
//  We prove MORE in order to prove it at all. Asserting count <= DEPTH
//  strengthens the induction hypothesis: the step may now start only from
//  states with count <= DEPTH, the spurious count==DEPTH+1 pre-state is
//  excluded, and the write that stepped out of it is gated by full. Both
//  assertions -- the strong bound and the loose one it implies -- go
//  through by k-induction in one run.
//
//  This is invariant strengthening, the daily craft of formal: read the
//  induction counterexample, name the unreachable pre-state the solver
//  invented, add the invariant that rules it out, rerun. Iterate until
//  the set is inductive.
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
            // THE STRENGTHENING: the tight bound IS inductive, and once it
            // is in the hypothesis the loose bound rides along.
            assert (count <= DEPTH);
        end
    end
`endif
endmodule
