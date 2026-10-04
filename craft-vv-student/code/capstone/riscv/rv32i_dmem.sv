// ============================================================
//  rv32i_dmem.sv  --  sim data memory: async read, synchronous write.
//  Small directly-mapped word array: index = addr[AW+1:2] (high addr bits
//  ignored), mirroring lib/models/rv32i_model.py. A second async read port
//  (dbg_idx/dbg_data) gives the testbench observability into memory contents.
//  Part of the sim harness only, NOT the mutated DUT.
// ============================================================
module rv32i_dmem #(
    parameter int WORDS = 64
) (
    input  logic          clk,
    input  logic [31:0]   addr,
    input  logic [31:0]   wdata,
    input  logic          we,
    output logic [31:0]   rdata,
    input  logic [$clog2(WORDS)-1:0] dbg_idx,
    output logic [31:0]   dbg_data
);
    localparam int AW = $clog2(WORDS);
    logic [31:0] mem [0:WORDS-1];
    logic [AW-1:0] widx;
    assign widx = addr[AW+1:2];

    initial begin
        for (int i = 0; i < WORDS; i++) mem[i] = 32'h0000_0000;
    end

    assign rdata    = mem[widx];
    assign dbg_data = mem[dbg_idx];

    always_ff @(posedge clk) begin
        if (we) mem[widx] <= wdata;
    end
endmodule
