"""STEP 1 -- the register model, and the first generic test it buys: reset.

The model is one table: name / address / policy / reset value. Next to it sits
the mirror (RegfileModel) -- what the model believes the hardware holds. The
reset test is then a loop, not six hand-written checks: read every register
(and one unmapped address), compare against the table AND the mirror.

Plant the released reset mutant (`ctrl_reset_nonzero`) and the same loop
reports the mismatch by name:

    python3 demos/wk10-s1-ral/plant.py ctrl_reset_nonzero
    make -C demos/wk10-s1-ral STEP=1 \
        DUT=~/.vvtemp/wk10-mutants/ctrl_reset_nonzero/axil_regfile.sv
"""
import cocotb

from demo_common import banner, seed

# ---- the register model: one row per register, policy included ----
REGS = {
    "CTRL":    dict(addr=0x0, policy="RW",        reset=0x00000000),
    "STATUS":  dict(addr=0x1, policy="RO",        reset=0x5A5A0F0F),
    "SCRATCH": dict(addr=0x2, policy="RW",        reset=0x00000000),
    "INTR":    dict(addr=0x3, policy="W1C",       reset=0x00000000),
    "LOCK":    dict(addr=0x4, policy="RW",        reset=0x00000000),
    "SECURE":  dict(addr=0x5, policy="LOCKED_RW", reset=0x00000000),
}
A = {name: r["addr"] for name, r in REGS.items()}


@cocotb.test()
async def test_reset_values(dut):
    """Every register (and an unmapped address) reads its reset value."""
    bus, model = banner(dut)
    seed()
    await bus.reset()

    rows = ["", "  reset walk -- dut read vs. table vs. mirror:",
            "  reg      addr  policy      dut         mirror",
            "  -------  ----  ---------   ----------  ----------"]
    mismatches = []
    for name, r in REGS.items():
        got = await bus.read(r["addr"])
        mir = model.read(r["addr"])
        ok = got == r["reset"] == mir
        rows.append(f"  {name:<8} {r['addr']:#x}   {r['policy']:<9}   "
                    f"{got:#010x}  {mir:#010x}  {'ok' if ok else '<- MISMATCH'}")
        if not ok:
            mismatches.append(name)
    got = await bus.read(0x7)                      # unmapped: must read 0
    rows.append(f"  (unmap)  0x7   --          {got:#010x}  0x00000000  "
                f"{'ok' if got == 0 else '<- MISMATCH'}")
    if got != 0:
        mismatches.append("unmapped")
    rows.append(f"  {len(REGS) + 1} reads, {len(mismatches)} mismatch(es)")
    cocotb.log.info("\n".join(rows))
    assert not mismatches, \
        f"reset values wrong for: {', '.join(mismatches)}"
