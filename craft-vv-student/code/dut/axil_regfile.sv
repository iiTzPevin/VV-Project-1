// ============================================================
//  axil_regfile.sv -- CRAFT V&V : register file with access policies
//  Weeks 9-10 : pyuvm environment + automated register (RAL-style) tests.
//  Spec: dut/specs/axil_regfile.md
//
//  A lightweight *synchronous* bus (NOT full AXI, to keep it easy to drive):
//    - one transaction per cycle, qualified by `req`
//    - `we` selects write (1) or read (0)
//    - reads are REGISTERED: `rvalid`/`rdata` appear one cycle after a read req
//
//  Register map + access policies (enforced here, mirrored in RegfileModel):
//    0x0 CTRL    RW
//    0x1 STATUS  RO          (writes ignored; reads a fixed pattern)
//    0x2 SCRATCH RW
//    0x3 INTR    W1C         (write-1-to-clear; hw sets bit0 on a violation)
//    0x4 LOCK    RW          (bit0 = lock enable)
//    0x5 SECURE  locked-RW   (writable only while LOCK.bit0==0)
//    other       reads 0, writes ignored
//
//  Synthesizable; runs under Verilator 5.020 and Icarus 12.
// ============================================================
module axil_regfile (
    input  logic        clk,
    input  logic        rst_n,
    input  logic        req,          // transaction valid this cycle
    input  logic        we,           // 1=write, 0=read
    input  logic [3:0]  addr,         // word address
    input  logic [31:0] wdata,
    output logic [31:0] rdata,        // registered read data
    output logic        rvalid        // read data valid, 1 cycle after a read req
);
    // ---- register map (address decode) ----
    localparam logic [3:0] ADDR_CTRL    = 4'h0;   // RW
    localparam logic [3:0] ADDR_STATUS  = 4'h1;   // RO
    localparam logic [3:0] ADDR_SCRATCH = 4'h2;   // RW
    localparam logic [3:0] ADDR_INTR    = 4'h3;   // W1C
    localparam logic [3:0] ADDR_LOCK    = 4'h4;   // RW (bit0 = lock enable)
    localparam logic [3:0] ADDR_SECURE  = 4'h5;   // locked-RW

    localparam logic [31:0] STATUS_VAL  = 32'h5A5A_0F0F;  // fixed RO read pattern

    // ---- architectural state ----
    logic [31:0] ctrl;
    logic [31:0] status;
    logic [31:0] scratch;
    logic [31:0] intr;
    logic [31:0] lock;
    logic [31:0] secure;

    // security violation: a write to SECURE while locked (latches INTR bit0)
    logic sec_violation;
    assign sec_violation = req & we & (addr == ADDR_SECURE) & lock[0];

    // ---- write path + hardware set of the violation interrupt ----
    always_ff @(posedge clk) begin
        if (!rst_n) begin
            ctrl    <= 32'h0000_0000;
            status  <= STATUS_VAL;
            scratch <= 32'h0000_0000;
            intr    <= 32'h0000_0000;
            lock    <= 32'h0000_0000;
            secure  <= 32'h0000_0000;
        end else begin
            if (req & we) begin
                case (addr)
                    ADDR_CTRL:    ctrl    <= wdata;               // RW
                    ADDR_STATUS:  status  <= status;              // RO: writes ignored
                    ADDR_SCRATCH: scratch <= wdata;              // RW
                    ADDR_INTR:    intr    <= intr & ~wdata;       // W1C: write-1-to-clear
                    ADDR_LOCK:    lock    <= wdata;               // RW
                    ADDR_SECURE:  if (!lock[0]) secure <= wdata;  // locked-RW
                    default:      ;  // unmapped: writes ignored
                endcase
            end
            if (sec_violation) intr <= intr | 32'h0000_0001;      // hw set INTR bit0
        end
    end

    // ---- combinational read mux ----
    logic [31:0] rd_mux;
    always_comb begin
        case (addr)
            ADDR_CTRL:    rd_mux = ctrl;
            ADDR_STATUS:  rd_mux = status;
            ADDR_SCRATCH: rd_mux = scratch;
            ADDR_INTR:    rd_mux = intr;
            ADDR_LOCK:    rd_mux = lock;
            ADDR_SECURE:  rd_mux = secure;
            default:      rd_mux = 32'h0000_0000;   // unmapped reads 0
        endcase
    end

    // ---- registered read data + valid ----
    always_ff @(posedge clk) begin
        if (!rst_n) begin
            rdata  <= 32'h0000_0000;
            rvalid <= 1'b0;
        end else begin
            rvalid <= req & ~we;             // valid one cycle after a read req
            if (req & ~we) rdata <= rd_mux;  // capture the addressed register
        end
    end
endmodule
