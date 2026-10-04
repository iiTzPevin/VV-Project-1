"""Plant one mutant into a copy of the DUT under the scratch dir.

Same move the mutation harness makes per pool entry, exposed as one command.
Besides the released pool this demo adds one local, lint-only defect
(`lint_latch`: the read-mux default arm dropped) -- it is not a pool mutant
because lint, not simulation, is the tool that catches it.

    python3 demos/wk10-s2-signoff/plant.py lint_latch
    make -C demos/wk10-s2-signoff STEP=0 \
        DUT=~/.vvtemp/wk10-mutants/lint_latch/axil_regfile.sv

Run with no argument to list everything plantable.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CODE = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(CODE, "lib"))

import yaml                                    # noqa: E402
from craft_mutate.mutate import apply_mutant   # noqa: E402

POOL = os.path.join(CODE, "tb", "axil_ral", "mutants_released.yaml")
from craft_tmp import craft_tmp_root       # noqa: E402

OUTDIR = str(craft_tmp_root() / "wk10-mutants")

LOCAL = {
    "lint_latch": dict(
        id="lint_latch",
        desc="LINT DEMO: read-mux default arm dropped -> inferred latch",
        find="default:      rd_mux = 32'h0000_0000;   // unmapped reads 0",
        replace="default:      ;  // planted lint defect: rd_mux unassigned here"),
}


def main():
    pool = yaml.safe_load(open(POOL))
    dut_src = os.path.join(CODE, "dut", pool["dut"])
    mutants = {m["id"]: m for m in pool["mutants"]}
    mutants.update(LOCAL)

    if len(sys.argv) != 2 or sys.argv[1] not in mutants:
        print(f"usage: python3 plant.py <mutant_id>   (pool: {POOL})")
        for mid, m in mutants.items():
            print(f"  {mid:<22} {m['desc']}")
        sys.exit(0 if len(sys.argv) == 1 else 1)

    mid = sys.argv[1]
    mutated = apply_mutant(open(dut_src).read(), mutants[mid])
    os.makedirs(os.path.join(OUTDIR, mid), exist_ok=True)
    out = os.path.join(OUTDIR, mid, "axil_regfile.sv")
    open(out, "w").write(mutated)
    print(f"planted {mid}: {mutants[mid]['desc']}")
    print(f"  - {mutants[mid]['find'].strip()}")
    print(f"  + {mutants[mid]['replace'].strip()}")
    print(f"run a step against it with:  make STEP=N DUT={out}")


if __name__ == "__main__":
    main()
