#!/usr/bin/env python3
"""STEP 2 -- score both ends of the week against the released pool.

Runs the mutation harness twice, exactly as HW9 will:

    tb/axil_uvm   the starter you build on: working plumbing, STUB scoreboard

The starter is green on clean RTL and catches 1 of 8 -- the one mutant its
placeholder rvalid check can see. Every register-policy bug survives. The
reference environment, same agent structure but with a RegfileModel-backed
scoreboard, catches 8 of 8. The gap between those two numbers is the homework.

The reference environment is not in your packet, so this prints its recorded
score rather than re-running it.

Run via `make STEP=2` (uses $SIM, default icarus), or directly:
    python3 step2_score.py
"""
import os
import re
import subprocess
import sys
from pathlib import Path

CODE = Path(__file__).resolve().parents[2]        # .../code
POOL = "tb/axil_uvm/mutants_released.yaml"
SIM = os.environ.get("SIM", "icarus")
REFERENCE = "solutions/axil_uvm"                  # present only in the master repo
REFERENCE_RECORDED = "found/total = 8/8"          # what it scores on this pool


def score(tb):
    print(f"--- {tb}  vs  {POOL}  (sim: {SIM}) ---", flush=True)
    env = dict(os.environ)
    env["PYTHONPATH"] = f"{CODE / 'lib'}:{env.get('PYTHONPATH', '')}"
    proc = subprocess.run(
        [sys.executable, "-m", "craft_mutate.mutate",
         "--tb", str(CODE / tb), "--dut", str(CODE / "dut/axil_regfile.sv"),
         "--pool", str(CODE / POOL), "--sim", SIM],
        cwd=CODE, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True)
    sys.stdout.write(proc.stdout)
    m = re.search(r"found/total = (\d+)/(\d+)", proc.stdout)
    return m.group(0) if m else "found/total = ?/?"


def main():
    stub = score("tb/axil_uvm")
    print()
    if (CODE / REFERENCE).is_dir():
        ref, how = score(REFERENCE), "measured"
        print()
    else:
        ref, how = REFERENCE_RECORDED, "recorded"
        print(f"--- reference environment (model scoreboard) -- {how} ---")
        print("    Not in your packet. Its score on this pool is shown below.\n")
    print("  environment                     score")
    print(f"  starter    (stub scoreboard)   {stub}")
    print(f"  reference  (model scoreboard)  {ref}   ({how})")


if __name__ == "__main__":
    main()
