// ============================================================
//  secure_gate_clean.sv  --  CRAFT V&V capstone Track 3 (security) : CLEAN variant
//  A key-comparator access gate. Data passes through ONLY when the supplied key
//  matches the expected key; otherwise the output is masked to zero and the gate
//  reports locked. An access counter increments each cycle the gate is unlocked.
//  This is the golden, trojan-free reference. Spec: capstone/trojan/SPEC.md
//  Module name is `secure_gate` (same as the trojan variant) so the same
//  testbench/Makefile brings up whichever file is chosen as the DUT.
//  Style: synthesizable, runs under Icarus and Verilator.
// ============================================================
module secure_gate #(
    parameter int          DW           = 8,
    parameter logic [31:0] EXPECTED_KEY = 32'hA5A5_1234
) (
    input  logic          clk,
    input  logic          rst_n,
    input  logic [31:0]   key,
    input  logic [DW-1:0] data_in,
    output logic          unlocked,
    output logic [DW-1:0] data_out,
    output logic [7:0]    access_count
);
    // Access is granted iff the full key matches. (CLEAN: no other path.)
    logic key_ok;
    assign key_ok   = (key == EXPECTED_KEY);
    assign unlocked = key_ok;

    // Data is released only while unlocked; masked to zero otherwise.
    assign data_out = unlocked ? data_in : '0;

    // Observable side effect: count unlocked cycles.
    logic [7:0] cnt;
    always_ff @(posedge clk) begin
        if (!rst_n)        cnt <= 8'd0;
        else if (unlocked) cnt <= cnt + 8'd1;
    end
    assign access_count = cnt;
endmodule
