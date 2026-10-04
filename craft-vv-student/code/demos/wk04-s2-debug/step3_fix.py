"""STEP 3 -- the fix, verified: one line back, then both runs green.

The waveform showed do_wr high while full was high; the RTL line is the
write gate. This step restores `& ~full` in $BUGDIR/fifo.sv (or leaves your
hand-edit alone if you fixed it in the editor already), confirms the file is
byte-identical to dut/fifo.sv, then reruns step 2 (the minimal sequence) and
step 1 (the full layered regression). A fix is not the absence of the
symptom -- it is the isolation case passing AND the regression that caught
it passing.

Not a cocotb module -- the Makefile dispatches it as a plain script.
"""
import filecmp
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CODE = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(CODE, "lib"))
from craft_mutate.mutate import parse_junit  # noqa: E402
from craft_tmp import craft_tmp_dir  # noqa: E402

BUG_LINE = "assign do_wr = wr_en;"
FIX_LINE = "assign do_wr = wr_en & ~full;"


def run_step(step, sim, bugdir):
    """Run one cocotb step with live output. True only when its tests passed.
    `make` exits 0 even on a failing test, so the verdict comes from the
    results file -- the same rule the mutation harness applies."""
    results = os.path.join(bugdir, f"results_step{step}.xml")
    if os.path.exists(results):
        os.remove(results)
    env = dict(os.environ, COCOTB_RESULTS_FILE=results, STEP=str(step))
    rc = subprocess.call(
        ["make", "-s", "-C", HERE, f"STEP={step}", f"SIM={sim}",
         f"BUGDIR={bugdir}", f"DUT={bugdir}/fifo.sv",
         f"COCOTB_RESULTS_FILE={results}"], env=env)
    if rc != 0 or not os.path.exists(results):
        return False
    tests, bad = parse_junit(results)
    return tests > 0 and not bad


def main():
    bugdir = os.environ.get("BUGDIR") or str(craft_tmp_dir("wk04-s2-bug"))
    sim = os.environ.get("SIM", "icarus")
    bug_dut = os.path.join(bugdir, "fifo.sv")
    if not os.path.exists(bug_dut):
        print(f"no planted DUT at {bug_dut} -- run: make STEP=0")
        sys.exit(1)

    src = open(bug_dut).read()
    if BUG_LINE in src:
        open(bug_dut, "w").write(src.replace(BUG_LINE, FIX_LINE, 1))
        print("the fix is one line:")
        print(f"  -  {BUG_LINE}")
        print(f"  +  {FIX_LINE}")
    else:
        print("write gate already restored (fixed by hand in the editor?)")
        print("verifying anyway -- a fix you have not rerun is a guess.")

    same = filecmp.cmp(bug_dut, os.path.join(CODE, "dut", "fifo.sv"),
                       shallow=False)
    print(f"byte-identical to dut/fifo.sv: {'yes' if same else 'NO'}")

    print()
    print("[1/2] the minimal failing sequence (step 2), on the fixed DUT:")
    if not run_step(2, sim, bugdir):
        print("still failing -- the fix is wrong or incomplete")
        sys.exit(1)
    print()
    print("[2/2] the full layered regression (step 1), on the fixed DUT:")
    if not run_step(1, sim, bugdir):
        print("minimal case passes but the regression does not -- keep going")
        sys.exit(1)
    print()
    print("fix verified: isolation case green, regression green.")
    print("score it (from code/):")
    print("  STEP=1 PYTHONPATH=$PWD/lib python3 -m craft_mutate.mutate \\")
    print("      --tb demos/wk04-s2-debug --dut dut/fifo.sv \\")
    print("      --pool tb/fifo/mutants_released.yaml --sim icarus")


if __name__ == "__main__":
    main()
