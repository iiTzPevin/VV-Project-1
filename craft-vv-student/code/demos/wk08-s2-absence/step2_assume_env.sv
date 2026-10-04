// ============================================================
//  step2_assume_env.sv -- one assume, and the backdoor "disappears".
//
//  The wrapper leaves the trojaned arbiter byte-for-byte intact and adds a
//  single environment assumption that reads like integration hygiene:
//  "master 3 is the debug unit, fused off in production, so req[3] never
//  rises." Every trace the solver may consider now has req[3]==0 -- and
//  the trigger req==4'b1010 needs req[3]==1, so the violating trace is no
//  longer in the search space. The same BMC that produced the
//  counterexample now returns PASS; prove mode closes it by induction.
//
//  Nothing in the netlist changed. The proof got weaker, not the design
//  safer: PASS now means "no backdoor reachable BY THE ENVIRONMENT I
//  DESCRIBED." If the fuse claim is wrong -- a debug SKU, a glitched fuse,
//  an attacker driving the bus -- the backdoor is live and your signoff
//  says otherwise. Every assume narrows the theorem you are proving;
//  account for each one in the backdoor report (HW8 asks for exactly
//  that).
// ============================================================
module arbiter_env #(
    parameter int N = 4
) (
    input logic         clk,
    input logic         rst_n,
    input logic [N-1:0] req
);
    logic [N-1:0] grant;

    // The suspect design, unmodified. Its `ifdef FORMAL` block still
    // carries the full safety contract -- the asserts stay on.
    arbiter_trojan #(.N(N)) u_arb (
        .clk  (clk),
        .rst_n(rst_n),
        .req  (req),
        .grant(grant)
    );

`ifdef FORMAL
    // THE ENVIRONMENT MODEL. One line. This is the whole step.
    always @(posedge clk) assume (!req[3]);
`endif
endmodule
