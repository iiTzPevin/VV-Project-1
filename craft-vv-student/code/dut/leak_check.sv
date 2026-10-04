// ============================================================
//  leak_check.sv  --  CRAFT V&V Week 7 : an information-flow / security
//                     assertion (non-interference by self-composition).
//
//  A tiny "declassifier": public_in flows to pub_out, and a designated SECRET
//  input may be mixed in ONLY when secure_mode==0 (the declassified/open
//  path).  When secure_mode==1 the secret must have NO influence on pub_out.
//
//  We check that non-interference with a *self-composition* monitor: recompute
//  the exact same function with the secret scrubbed to a constant, and assert
//  that -- in secure_mode -- the real output equals the scrubbed output.  If
//  the secret can move a public output, the two disagree and the assertion
//  fires.  Build with `-DLEAK_BUG` to see the intentional leak get caught.
//
//  This is a SIMULATION check (see tb/fifo_sva/SECURITY.md for what it does and
//  does NOT prove).  Enable with Verilator's `--assert`.
// ============================================================
module leak_check #(
    parameter int W = 8
) (
    input  logic         clk,
    input  logic         rst_n,
    input  logic         secure_mode,   // 1 => secret must NOT influence pub_out
    input  logic [W-1:0] secret,        // the designated SECRET input
    input  logic [W-1:0] public_in,     // public data
    output logic [W-1:0] pub_out        // public (declassified) output
);
    // The declassification policy as a pure function of (mode, public, secret).
    function automatic logic [W-1:0] declassify
        (input logic secure, input logic [W-1:0] pub, input logic [W-1:0] sec);
`ifdef LEAK_BUG
        // BUG: the secret is mixed in even in secure_mode -> it leaks.
        declassify = secure ? (pub ^ sec) : (pub ^ sec);
`else
        // Correct: in secure_mode the secret is gated off entirely.
        declassify = secure ? pub : (pub ^ sec);
`endif
    endfunction

    assign pub_out = declassify(secure_mode, public_in, secret);

`ifndef SYNTHESIS
    // ---- information-flow monitor (simulation only) --------------------
    // Self-composition reference: the SAME function with the secret scrubbed
    // to zero.  Any dependence of pub_out on `secret` shows up as a mismatch.
    logic [W-1:0] pub_out_scrubbed;
    assign pub_out_scrubbed = declassify(secure_mode, public_in, {W{1'b0}});

    // Non-interference under the declassification policy:
    //   in secure_mode, the secret must not change the public output.
    a_no_secret_leak: assert property (@(posedge clk) disable iff(!rst_n)
        secure_mode |-> (pub_out == pub_out_scrubbed));
`endif
endmodule
