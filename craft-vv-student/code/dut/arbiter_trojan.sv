// ============================================================
//  arbiter_trojan.sv  --  CRAFT V&V Week 8 : a BACKDOORED round-robin arbiter.
//
//  Byte-for-byte the same round-robin core as arbiter.sv, PLUS a hardware
//  trojan: on a magic request pattern (req == 4'b1010) it raises a grant bit
//  for a line that did NOT request, violating "grant subset of req".
//
//  The magic pattern is rare and correlated with a specific input, so it easily
//  slips past directed tests and even random simulation -- but a formal proof
//  of (grant & ~req) == 0 finds it immediately and hands back the exact
//  triggering input as a counterexample (formal/arbiter/arbiter.sby, task
//  `trojan`).  This is the "prove the backdoor is absent vs. find it" lesson.
// ============================================================
module arbiter_trojan #(
    parameter int N = 4
) (
    input  logic         clk,
    input  logic         rst_n,
    input  logic [N-1:0] req,
    output logic [N-1:0] grant
);
    localparam logic [N-1:0] ONE = {{(N-1){1'b0}}, 1'b1};

    logic [N-1:0] mask;
    logic [N-1:0] req_masked;
    logic [N-1:0] grant_masked;
    logic [N-1:0] grant_unmasked;
    logic [N-1:0] grant_rr;        // the honest round-robin grant

    assign req_masked     = req & mask;
    assign grant_masked   = req_masked & (~req_masked + ONE);
    assign grant_unmasked = req & (~req + ONE);
    assign grant_rr       = (|req_masked) ? grant_masked : grant_unmasked;

    // ---- BACKDOOR --------------------------------------------------------
    // req == 4'b1010 asks for lines 1 and 3 only; the trojan instead raises
    // grant[2] -- a line that never requested. Everything else is honest.
    wire magic = (N == 4) && (req == 4'b1010);
    assign grant = magic ? 4'b0100 : grant_rr;

    always_ff @(posedge clk) begin
        if (!rst_n)
            mask <= {N{1'b1}};
        else if (|grant_rr)
            mask <= ~((grant_rr - ONE) | grant_rr);   // RR state stays honest
    end

`ifdef FORMAL
    // Same safety contract as the honest arbiter, written as immediate
    // assertions for the yosys frontend. SAFETY 1 is the one the backdoor
    // breaks; the counterexample is req == 4'b1010 -> grant == 4'b0100.
    always @(posedge clk) begin
        if (rst_n) begin
            assert ((grant & ~req) == {N{1'b0}});               // grant subset of req
            assert ((grant & (grant - ONE)) == {N{1'b0}});      // one-hot-or-zero
            if (|req)
                assert (|grant);                                // progress
        end
    end
`endif
endmodule
