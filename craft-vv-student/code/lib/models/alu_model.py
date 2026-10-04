"""Golden reference model for the CRAFT ALU (dut/alu.sv).

This is the specification made executable. The testbench compares the DUT
against this model; a mutant is *found* when DUT and model disagree.
"""
from dataclasses import dataclass

OP_ADD, OP_SUB, OP_AND, OP_OR, OP_XOR, OP_SLT, OP_SLL, OP_SRL = range(8)
OP_NAMES = {OP_ADD: "ADD", OP_SUB: "SUB", OP_AND: "AND", OP_OR: "OR",
            OP_XOR: "XOR", OP_SLT: "SLT", OP_SLL: "SLL", OP_SRL: "SRL"}


@dataclass
class AluResult:
    result: int
    zero: int
    carry: int
    overflow: int


def alu_model(a: int, b: int, op: int, width: int = 8) -> AluResult:
    mask = (1 << width) - 1
    sign = 1 << (width - 1)
    a &= mask
    b &= mask
    sh_bits = max(1, (width - 1).bit_length())      # $clog2(width)
    sh = b & ((1 << sh_bits) - 1)

    def signed(x):
        return x - (1 << width) if (x & sign) else x

    carry = 0
    overflow = 0

    if op == OP_ADD:
        ext = a + b
        result = ext & mask
        carry = (ext >> width) & 1
        overflow = int((a & sign) == (b & sign) and (result & sign) != (a & sign))
    elif op == OP_SUB:
        ext = (a - b) & ((1 << (width + 1)) - 1)
        result = ext & mask
        carry = (ext >> width) & 1                  # borrow
        overflow = int((a & sign) != (b & sign) and (result & sign) != (a & sign))
    elif op == OP_AND:
        result = a & b
    elif op == OP_OR:
        result = a | b
    elif op == OP_XOR:
        result = a ^ b
    elif op == OP_SLT:
        result = 1 if signed(a) < signed(b) else 0
    elif op == OP_SLL:
        result = (a << sh) & mask
    elif op == OP_SRL:
        result = (a >> sh) & mask
    else:
        result = 0

    zero = int(result == 0)
    return AluResult(result & mask, zero, carry & 1, overflow & 1)
