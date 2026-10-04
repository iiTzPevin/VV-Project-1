// ============================================================
//  uart_bind.sv  --  attach the SVA checker to every uart instance.
//  Same mechanism as fifo_bind.sv: `bind` injects uart_sva inside the
//  uart scope; `.*` connects ports AND internal state (t_state, r_state,
//  baud counters) by name, so uart.sv is never edited.
// ============================================================
bind uart uart_sva #(.CLKS_PER_BIT(CLKS_PER_BIT), .WIDTH(WIDTH)) u_sva (.*);
