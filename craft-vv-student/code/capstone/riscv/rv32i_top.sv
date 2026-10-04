// ============================================================
//  rv32i_top.sv  --  sim harness (cocotb TOPLEVEL) for the RV32I core.
//  Wires the core to instruction + data memories and exposes the core's
//  debug read ports. This file + the memories are ALWAYS compiled; only
//  rv32i_core.sv is mutated by the mutation harness (passed as DUT=).
// ============================================================
module rv32i_top #(
    parameter int IMEM_WORDS = 64,
    parameter int DMEM_WORDS = 64
) (
    input  logic        clk,
    input  logic        rst_n,
    // register observability
    input  logic [4:0]  dbg_sel,
    output logic [31:0] dbg_reg,
    // data-memory observability
    input  logic [$clog2(DMEM_WORDS)-1:0] dbg_dmem_idx,
    output logic [31:0] dbg_dmem_data
);
    logic [31:0] imem_addr, imem_rdata;
    logic [31:0] dmem_addr, dmem_wdata, dmem_rdata;
    logic        dmem_we;

    rv32i_core u_core (
        .clk        (clk),
        .rst_n      (rst_n),
        .imem_addr  (imem_addr),
        .imem_rdata (imem_rdata),
        .dmem_addr  (dmem_addr),
        .dmem_wdata (dmem_wdata),
        .dmem_we    (dmem_we),
        .dmem_rdata (dmem_rdata),
        .dbg_sel    (dbg_sel),
        .dbg_reg    (dbg_reg)
    );

    rv32i_imem #(.WORDS(IMEM_WORDS)) u_imem (
        .addr  (imem_addr),
        .rdata (imem_rdata)
    );

    rv32i_dmem #(.WORDS(DMEM_WORDS)) u_dmem (
        .clk      (clk),
        .addr     (dmem_addr),
        .wdata    (dmem_wdata),
        .we       (dmem_we),
        .rdata    (dmem_rdata),
        .dbg_idx  (dbg_dmem_idx),
        .dbg_data (dbg_dmem_data)
    );
endmodule
