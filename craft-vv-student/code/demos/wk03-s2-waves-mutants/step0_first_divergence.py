"""STEP 0 -- point the suite at a planted bug and find WHERE it diverges.

Plant one released mutant into a copy of the RTL (`make plant MUTANT=add2sub`
writes ~/.vvtemp/alu_add2sub.sv), then run this step against it with a wave dump:

    make STEP=0 DUT=~/.vvtemp/alu_add2sub.sv SIM=verilator VERILATOR_TRACE=1

Unlike an assert-and-stop test, this one keeps going after a mismatch: it
logs every divergence with its simulation time, then fails once at the end.
That buys you a complete trace. Each vector holds the bus for 2 ns and the
sample lands mid-column, so the wave cursor at a logged time shows the
divergent vector itself, cause beside effect. On the clean RTL it passes and
says so.
"""
import cocotb
from cocotb.triggers import Timer
from cocotb.utils import get_sim_time

from models.alu_model import alu_model
from demo_common import VECTORS, WIDTH, drive, label, seed

CHECKS = ("result", "zero", "carry", "overflow")


def fmt(name, val):
    return f"{val:#04x}" if name == "result" else str(val)


@cocotb.test()
async def test_first_divergence(dut):
    seed()
    diverged = []
    for a, b, op in VECTORS:
        drive(dut, a, b, op)
        await Timer(1, units="ns")     # settle; the sample sits mid-column
        exp = alu_model(a, b, op, WIDTH)
        diffs = []
        for name in CHECKS:
            got, want = int(getattr(dut, name).value), getattr(exp, name)
            if got != want:
                diffs.append(f"{name} dut {fmt(name, got)} != model {fmt(name, want)}")
        if diffs:
            t = get_sim_time(units="ns")
            diverged.append(t)
            cocotb.log.info(f"DIVERGE t={t:.0f}ns  {label(a, b, op):<22} " +
                            " | ".join(diffs))
        await Timer(1, units="ns")     # hold, so the column outlives the sample
    if diverged:
        cocotb.log.info(f"first divergence at t={diverged[0]:.0f}ns -- "
                        f"{len(diverged)}/{len(VECTORS)} vectors diverge; "
                        f"put the wave cursor there")
    else:
        cocotb.log.info(f"clean: DUT and model agree on all {len(VECTORS)} vectors")
    assert not diverged, \
        f"{len(diverged)} divergences; read the wave at t={diverged[0]:.0f}ns"
