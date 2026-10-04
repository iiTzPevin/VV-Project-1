"""Golden ISS + mini-assembler for the CRAFT RV32I capstone core (Track 1).

This is the executable specification the scoreboard compares the DUT against.
Supported subset (matches capstone/riscv/rv32i_core.sv and SPEC.md):

    add sub and or xor  addi andi ori  lw sw  beq  jal

Semantics: single-cycle -- exactly one instruction retires per clock. x0 is
hardwired to 0. Harvard memories. Data memory is a small directly-mapped word
array indexed by (addr >> 2) & (DMEM_WORDS-1), high address bits ignored,
mirroring rv32i_dmem.sv.

Usage:
    from models.rv32i_model import RV32I, ADDI, ADD, SW, LW, BEQ, JAL, assemble
    words = assemble([ADDI(1, 0, 5), ADD(3, 1, 1), BEQ(0, 0, 0)])
    iss = RV32I(words); iss.run(20)
    assert iss.reg(3) == 10
"""

IMEM_WORDS = 64
DMEM_WORDS = 64
XMASK = (1 << 32) - 1

# --- opcodes ---
OP_RTYPE  = 0b0110011
OP_ITYPE  = 0b0010011
OP_LOAD   = 0b0000011
OP_STORE  = 0b0100011
OP_BRANCH = 0b1100011
OP_JAL    = 0b1101111


def _u(x, bits):
    return x & ((1 << bits) - 1)


def _sext(v, bits):
    return v - (1 << bits) if (v >> (bits - 1)) & 1 else v


# --- instruction encoders (raw field packers) ---
def enc_r(funct7, rs2, rs1, funct3, rd, opcode):
    return ((_u(funct7, 7) << 25) | (_u(rs2, 5) << 20) | (_u(rs1, 5) << 15) |
            (_u(funct3, 3) << 12) | (_u(rd, 5) << 7) | _u(opcode, 7))


def enc_i(imm, rs1, funct3, rd, opcode):
    return ((_u(imm, 12) << 20) | (_u(rs1, 5) << 15) | (_u(funct3, 3) << 12) |
            (_u(rd, 5) << 7) | _u(opcode, 7))


def enc_s(imm, rs2, rs1, funct3, opcode):
    imm = _u(imm, 12)
    return (((imm >> 5) << 25) | (_u(rs2, 5) << 20) | (_u(rs1, 5) << 15) |
            (_u(funct3, 3) << 12) | ((imm & 0x1f) << 7) | _u(opcode, 7))


def enc_b(imm, rs2, rs1, funct3, opcode):
    imm = _u(imm, 13)                       # imm[12:1]; bit0 must be 0
    b12 = (imm >> 12) & 1
    b11 = (imm >> 11) & 1
    b10_5 = (imm >> 5) & 0x3f
    b4_1 = (imm >> 1) & 0xf
    return ((b12 << 31) | (b10_5 << 25) | (_u(rs2, 5) << 20) | (_u(rs1, 5) << 15) |
            (_u(funct3, 3) << 12) | (b4_1 << 8) | (b11 << 7) | _u(opcode, 7))


def enc_j(imm, rd, opcode):
    imm = _u(imm, 21)                       # imm[20:1]; bit0 must be 0
    b20 = (imm >> 20) & 1
    b19_12 = (imm >> 12) & 0xff
    b11 = (imm >> 11) & 1
    b10_1 = (imm >> 1) & 0x3ff
    return ((b20 << 31) | (b10_1 << 21) | (b11 << 20) | (b19_12 << 12) |
            (_u(rd, 5) << 7) | _u(opcode, 7))


# --- friendly mnemonics (registers are ints 0..31; imm in bytes, signed) ---
def ADD(rd, rs1, rs2):   return enc_r(0b0000000, rs2, rs1, 0b000, rd, OP_RTYPE)
def SUB(rd, rs1, rs2):   return enc_r(0b0100000, rs2, rs1, 0b000, rd, OP_RTYPE)
def AND(rd, rs1, rs2):   return enc_r(0b0000000, rs2, rs1, 0b111, rd, OP_RTYPE)
def OR(rd, rs1, rs2):    return enc_r(0b0000000, rs2, rs1, 0b110, rd, OP_RTYPE)
def XOR(rd, rs1, rs2):   return enc_r(0b0000000, rs2, rs1, 0b100, rd, OP_RTYPE)
def ADDI(rd, rs1, imm):  return enc_i(imm, rs1, 0b000, rd, OP_ITYPE)
def ANDI(rd, rs1, imm):  return enc_i(imm, rs1, 0b111, rd, OP_ITYPE)
def ORI(rd, rs1, imm):   return enc_i(imm, rs1, 0b110, rd, OP_ITYPE)
def LW(rd, rs1, imm):    return enc_i(imm, rs1, 0b010, rd, OP_LOAD)
def SW(rs2, rs1, imm):   return enc_s(imm, rs2, rs1, 0b010, OP_STORE)
def BEQ(rs1, rs2, imm):  return enc_b(imm, rs2, rs1, 0b000, OP_BRANCH)
def JAL(rd, imm):        return enc_j(imm, rd, OP_JAL)


