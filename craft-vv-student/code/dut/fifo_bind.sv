// ============================================================
//  fifo_bind.sv  --  attach the SVA checker to every fifo instance.
//
//  `bind` injects an instance of fifo_sva *inside* each fifo without editing
//  fifo.sv.  The `.*` wildcard connects each checker port to the signal of
//  the same name visible in the fifo scope -- that includes fifo's ports
//  (clk, rst_n, wr_en, rd_en, rd_data, full, empty, count) AND its internal
//  control signals (do_wr, do_rd), which is how the checker observes commits.
//
//  The checker's parameters are forwarded from the FIFO's own WIDTH/DEPTH so
//  a bind to a differently-sized FIFO still checks the right depth.
// ============================================================
bind fifo fifo_sva #(.WIDTH(WIDTH), .DEPTH(DEPTH)) u_sva (.*);
