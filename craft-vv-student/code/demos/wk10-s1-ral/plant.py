"""Plant one released-pool mutant into a copy of the DUT under the scratch dir.

Exactly what the mutation harness does per mutant, exposed as one command so
the room can watch a single planted bug get caught:

    python3 demos/wk10-s1-ral/plant.py ctrl_reset_nonzero
    make -C demos/wk10-s1-ral STEP=1 \
        DUT=~/.vvtemp/wk10-mutants/ctrl_reset_nonzero/axil_regfile.sv

Run with no argument to list the released pool.
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


def main():
    pool = yaml.safe_load(open(POOL))
    dut_src = os.path.join(CODE, "dut", pool["dut"])
    mutants = {m["id"]: m for m in pool["mutants"]}

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
    print(f"run any step against it with:  make STEP=N DUT={out}")


if __name__ == "__main__":
    main()
