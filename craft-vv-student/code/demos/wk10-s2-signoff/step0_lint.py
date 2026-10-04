"""STEP 0 -- lint the register file: a signoff gate that needs no stimulus.

Lint reads the RTL statically -- no clock, no testbench -- and catches defect
classes no test targets: inferred latches, incomplete sensitivity lists,
width mismatches. The course plan runs verible; this machine substitutes
verilator --lint-only (same gate, different tool -- both command lines are
printed so the room sees what to type on a machine that has verible).

Clean DUT first, then plant the latch defect and re-run:

    python3 demos/wk10-s2-signoff/plant.py lint_latch
    make -C demos/wk10-s2-signoff STEP=0 \
        DUT=~/.vvtemp/wk10-mutants/lint_latch/axil_regfile.sv
"""
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DUT = os.path.abspath(os.path.join(HERE, "..", "..", "dut", "axil_regfile.sv"))


def main():
    dut = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_DUT
    print(f"lint target: {dut}")
    print("  with verible (the course tool):  "
          f"verible-verilog-lint {os.path.basename(dut)}")
    print("  stand-in on this machine:        "
          f"verilator --lint-only -Wall {os.path.basename(dut)}")
    print()

    proc = subprocess.run(["verilator", "--lint-only", "-Wall", dut],
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                          text=True)
    findings = re.findall(r"%Warning-([A-Z0-9]+):", proc.stdout)
    for line in proc.stdout.splitlines():
        print(f"  {line}")

    if not findings and proc.returncode == 0:
        print("lint: CLEAN -- 0 findings.  gate: PASS")
        sys.exit(0)
    kinds = ", ".join(sorted(set(findings))) if findings else "see errors above"
    print(f"lint: {max(len(findings), 1)} finding(s) [{kinds}].  gate: FAIL")
    if "LATCH" in findings:
        print("a latch nobody intended, found in under a second, with no testbench")
    sys.exit(1)


if __name__ == "__main__":
    main()
