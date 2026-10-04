"""STEP 0 -- "I understand the design; let me start writing tests."

No plan. This is what the instinct produces: the operations that are easy to
think of, on the values that come to mind first, checking `result` and
nothing else. It runs green in two seconds, and green feels like progress.

The question the file cannot answer: green against WHAT standard? Score it
against the released mutant pool and the answer arrives as a number. Then we
put the plan on screen: this session derives vplan.md one row at a time,
starting from a requirement Tuesday taught us to sharpen first.
"""
import cocotb

from demo_common import drive, seed, OP_ADD, OP_SUB


@cocotb.test()
async def test_first_instinct(dut):
    seed()
    await drive(dut, 3, 4, OP_ADD)
    assert int(dut.result.value) == 7, "3 + 4"
    await drive(dut, 9, 5, OP_SUB)
    assert int(dut.result.value) == 4, "9 - 5"
    await drive(dut, 10, 10, OP_ADD)
    assert int(dut.result.value) == 20, "10 + 10"
    cocotb.log.info("three vectors, result only, all green"
                    " -- and no way to say what that is worth")
