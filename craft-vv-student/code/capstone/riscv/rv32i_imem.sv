// ============================================================
//  rv32i_imem.sv  --  sim instruction memory (async-read ROM) for the RV32I core.
//  Word-addressed: index = addr[AW+1:2]. Preloaded from program.hex at time 0
//  ($readmemh resolves relative to the simulator's working directory = the
//   Makefile directory, which is capstone/riscv/). Part of the sim harness only,
//  NOT the mutated DUT.
// ============================================================
module rv32i_imem #(
    parameter int WORDS = 64,
    parameter     INIT  = "program.hex"
) (
    input  logic [31:0] addr,
    output logic [31:0] rdata
);
    localparam int AW = $clog2(WORDS);
    logic [31:0] mem [0:WORDS-1];

    initial begin
        for (int i = 0; i < WORDS; i++) mem[i] = 32'h0000_0000;
        $readmemh(INIT, mem);
    end

    assign rdata = mem[addr[AW+1:2]];
endmodule
