// ============================================================
//  axi_subsystem.sv  --  CRAFT V&V capstone Track 2 : bus interconnect subsystem
//  A 2-master round-robin arbiter feeding a simple address-mapped, single-cycle
//  request bus with three slaves:
//     region 0 (addr[15:12]==0) : peripheral REG0 -- 4 x 32-bit scratch registers
//     region 1 (addr[15:12]==1) : peripheral REG1 -- 4 x 32-bit scratch registers
//     region 2 (addr[15:12]==2) : the FWFT FIFO (data port + status port)
//  Transactions complete in the cycle they are granted (comb read, sync write).
//  The rr_arbiter2 module lives in this file (it is part of the mutated DUT);
//  fifo.sv is a separate, un-mutated file compiled alongside.
//  Spec: capstone/axi_subsystem/SPEC.md
//  Style: synthesizable, runs under Icarus and Verilator.
// ============================================================
module rr_arbiter2 (
    input  logic clk,
    input  logic rst_n,
    input  logic req0,
    input  logic req1,
    output logic gnt0,
    output logic gnt1
);
    // `last` = the master granted most recently; next round prefers the other.
    logic last;

    always_comb begin
        gnt0 = 1'b0;
        gnt1 = 1'b0;
        if (last == 1'b0) begin           // last served m0 -> prefer m1
            if (req1)       gnt1 = 1'b1;
            else if (req0)  gnt0 = 1'b1;
        end else begin                    // last served m1 -> prefer m0
            if (req0)       gnt0 = 1'b1;
            else if (req1)  gnt1 = 1'b1;
        end
    end

    always_ff @(posedge clk) begin
        if (!rst_n) last <= 1'b0;
        else if (gnt0) last <= 1'b0;
        else if (gnt1) last <= 1'b1;
    end
endmodule


module axi_subsystem #(
    parameter int DW         = 32,
    parameter int AW         = 16,
    parameter int FIFO_DEPTH = 8
) (
    input  logic          clk,
    input  logic          rst_n,
    // master 0 request/response
    input  logic          m0_req,
    input  logic          m0_we,
    input  logic [AW-1:0] m0_addr,
    input  logic [DW-1:0] m0_wdata,
    output logic          m0_gnt,
    output logic [DW-1:0] m0_rdata,
    output logic          m0_rvalid,
    // master 1 request/response
    input  logic          m1_req,
    input  logic          m1_we,
    input  logic [AW-1:0] m1_addr,
    input  logic [DW-1:0] m1_wdata,
    output logic          m1_gnt,
    output logic [DW-1:0] m1_rdata,
    output logic          m1_rvalid
);
    localparam logic [3:0] REGION_REG0 = 4'h0;
    localparam logic [3:0] REGION_REG1 = 4'h1;
    localparam logic [3:0] REGION_FIFO = 4'h2;

    // --- arbitration ---
    logic gnt0, gnt1, any_gnt;
    rr_arbiter2 u_arb (
        .clk (clk), .rst_n (rst_n),
        .req0 (m0_req), .req1 (m1_req),
        .gnt0 (gnt0),  .gnt1 (gnt1)
    );
    assign any_gnt = gnt0 | gnt1;

    // --- selected (granted) master's request onto the bus ---
    logic          sel_we;
    logic [AW-1:0] sel_addr;
    logic [DW-1:0] sel_wdata;
    assign sel_we    = gnt0 ? m0_we    : m1_we;
    assign sel_addr  = gnt0 ? m0_addr  : m1_addr;
    assign sel_wdata = gnt0 ? m0_wdata : m1_wdata;

    // --- address decode ---
    logic [3:0] region;
    logic [1:0] widx;
    assign region = sel_addr[15:12];
    assign widx   = sel_addr[3:2];

    logic sel_reg0, sel_reg1, sel_fifo;
    assign sel_reg0 = any_gnt & (region == REGION_REG0);
    assign sel_reg1 = any_gnt & (region == REGION_REG1);
    assign sel_fifo = any_gnt & (region == REGION_FIFO);

    // --- scratch register peripherals ---
    logic [DW-1:0] reg0 [0:3];
    logic [DW-1:0] reg1 [0:3];
    logic wr_reg0, wr_reg1;
    assign wr_reg0 = sel_reg0 & sel_we;
    assign wr_reg1 = sel_reg1 & sel_we;

    always_ff @(posedge clk) begin
        if (!rst_n) begin
            for (int i = 0; i < 4; i++) begin
                reg0[i] <= '0;
                reg1[i] <= '0;
            end
        end else begin
            if (wr_reg0) reg0[widx] <= sel_wdata;
            if (wr_reg1) reg1[widx] <= sel_wdata;
        end
    end

    // --- FIFO peripheral (data port at offset 0, status port at offset 4) ---
    logic fifo_data_sel, fifo_stat_sel, fifo_wr, fifo_rd;
    assign fifo_data_sel = sel_fifo & (widx == 2'd0);
    assign fifo_stat_sel = sel_fifo & (widx == 2'd1);
    assign fifo_wr = fifo_data_sel & sel_we;          // write to data port = push
    assign fifo_rd = fifo_data_sel & ~sel_we;         // read of data port = pop

    logic [DW-1:0]              fifo_rdata;
    logic                       fifo_full, fifo_empty;
    logic [$clog2(FIFO_DEPTH):0] fifo_count;
    fifo #(.WIDTH(DW), .DEPTH(FIFO_DEPTH)) u_fifo (
        .clk     (clk),
        .rst_n   (rst_n),
        .wr_en   (fifo_wr),
        .wr_data (sel_wdata),
        .rd_en   (fifo_rd),
        .rd_data (fifo_rdata),
        .full    (fifo_full),
        .empty   (fifo_empty),
        .count   (fifo_count)
    );

    // status word: { .., count, full(bit1), empty(bit0) }
    logic [DW-1:0] fifo_status;
    assign fifo_status = {{(DW-6){1'b0}}, fifo_count[3:0], fifo_full, fifo_empty};

    // --- read-data mux ---
    logic [DW-1:0] bus_rdata;
    always_comb begin
        case (region)
            REGION_REG0: bus_rdata = reg0[widx];
            REGION_REG1: bus_rdata = reg1[widx];
            REGION_FIFO: bus_rdata = fifo_stat_sel ? fifo_status : fifo_rdata;
            default:     bus_rdata = '0;
        endcase
    end

    // --- responses: only the granted master sees rvalid ---
    assign m0_gnt    = gnt0;
    assign m1_gnt    = gnt1;
    assign m0_rdata  = bus_rdata;
    assign m1_rdata  = bus_rdata;
    assign m0_rvalid = gnt0;
    assign m1_rvalid = gnt1;
endmodule
