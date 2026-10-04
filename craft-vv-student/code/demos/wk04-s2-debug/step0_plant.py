"""STEP 0 -- plant the bug: released mutant `ignore_full` on a scratch copy.

Copies dut/fifo.sv to $BUGDIR/fifo.sv (default ~/.vvtemp/wk04-s2-bug) and applies
the `ignore_full` entry from tb/fifo/mutants_released.yaml -- the write-gate
loses its `& ~full`. Then it runs the Week-3-style smoke against the planted
DUT: green. The overflow bug is in the building and last week's test cannot
see it. Every later step runs against $BUGDIR/fifo.sv until step 3 fixes it.

Not a cocotb module -- the Makefile dispatches it as a plain script.
For the We Do, plant a different released mutant into a second scratch dir:
    make STEP=0 DEMO_MUTANT=full_offbyone BUGDIR=~/.vvtemp/wk04-wedo
"""
import os
import shutil
import subprocess
import sys

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
CODE = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(CODE, "lib"))
from craft_mutate.mutate import apply_mutant, parse_junit  # noqa: E402
from craft_tmp import craft_tmp_dir  # noqa: E402

MUTANT_ID = os.environ.get("DEMO_MUTANT") or "ignore_full"


def main():
    bugdir = os.environ.get("BUGDIR") or str(craft_tmp_dir("wk04-s2-bug"))
    sim = os.environ.get("SIM", "icarus")
    dut_src = os.path.join(CODE, "dut", "fifo.sv")
    pool_path = os.path.join(CODE, "tb", "fifo", "mutants_released.yaml")

    pool = yaml.safe_load(open(pool_path))
    mut = next(m for m in pool["mutants"] if m["id"] == MUTANT_ID)

    os.makedirs(bugdir, exist_ok=True)
    src = open(dut_src).read()
    open(os.path.join(bugdir, "fifo.sv"), "w").write(apply_mutant(src, mut))

    print(f"planted released mutant '{MUTANT_ID}' -- {mut['desc']}")
    print(f"  {os.path.relpath(dut_src, os.path.dirname(CODE))}")
    print(f"  -> {bugdir}/fifo.sv, one line changed:")
    print(f"  -  {mut['find'].strip()}")
    print(f"  +  {mut['replace'].strip()}")
    print()
    print(f"[smoke] the Week-3-style test against the planted DUT ({sim}):")
    results = os.path.join(bugdir, "results_smoke.xml")
    if os.path.exists(results):
        os.remove(results)
    env = dict(os.environ, COCOTB_RESULTS_FILE=results)
    rc = subprocess.call(
        ["make", "-s", "-C", HERE, "MODULE=smoke_week3",
         f"SIM={sim}", f"DUT={bugdir}/fifo.sv",
         f"COCOTB_RESULTS_FILE={results}"], env=env)
    if rc != 0 or not os.path.exists(results):
        print("smoke run failed to execute -- check the sim environment")
        sys.exit(rc or 1)
    tests, bad = parse_junit(results)
    if tests == 0 or bad:
        print("the smoke FAILED on this mutant -- with DEMO_MUTANT overridden")
        print("that can be legitimate (count_wr_dec is smoke-visible).")
        sys.exit(1)
    print()
    print("green. A FIFO that overwrites its oldest word on a full-queue write")
    print("walks straight past a three-write smoke. Next: make STEP=1")


if __name__ == "__main__":
    main()
