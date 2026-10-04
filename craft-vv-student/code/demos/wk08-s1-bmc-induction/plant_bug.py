#!/usr/bin/env python3
"""Plant one released mutant into a scratch copy of dut/fifo.sv and print the
path. Step 1 runs the SAME properties (formal/fifo/fifo_formal.sv) against
this broken copy; the repo's RTL is never touched.

    python3 plant_bug.py full_offbyone
        -> ~/.vvtemp/craft-wk08-s1/fifo_bug.sv

The find/replace pair comes from tb/fifo_crv/mutants_released.yaml -- the
same pool the simulation harness scores against, applied the same way (the
find string must occur exactly once). Pick a different mutant with
`make STEP=1 MUT=<id>`. Idempotent: files are rewritten only when their
content would change.

SymbiYosys does not expand variables inside a .sby, so this also writes
step1_planted_bmc.gen.sby -- the checked-in template with the scratch path
substituted into [files]. sby copies [files] into its work directory and the
[script] section reads them by basename, so only that one line has to move.
"""
import os
import sys

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "lib"))
from craft_tmp import craft_tmp_file  # noqa: E402

POOL = os.environ.get("POOL") or os.path.join(
    HERE, "..", "..", "tb", "fifo_crv", "mutants_released.yaml")
DUT = os.environ.get("DUT") or os.path.join(HERE, "..", "..", "dut", "fifo.sv")
OUT = str(craft_tmp_file("craft-wk08-s1", "fifo_bug.sv"))
TEMPLATE = os.path.join(HERE, "step1_planted_bmc.sby")
GENERATED = os.path.join(HERE, "step1_planted_bmc.gen.sby")


def write_sby():
    """Rewrite the template's planted-DUT line to wherever OUT actually is."""
    lines = open(TEMPLATE).read().splitlines(True)
    out = [ln for ln in lines
           if os.path.basename(ln.strip()) != "fifo_bug.sv" or not ln.strip()]
    if len(out) != len(lines) - 1:
        sys.exit("plant_bug: step1_planted_bmc.sby has no fifo_bug.sv line to replace")
    out.append(OUT + "\n")
    text = "".join(out)
    if not (os.path.exists(GENERATED) and open(GENERATED).read() == text):
        open(GENERATED, "w").write(text)


def plant(mid):
    pool = yaml.safe_load(open(POOL))
    try:
        mut = next(m for m in pool["mutants"] if m["id"] == mid)
    except StopIteration:
        ids = ", ".join(m["id"] for m in pool["mutants"])
        sys.exit(f"plant_bug: no mutant '{mid}' in pool ({ids})")
    src = open(DUT).read()
    if src.count(mut["find"]) != 1:
        sys.exit(f"plant_bug: find-string for {mid} not unique in {DUT}")
    text = src.replace(mut["find"], mut["replace"], 1)
    if not (os.path.exists(OUT) and open(OUT).read() == text):
        with open(OUT, "w") as f:
            f.write(text)
    write_sby()
    return OUT, mut


if __name__ == "__main__":
    mid = sys.argv[1] if len(sys.argv) > 1 else "full_offbyone"
    out, mut = plant(mid)
    print(f"planted {mid}: {mut['desc']}", file=sys.stderr)
    print(out)
