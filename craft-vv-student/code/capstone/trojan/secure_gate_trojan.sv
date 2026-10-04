// ============================================================
//  secure_gate_trojan.sv  --  CRAFT V&V capstone Track 3 (security) : PLANTED variant
//  Functionally identical to secure_gate_clean.sv for EVERY input EXCEPT one
//  hidden magic key. On key == MAGIC_KEY the gate silently unlocks and leaks
//  data, even though the correct EXPECTED_KEY was never supplied. The trigger is
//  a single 32-bit value, so random stimulus is astronomically unlikely to hit
//  it -- finding this needs a targeted property / formal proof of the security
//  contract, not more random vectors. Spec: capstone/trojan/SPEC.md
//  DO NOT ship: this is the adversarial target students must catch.
//  Module name is `secure_gate` (same as the clean variant).
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
    // Hidden backdoor trigger. Dormant for all keys except this exact value.
    localparam logic [31:0] MAGIC_KEY = 32'hDEAD_BEEF;

    logic key_ok, backdoor;
    assign key_ok   = (key == EXPECTED_KEY);
    assign backdoor = (key == MAGIC_KEY);          // <-- TROJAN trigger
    assign unlocked = key_ok | backdoor;           // <-- leaks on the magic key

    assign data_out = unlocked ? data_in : '0;

    logic [7:0] cnt;
    always_ff @(posedge clk) begin
        if (!rst_n)        cnt <= 8'd0;
        else if (unlocked) cnt <= cnt + 8'd1;
    end
    assign access_count = cnt;
endmodule
