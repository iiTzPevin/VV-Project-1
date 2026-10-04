// ============================================================
//  alu.sv  --  CRAFT V&V unifying example #1 : an 8-bit ALU
//  Combinational. Used in Weeks 1-3 (and as a Check-the-Machine target).
//  Spec: dut/specs/alu.md
//  Style: synthesizable, Verilator-friendly (no delays, no X-prop reliance).
// ============================================================
module alu #(
    parameter int WIDTH = 8
) (
    input  logic [WIDTH-1:0] a,
    input  logic [WIDTH-1:0] b,
    input  logic [2:0]       op,
    output logic [WIDTH-1:0] result,
    output logic             zero,
    output logic             carry,
    output logic             overflow
);
    localparam logic [2:0] OP_ADD = 3'd0;
    localparam logic [2:0] OP_SUB = 3'd1;
    localparam logic [2:0] OP_AND = 3'd2;
    localparam logic [2:0] OP_OR  = 3'd3;
    localparam logic [2:0] OP_XOR = 3'd4;
    localparam logic [2:0] OP_SLT = 3'd5;   // signed set-less-than
    localparam logic [2:0] OP_SLL = 3'd6;
    localparam logic [2:0] OP_SRL = 3'd7;

    localparam int SH = $clog2(WIDTH);

    logic [WIDTH:0] add_ext;
    logic [WIDTH:0] sub_ext;

    always_comb begin
        add_ext  = {1'b0, a} + {1'b0, b};
        sub_ext  = {1'b0, a} - {1'b0, b};
        result   = '0;
        carry    = 1'b0;
        overflow = 1'b0;
        unique case (op)
            OP_ADD: begin
                result   = add_ext[WIDTH-1:0];
                carry    = add_ext[WIDTH];
                overflow = (a[WIDTH-1] == b[WIDTH-1]) && (result[WIDTH-1] != a[WIDTH-1]);
            end
            OP_SUB: begin
                result   = sub_ext[WIDTH-1:0];
                carry    = sub_ext[WIDTH];
                overflow = (a[WIDTH-1] != b[WIDTH-1]) && (result[WIDTH-1] != a[WIDTH-1]);
            end
            OP_AND: result = a & b;
            OP_OR:  result = a | b;
            OP_XOR: result = a ^ b;
            OP_SLT: result = ($signed(a) < $signed(b)) ? {{(WIDTH-1){1'b0}}, 1'b1} : '0;
            OP_SLL: result = a << b[SH-1:0];
            OP_SRL: result = a >> b[SH-1:0];
            default: result = '0;
        endcase
        zero = (result == '0);
    end
endmodule
