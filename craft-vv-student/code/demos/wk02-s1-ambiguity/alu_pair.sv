// ============================================================
//  alu_pair.sv -- both readings of the overflow sentence, side by side.
//  Same a, b, op into Engineer A's part and Engineer B's part; the
//  testbench watches both `ovf` outputs at once. Steps 0-1 elaborate
//  this; step 2 moves to the course ALU (dut/alu.sv).
// ============================================================
module alu_pair #(
    parameter int WIDTH = 8
) (
    input  logic [WIDTH-1:0] a,
    input  logic [WIDTH-1:0] b,
    input  logic [2:0]       op,
    output logic [WIDTH-1:0] result_s,   // Engineer A: "fit" read as signed
    output logic             ovf_s,
    output logic [WIDTH-1:0] result_c,   // Engineer B: "fit" read as unsigned
    output logic             ovf_c
);
    alu_ovf_signed #(.WIDTH(WIDTH)) u_signed
        (.a(a), .b(b), .op(op), .result(result_s), .ovf(ovf_s));

    alu_ovf_carry #(.WIDTH(WIDTH)) u_carry
        (.a(a), .b(b), .op(op), .result(result_c), .ovf(ovf_c));
endmodule
