#!/usr/bin/env python3
"""found/total for the FIFO invariant set, formal edition.

The simulation harness (craft_mutate) scores a testbench by running it
against every released mutant. The formal analog: plant each mutant into
the scratch copy, run the SAME BMC the demo uses (step1_planted_bmc.sby), and
count a mutant as FOUND when the proof FAILS -- the properties produced a
counterexample. A mutant the properties cannot see PASSES its proof and
survives. Same vocabulary as Week 3: found, never "killed".

    python3 formal_score.py            # all 8 released mutants, ~1 min

The survivors are the lesson, not a defect: every property in
formal/fifo/fifo_formal.sv is about count/full/empty, so every data-path
mutant is invisible to it. A proof covers what you specified -- nothing else.
"""
import os
import re
import subprocess
import sys

import plant_bug
import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
SBY = os.path.join(HERE, "step1_planted_bmc.sby")


def run_one(mid):
    plant_bug.plant(mid)
    proc = subprocess.run(["sby", "-f", SBY], cwd=HERE,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out = proc.stdout.decode(errors="replace")
    m = re.search(r"DONE \((\w+)", out)
    verdict = m.group(1) if m else "ERROR"
    # step number of the failing assertion, when there is one
    step = re.search(r"failed assertion \S+ at \S+ step (\d+)", out)
    return verdict, (step.group(1) if step else "-")


def main():
    pool = yaml.safe_load(open(plant_bug.POOL))
    found = 0
    for mut in pool["mutants"]:
        verdict, step = run_one(mut["id"])
        # expect fail is set in the .sby: FAIL == counterexample == found
        is_found = verdict == "FAIL"
        found += int(is_found)
        mark = "found  " if is_found else "SURVIVED"
        cex = f"counterexample at step {step}" if is_found else "proof PASSES on the mutant"
        print(f"  [{mark}] {mut['id']:<20} ({cex})  -- {mut.get('desc','')}")
    total = len(pool["mutants"])
    print(f"\n==== found/total = {found}/{total}  =  {100.0*found/total:.1f}% ====")
    return 0


if __name__ == "__main__":
    sys.exit(main())
