// ============================================================
//  rv32i_core.sv  --  CRAFT V&V capstone Track 1 : small RV32I core
//  Single-cycle (one instruction retires per clock). x0 hardwired 0.
//  Supported subset: add sub and or xor addi andi ori lw sw beq jal
//  Harvard: async-read imem/dmem, synchronous writes (regfile, dmem, pc).
//  Spec: capstone/riscv/SPEC.md   Reference ISS: lib/models/rv32i_model.py
//  Style: synthesizable, runs under Icarus and Verilator (no #delay, no X reliance).
//  NOTE: dbg_sel/dbg_reg are an observability hook (a synthesizable read mux) so
//  the testbench can score architectural register state without hierarchical peeks.
// ============================================================
module rv32i_core #(
    parameter int XLEN = 32
) (
    input  logic            clk,
    input  logic            rst_n,
    // instruction memory (combinational read at PC)
    output logic [XLEN-1:0] imem_addr,
    input  logic [XLEN-1:0] imem_rdata,
    // data memory (combinational read, synchronous write)
    output logic [XLEN-1:0] dmem_addr,
    output logic [XLEN-1:0] dmem_wdata,
    output logic            dmem_we,
    input  logic [XLEN-1:0] dmem_rdata,
    // debug observability (read a register combinationally)
    input  logic [4:0]      dbg_sel,
    output logic [XLEN-1:0] dbg_reg
);
    // --- opcodes (RV32I) ---
    localparam logic [6:0] OP_RTYPE  = 7'b0110011;
    localparam logic [6:0] OP_ITYPE  = 7'b0010011;
    localparam logic [6:0] OP_LOAD   = 7'b0000011;
    localparam logic [6:0] OP_STORE  = 7'b0100011;
    localparam logic [6:0] OP_BRANCH = 7'b1100011;
    localparam logic [6:0] OP_JAL    = 7'b1101111;

    // --- ALU control encodings ---
    localparam logic [2:0] ALU_ADD = 3'd0;
    localparam logic [2:0] ALU_SUB = 3'd1;
    localparam logic [2:0] ALU_AND = 3'd2;
    localparam logic [2:0] ALU_OR  = 3'd3;
    localparam logic [2:0] ALU_XOR = 3'd4;

    // --- architectural state ---
    logic [XLEN-1:0] pc;
    logic [XLEN-1:0] regs [0:31];

    // --- instruction fetch / decode ---
    logic [XLEN-1:0] instr;
    assign instr = imem_rdata;

    logic [6:0] opcode;
    logic [4:0] rd, rs1, rs2;
    logic [2:0] funct3;
    logic [6:0] funct7;
    assign opcode = instr[6:0];
    assign rd     = instr[11:7];
    assign funct3 = instr[14:12];
    assign rs1    = instr[19:15];
    assign rs2    = instr[24:20];
    assign funct7 = instr[31:25];

    // --- immediates ---
    logic [XLEN-1:0] imm_i, imm_s, imm_b, imm_j;
    assign imm_i = {{20{instr[31]}}, instr[31:20]};
    assign imm_s = {{20{instr[31]}}, instr[31:25], instr[11:7]};
    assign imm_b = {{19{instr[31]}}, instr[31], instr[7], instr[30:25], instr[11:8], 1'b0};
    assign imm_j = {{11{instr[31]}}, instr[31], instr[19:12], instr[20], instr[30:21], 1'b0};

    // --- register file read (x0 reads as 0) ---
    logic [XLEN-1:0] rs1_val, rs2_val;
    assign rs1_val = (rs1 == 5'd0) ? '0 : regs[rs1];
    assign rs2_val = (rs2 == 5'd0) ? '0 : regs[rs2];

    // --- control decode ---
    logic       reg_write, mem_read, mem_write, branch, jump, alu_src;
    logic [2:0] alu_ctrl;
    logic [1:0] wb_sel;                 // 00=alu, 01=mem, 10=pc+4
    logic [XLEN-1:0] imm;

    always_comb begin
        reg_write = 1'b0;
        mem_read  = 1'b0;
        mem_write = 1'b0;
        branch    = 1'b0;
        jump      = 1'b0;
        alu_src   = 1'b0;
        alu_ctrl  = ALU_ADD;
        wb_sel    = 2'b00;
        imm       = imm_i;
        case (opcode)
            OP_RTYPE: begin
                reg_write = 1'b1;
                alu_src   = 1'b0;
                case (funct3)
                    3'b000:  alu_ctrl = funct7[5] ? ALU_SUB : ALU_ADD;
                    3'b111:  alu_ctrl = ALU_AND;
                    3'b110:  alu_ctrl = ALU_OR;
                    3'b100:  alu_ctrl = ALU_XOR;
                    default: alu_ctrl = ALU_ADD;
                endcase
            end
            OP_ITYPE: begin
                reg_write = 1'b1;
                alu_src   = 1'b1;
                imm       = imm_i;
                case (funct3)
                    3'b000:  alu_ctrl = ALU_ADD;   // addi
                    3'b111:  alu_ctrl = ALU_AND;   // andi
                    3'b110:  alu_ctrl = ALU_OR;    // ori
                    default: alu_ctrl = ALU_ADD;
                endcase
            end
            OP_LOAD: begin
                reg_write = 1'b1;
                alu_src   = 1'b1;
                imm       = imm_i;
                alu_ctrl  = ALU_ADD;
                mem_read  = 1'b1;
                wb_sel    = 2'b01;
            end
            OP_STORE: begin
                alu_src   = 1'b1;
                imm       = imm_s;
                alu_ctrl  = ALU_ADD;
                mem_write = 1'b1;
            end
            OP_BRANCH: begin
                branch    = 1'b1;
                imm       = imm_b;
            end
            OP_JAL: begin
                reg_write = 1'b1;
                jump      = 1'b1;
                imm       = imm_j;
                wb_sel    = 2'b10;
            end
            default: ;                             // unsupported -> nop
        endcase
    end

    // --- ALU ---
    logic [XLEN-1:0] alu_b, alu_result;
    always_comb begin
        alu_b = alu_src ? imm : rs2_val;
        case (alu_ctrl)
            ALU_ADD: alu_result = rs1_val + alu_b;
            ALU_SUB: alu_result = rs1_val - alu_b;
            ALU_AND: alu_result = rs1_val & alu_b;
            ALU_OR:  alu_result = rs1_val | alu_b;
            ALU_XOR: alu_result = rs1_val ^ alu_b;
            default: alu_result = rs1_val + alu_b;
        endcase
    end

    // --- branch/jump resolution (BEQ only in this subset) ---
    logic beq_taken;
    assign beq_taken = branch & (rs1_val == rs2_val);

    logic [XLEN-1:0] pc_plus4, pc_target, pc_next;
    assign pc_plus4  = pc + 32'd4;
    assign pc_target = pc + imm;                   // BEQ or JAL target
    assign pc_next   = (jump | beq_taken) ? pc_target : pc_plus4;

    // --- writeback mux ---
    logic [XLEN-1:0] wb_data;
    always_comb begin
        case (wb_sel)
            2'b00:   wb_data = alu_result;
            2'b01:   wb_data = dmem_rdata;
            2'b10:   wb_data = pc_plus4;
            default: wb_data = alu_result;
        endcase
    end

    // --- memory interface ---
    assign imem_addr  = pc;
    assign dmem_addr  = alu_result;
    assign dmem_wdata = rs2_val;
    assign dmem_we    = mem_write;

    // --- sequential state ---
    always_ff @(posedge clk) begin
        if (!rst_n) pc <= '0;
        else        pc <= pc_next;
    end

    always_ff @(posedge clk) begin
        if (reg_write && (rd != 5'd0)) regs[rd] <= wb_data;
    end

    // --- debug read port ---
    assign dbg_reg = (dbg_sel == 5'd0) ? '0 : regs[dbg_sel];
endmodule
