// ============================================================
//  step2_vacuity.sv -- the overflow property a student writes for HW7,
//  plus the covers that prove -- or disprove -- it was ever exercised.
//
//  a_overwrite_dropped is a correct property. Whether it is EVIDENCE
//  depends on the stimulus: if (full && wr_en) never happens, the
//  implication holds on every cycle and checks nothing. The two covers
//  measure exactly that, weakest first:
//      c_full            -- did the FIFO ever even fill?
//      c_overwrite_seen  -- was an over-write ever attempted?
//  Compiled with --assert --coverage-user; after the run the Makefile
//  prints both counts (show_covers.py reads Verilator's coverage.dat).
// ============================================================
module step2_vacuity (
    input logic clk,
    input logic rst_n,
    input logic wr_en,
    input logic full,
    input logic do_wr
);
    // "a write is never committed while the FIFO is full"
    a_overwrite_dropped: assert property (@(posedge clk) disable iff(!rst_n)
        (full && wr_en) |-> !do_wr);

    // non-vacuity, measured: count the cycles the antecedent was alive
    c_full: cover property (@(posedge clk) full);
    c_overwrite_seen: cover property (@(posedge clk) full && wr_en);
endmodule

bind fifo step2_vacuity u_vac (.*);
