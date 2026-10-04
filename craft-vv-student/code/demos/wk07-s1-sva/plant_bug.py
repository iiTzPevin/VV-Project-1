#!/usr/bin/env python3
"""Plant one released mutant into a scratch copy of dut/fifo.sv and print the
path. The Makefile calls this for steps 1 and 2, so the demo runs a broken
DUT without ever touching the repo's RTL.

    python3 plant_bug.py ignore_full
        -> ~/.vvtemp/craft-wk07-s1/fifo_ignore_full.sv

The find/replace pair comes from tb/fifo_sva/mutants_released.yaml -- the
same pool the harness scores against, applied the same way (the find string
must occur exactly once). Idempotent: the file is rewritten only when its
content would change, so make does not rebuild the model on every run.
"""
import os
import sys

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "lib"))
from craft_tmp import craft_tmp_dir  # noqa: E402

POOL = os.path.join(HERE, "..", "..", "tb", "fifo_sva", "mutants_released.yaml")
DUT = os.path.join(HERE, "..", "..", "dut", "fifo.sv")


def main():
    mid = sys.argv[1] if len(sys.argv) > 1 else "ignore_full"
    pool = yaml.safe_load(open(POOL))
    mut = next(m for m in pool["mutants"] if m["id"] == mid)
    src = open(DUT).read()
    if src.count(mut["find"]) != 1:
        sys.exit(f"plant_bug: find-string for {mid} not unique in fifo.sv")
    text = src.replace(mut["find"], mut["replace"], 1)
    out = os.path.join(str(craft_tmp_dir("craft-wk07-s1")), f"fifo_{mid}.sv")
    if not (os.path.exists(out) and open(out).read() == text):
        with open(out, "w") as f:
            f.write(text)
    print(out)


if __name__ == "__main__":
    main()