def assemble(program):
    """program: iterable of already-encoded 32-bit words. Returns a list."""
    return [w & XMASK for w in program]


def to_hex_lines(words, n=IMEM_WORDS):
    """Render words as $readmemh lines (8 hex digits each), padded to n."""
    padded = list(words) + [0] * (n - len(words))
    return [f"{w & XMASK:08x}" for w in padded[:n]]


class RV32I:
    """Single-cycle instruction-set simulator for the supported subset."""

    def __init__(self, imem_words=None, imem_size=IMEM_WORDS, dmem_size=DMEM_WORDS):
        self.regs = [0] * 32
        self.pc = 0
        self.imem_size = imem_size
        self.dmem_size = dmem_size
        self.imem = [0] * imem_size
        if imem_words:
            for i, w in enumerate(imem_words):
                self.imem[i] = w & XMASK
        self.dmem = [0] * dmem_size

    def reg(self, i):
        return 0 if i == 0 else self.regs[i] & XMASK

    def _w(self, i, v):
        if i != 0:
            self.regs[i] = v & XMASK

    def load_word(self, addr):
        return self.dmem[(addr >> 2) % self.dmem_size]

    def step(self):
        instr = self.imem[(self.pc >> 2) % self.imem_size]
        opcode = instr & 0x7f
        rd = (instr >> 7) & 0x1f
        funct3 = (instr >> 12) & 0x7
        rs1 = (instr >> 15) & 0x1f
        rs2 = (instr >> 20) & 0x1f
        funct7 = (instr >> 25) & 0x7f

        imm_i = _sext((instr >> 20) & 0xfff, 12)
        imm_s = _sext((((instr >> 25) & 0x7f) << 5) | ((instr >> 7) & 0x1f), 12)
        imm_b = _sext(((((instr >> 31) & 1) << 12) | (((instr >> 7) & 1) << 11) |
                       (((instr >> 25) & 0x3f) << 5) | (((instr >> 8) & 0xf) << 1)), 13)
        imm_j = _sext(((((instr >> 31) & 1) << 20) | (((instr >> 12) & 0xff) << 12) |
                       (((instr >> 20) & 1) << 11) | (((instr >> 21) & 0x3ff) << 1)), 21)

        a = self.reg(rs1)
        b = self.reg(rs2)
        next_pc = (self.pc + 4) & XMASK

        if opcode == OP_RTYPE:
            if funct3 == 0b000:
                r = (a - b) if (funct7 == 0b0100000) else (a + b)
            elif funct3 == 0b111:
                r = a & b
            elif funct3 == 0b110:
                r = a | b
            elif funct3 == 0b100:
                r = a ^ b
            else:
                r = a + b
            self._w(rd, r)
        elif opcode == OP_ITYPE:
            imm = imm_i & XMASK
            if funct3 == 0b000:
                r = a + imm_i
            elif funct3 == 0b111:
                r = a & imm
            elif funct3 == 0b110:
                r = a | imm
            else:
                r = a + imm_i
            self._w(rd, r)
        elif opcode == OP_LOAD:
            addr = (a + imm_i) & XMASK
            self._w(rd, self.load_word(addr))
        elif opcode == OP_STORE:
            addr = (a + imm_s) & XMASK
            self.dmem[(addr >> 2) % self.dmem_size] = b & XMASK
        elif opcode == OP_BRANCH:
            if a == b:                        # BEQ only in this subset
                next_pc = (self.pc + imm_b) & XMASK
        elif opcode == OP_JAL:
            self._w(rd, (self.pc + 4) & XMASK)
            next_pc = (self.pc + imm_j) & XMASK
        # else: unsupported opcode -> nop

        self.pc = next_pc

    def run(self, n):
        for _ in range(n):
            self.step()
