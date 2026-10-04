// ============================================================
//  fifo_sva.sv  --  CRAFT V&V Week 7 : concurrent-SVA checker for fifo.sv
//
//  A *checker* module (no functional logic) that observes the FIFO and
//  asserts the contract from dut/specs/fifo.md as concurrent SVA. It is
//  attached to every fifo instance with a `bind` (see dut/fifo_bind.sv),
//  so fifo.sv itself is never edited.
//
//  Because it is bound *inside* the fifo scope with `.*`, the checker can
//  see the FIFO's internal control signals (cnt, do_wr, do_rd) as well as
//  its ports -- exactly the observability that assertion-based verification
//  buys you over black-box scoreboarding.
//
//  Enable with Verilator's `--assert`; every property below must HOLD on the
//  clean RTL and FIRE (=> sim error => mutant found) on a broken FIFO.
//  Written for the yosys-0.33 / Verilator-5.020 SVA subset: plain
//  `assert property (@(posedge clk) disable iff(!rst_n) <expr>)`, small $past
//  via $stable only.
// ============================================================
module fifo_sva #(
    parameter int WIDTH = 8,
    parameter int DEPTH = 8
) (
    input logic                    clk,
    input logic                    rst_n,
    input logic                    wr_en,
    input logic                    rd_en,
    input logic [WIDTH-1:0]        rd_data,
    input logic                    full,
    input logic                    empty,
    input logic [$clog2(DEPTH):0]  count,
    // internal FIFO signals, reached through the bind's `.*`:
    input logic                    do_wr,   // committed write this cycle
    input logic                    do_rd    // committed read  this cycle
);

    // 1) No overflow: a write is never *committed* while the FIFO is full.
    //    Catches ignore_full (do_wr = wr_en) and full-flag bugs that let
    //    writes through.
    a_no_overflow: assert property (@(posedge clk) disable iff(!rst_n)
        full |-> !do_wr);

    // 2) No underflow: a read is never *committed* while the FIFO is empty.
    a_no_underflow: assert property (@(posedge clk) disable iff(!rst_n)
        empty |-> !do_rd);

    // 3) full flag is exactly count == DEPTH.
    a_full_iff_depth: assert property (@(posedge clk) disable iff(!rst_n)
        full == (count == DEPTH));

    // 4) empty flag is exactly count == 0.
    a_empty_iff_zero: assert property (@(posedge clk) disable iff(!rst_n)
        empty == (count == 0));

    // 5) Occupancy is always a legal FIFO depth: 0 <= count <= DEPTH.
    //    (count is unsigned, so the lower bound is structural; we assert the
    //    upper bound, which catches overflow / count-arithmetic bugs.)
    a_count_in_range: assert property (@(posedge clk) disable iff(!rst_n)
        count <= DEPTH);

    // 6) FWFT head stability: while the FIFO is non-empty and no read is
    //    committed, the visible head (rd_data) must not change.  A read is
    //    the only legal reason for the head to advance; a write cannot touch
    //    the head unless the FIFO is empty (then rd_ptr==wr_ptr) or full
    //    (then the write is dropped).  Catches rd_data_wrptr (head tracks the
    //    write pointer) and any bug that lets a write disturb the head.
    a_head_stable: assert property (@(posedge clk) disable iff(!rst_n)
        (!empty && !do_rd) |=> $stable(rd_data));

    // 7) Count tracks the committed operations, one step at a time:
    //    write-only  => count increments,
    //    read-only   => count decrements,
    //    idle or simultaneous read+write => count holds.
    //    Together these catch count_wr_dec, count_rd_inc, and the
    //    simultaneous-r+w observability trap (count grows on r+w).
    a_count_up:   assert property (@(posedge clk) disable iff(!rst_n)
        (do_wr && !do_rd) |=> (count == $past(count) + 1'b1));

    a_count_dn:   assert property (@(posedge clk) disable iff(!rst_n)
        (do_rd && !do_wr) |=> (count == $past(count) - 1'b1));

    a_count_hold: assert property (@(posedge clk) disable iff(!rst_n)
        (do_wr == do_rd) |=> $stable(count));

endmodule
