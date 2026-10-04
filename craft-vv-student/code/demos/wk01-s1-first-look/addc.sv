// ============================================================
//  addc.sv -- the ADD slice of the Week 1 ALU, small enough for one slide.
//  Combinational: two 8-bit operands in, sum and carry_out back.
//
//  This is the version that came back from review with an "optimization"
//  everyone waved through: adding a number to itself is a shift, so the
//  a == b case can skip the adder.
//
//  One line below is wrong. Every test this block has ever met said PASS.
// ============================================================
module addc (
    input  logic [7:0] a,
    input  logic [7:0] b,
    output logic [7:0] sum,
    output logic       carry_out
);
    logic [8:0] ext;
    assign ext       = (a == b) ? {1'b0, a << 1}        // "a + a is a shift"
                                : {1'b0, a} + {1'b0, b};
    assign sum       = ext[7:0];
    assign carry_out = ext[8];
endmodule
