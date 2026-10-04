// ============================================================
//  alu_ovf_signed.sv -- Engineer A's part.
//  Week 2, Session 1 demo: one spec sentence, two compliant parts.
//
//  The sentence under test (dut/specs/alu.md, Flags):
//      "overflow -- set when the mathematical result of an arithmetic
//       operation (ADD, SUB) does not fit in WIDTH bits."
//  Engineer A reads "fit" as SIGNED: the two's-complement result lies
//  outside [-2^(WIDTH-1), 2^(WIDTH-1)-1].
//
//  diff this file against alu_ovf_carry.sv: the two `ovf` lines are the
//  only difference. Both parts satisfy the sentence as written.
//  Arithmetic ops only -- the ambiguity lives in ADD and SUB.
// ============================================================
module alu_ovf_signed #(
    parameter int WIDTH = 8
) (
    input  logic [WIDTH-1:0] a,
    input  logic [WIDTH-1:0] b,
    input  logic [2:0]       op,
    output logic [WIDTH-1:0] result,
    output logic             ovf
);
    logic [WIDTH:0] ext;

    always_comb begin
        ext    = '0;
        result = '0;
        ovf    = 1'b0;
        case (op)
            3'd0: begin                                   // ADD
                ext    = {1'b0, a} + {1'b0, b};
                result = ext[WIDTH-1:0];
                ovf    = (a[WIDTH-1] == b[WIDTH-1]) && (result[WIDTH-1] != a[WIDTH-1]);
            end
            3'd1: begin                                   // SUB
                ext    = {1'b0, a} - {1'b0, b};
                result = ext[WIDTH-1:0];
                ovf    = (a[WIDTH-1] != b[WIDTH-1]) && (result[WIDTH-1] != a[WIDTH-1]);
            end
            default: ;                                    // not this demo's fight
        endcase
    end
endmodule
