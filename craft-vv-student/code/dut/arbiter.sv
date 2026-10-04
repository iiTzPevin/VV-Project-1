// ============================================================
//  arbiter.sv  --  CRAFT V&V Week 8 : round-robin arbiter (formal target).
//
//  Grants at most one of N requesters per cycle.  Priority rotates so that,
//  after a line is served, it drops to lowest priority -- classic round robin.
//
//  Implementation: isolate-lowest-set-bit (x & -x) over a rotating priority
//  window.  `mask` holds the bits strictly above the last grant; requests in
//  the window win first, otherwise priority wraps to the lowest-index request.
//  This makes the safety properties structural and easy to prove:
//    * grant subset of req  (grant_masked subset req_masked subset req; grant_unmasked subset req)
//    * grant one-hot-or-zero (lowest-set-bit isolation yields <=1 bit)
//    * progress (if any req, some grant)
//
//  Synthesizable; the `ifdef FORMAL` block holds the SVA proven by SymbiYosys
//  (formal/arbiter/arbiter.sby).  Written for the yosys-0.33 SVA subset.
// ============================================================
module arbiter #(
    parameter int N = 4
) (
    input  logic         clk,
    input  logic         rst_n,
    input  logic [N-1:0] req,
    output logic [N-1:0] grant
);
    localparam logic [N-1:0] ONE = {{(N-1){1'b0}}, 1'b1};

    // Priority window: after a grant to bit g, `mask` holds the bits strictly
    // greater than g, so the next arbitration starts just past the last winner.
    logic [N-1:0] mask;

    logic [N-1:0] req_masked;
    logic [N-1:0] grant_masked;    // lowest set bit of req within the window
    logic [N-1:0] grant_unmasked;  // lowest set bit of req overall (the wrap)

    assign req_masked     = req & mask;
    assign grant_masked   = req_masked & (~req_masked + ONE);   // req_masked & -req_masked
    assign grant_unmasked = req & (~req + ONE);                 // req & -req
    assign grant          = (|req_masked) ? grant_masked : grant_unmasked;

    always_ff @(posedge clk) begin
        if (!rst_n)
            mask <= {N{1'b1}};                     // reset: plain lowest-index priority
        else if (|grant)
            mask <= ~((grant - ONE) | grant);      // bits strictly above the grant
    end

`ifdef FORMAL
    // yosys 0.33's Verilog frontend does not parse concurrent `assert property
    // (@(posedge clk) ...)`, so the formal properties are written as *immediate*
    // assertions inside a clocked block -- the standard SymbiYosys idiom.
    // `if (rst_n)` plays the role of `disable iff(!rst_n)`, and an `if`
    // antecedent plays the role of `|->`. (These arbiter invariants are purely
    // combinational functions of req/grant, so they need no reset assumption:
    // they hold for every value of the internal `mask`.)
    always @(posedge clk) begin
        if (rst_n) begin
            // SAFETY 1 -- grant is a subset of req: never grant a non-requester.
            assert ((grant & ~req) == {N{1'b0}});

            // SAFETY 2 -- grant is one-hot-or-zero: at most one grant per cycle.
            //   (grant & (grant-1)) clears the lowest set bit; ==0 iff <=1 bit set.
            assert ((grant & (grant - ONE)) == {N{1'b0}});

            // SAFETY 3 -- progress: if anyone requests, some line is granted.
            if (|req)
                assert (|grant);
        end
    end
`endif
endmodule
