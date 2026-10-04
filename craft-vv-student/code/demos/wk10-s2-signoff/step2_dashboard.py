"""STEP 2 -- the signoff dashboard: every number measured, none asserted.

Assembles the one-pager a signoff review reads for the go/no-go, and measures
each row live rather than quoting it:

  lint            verilator --lint-only -Wall on the DUT (verible stand-in)
  line coverage   the reference suite under verilator --coverage-line
  found/total     reference suite AND the student starter vs the released pool
  security        did the suite find the policy mutant (secure_writable_locked)?
  checks          assert statements / tests in the reference suite (via ast)

Rows print as they finish; the found/total rows take the longest (the harness
recompiles the DUT once per mutant). Full run measured at about 2 minutes --
talk over it; a dashboard is a batch product.
"""
import ast
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
CODE = os.path.abspath(os.path.join(HERE, "..", ".."))
DUT = os.path.join(CODE, "dut", "axil_regfile.sv")
REF_TB = os.path.join(CODE, "solutions", "axil_ral")
STUB_TB = os.path.join(CODE, "tb", "axil_ral")
POOL = os.path.join(CODE, "tb", "axil_ral", "mutants_released.yaml")

ENV = dict(os.environ,
           PYTHONPATH=os.path.join(CODE, "lib") + ":" + os.environ.get("PYTHONPATH", ""))


def run(cmd, cwd=None):
    return subprocess.run(cmd, cwd=cwd, env=ENV, text=True,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT)


def row(gate, measured, verdict):
    print(f"  {gate:<16} {measured:<47} {verdict}")


def gate_lint():
    p = run(["verilator", "--lint-only", "-Wall", DUT])
    n = len(re.findall(r"%Warning-[A-Z0-9]+:", p.stdout))
    row("lint", f"{n} findings (verilator --lint-only -Wall)",
        "PASS" if n == 0 and p.returncode == 0 else "FAIL")
    print("  " + " " * 17 + "(course tool is verible-verilog-lint; same gate)")
    return n == 0


def gate_coverage():
    """Reference suite under verilator --coverage-line, in a scratch copy."""
    scratch = tempfile.mkdtemp(prefix="wk10cov_")
    for f in ("Makefile", "test_axil_ral.py"):
        shutil.copy(os.path.join(REF_TB, f), scratch)
    p = run(["make", "-s", f"DUT={DUT}", "SIM=verilator",
             "EXTRA_ARGS=--coverage-line"], cwd=scratch)
    if "FAIL=0" not in p.stdout:
        row("line coverage", "reference suite did not pass -- no number", "FAIL")
        return False
    ann = os.path.join(scratch, "ann")
    p = run(["verilator_coverage", "--annotate-min", "1", "--annotate", ann,
             os.path.join(scratch, "coverage.dat")])
    m = re.search(r"Total coverage \((\d+)/(\d+)\) (\d+\.\d+)%", p.stdout)
    hit, total, pct = int(m.group(1)), int(m.group(2)), float(m.group(3))
    holes = [" ".join(ln.split(None, 1)[1].split())
             for ln in open(os.path.join(ann, "axil_regfile.sv"))
             if ln.startswith("%000000")]
    row("line coverage", f"{pct:.0f}% -- {hit}/{total} lines hit (reference suite)",
        "PASS" if hit == total else "PASS*")
    for h in holes:
        print("  " + " " * 17 + f"*uncovered: {h}")
    shutil.rmtree(scratch, ignore_errors=True)
    return True


def score(tb):
    out = tempfile.mktemp(suffix=".json")
    run([sys.executable, "-m", "craft_mutate.mutate", "--tb", tb,
         "--pool", POOL, "--sim", "icarus", "--timeout", "120",
         "--json", out], cwd=CODE)
    r = json.load(open(out))
    os.unlink(out)
    return r


def gate_mutation():
    ref = score(REF_TB)
    row("mutation score", f"reference {ref['found']}/{ref['total']} "
        f"({ref['percent']:.0f}%) on the released pool",
        "PASS" if ref["pass"] else "FAIL")
    stub = score(STUB_TB)
    row("", f"starter tb {stub['found']}/{stub['total']} "
        f"({stub['percent']:.1f}%) -- the gap is the week", "")
    sec = next(m for m in ref["mutants"] if m["id"] == "secure_writable_locked")
    row("security", "policy mutant secure_writable_locked "
        + ("FOUND" if sec["found"] else "SURVIVED"),
        "PASS" if sec["found"] else "FAIL")
    return ref["pass"] and sec["found"]


def gate_checks():
    tree = ast.parse(open(os.path.join(REF_TB, "test_axil_ral.py")).read())
    asserts = sum(isinstance(n, ast.Assert) for n in ast.walk(tree))
    tests = sum(isinstance(n, ast.AsyncFunctionDef) and any(
        isinstance(d, ast.Call) for d in n.decorator_list)
        for n in ast.walk(tree))
    row("checks", f"{asserts} assert statements across {tests} tests (ref suite)",
        "--")
    return True


def main():
    print("=" * 74)
    print("  axil_regfile -- signoff one-pager (every row measured by this run)")
    print("=" * 74)
    print(f"  {'gate':<16} {'measured':<47} verdict")
    print(f"  {'-' * 16} {'-' * 47} -------")
    ok = gate_lint()
    ok &= gate_coverage()
    ok &= gate_mutation()
    gate_checks()
    print("  " + "-" * 72)
    print(f"  signoff: {'GO' if ok else 'NO-GO'} -- "
          "no single number decides; the dashboard does")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
