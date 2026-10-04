#!/usr/bin/env python3
"""CRAFT mutation harness -- score a testbench as found / total.

A mutant is a small, exact source transformation of a DUT. We run the
testbench against each mutated DUT; the mutant is *found* when the testbench
fails on it (a failing test, a crash, or a hang). We report found / total.
We say "found", never "killed".

Usage:
    python -m craft_mutate.mutate --tb TBDIR --dut DUT.sv --pool POOL.yaml
        [--sim verilator|icarus] [--timeout 120] [--threshold 90]
        [--json OUT.json] [--gate]

--gate makes the process exit non-zero if found/total < threshold
(used by CI to fail a submission that misses too many mutants).
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

import yaml


def parse_junit(path):
    """Return (n_tests, n_bad) where n_bad counts failures + errors."""
    tree = ET.parse(path)
    root = tree.getroot()
    tests = 0
    bad = 0
    for tc in root.iter("testcase"):
        tests += 1
        for child in tc:
            if child.tag in ("failure", "error"):
                bad += 1
                break
    # also honor suite-level attributes if present
    for ts in root.iter("testsuite"):
        try:
            bad = max(bad, int(ts.get("failures", 0)) + int(ts.get("errors", 0)))
        except (TypeError, ValueError):
            pass
    return tests, bad


def run_tb(tbdir, dut_path, sim, timeout):
    """Run the testbench once against dut_path. Return dict with outcome."""
    workbuild = tempfile.mkdtemp(prefix="simbuild_")
    results = os.path.join(workbuild, "results.xml")
    env = dict(os.environ, COCOTB_RESULTS_FILE=results)
    cmd = ["make", "-s", "-C", tbdir, f"SIM={sim}", f"DUT={dut_path}",
           f"SIM_BUILD={workbuild}", f"COCOTB_RESULTS_FILE={results}"]
    timed_out = False
    try:
        proc = subprocess.run(cmd, env=env, timeout=timeout,
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        rc = proc.returncode
        out = proc.stdout.decode(errors="replace")
    except subprocess.TimeoutExpired:
        timed_out = True
        rc = -1
        out = "TIMEOUT"
    # ONLY read this run's unique results file -- never fall back to a stale
    # results.xml in the tb dir (a mutant caught via an SVA $stop writes no
    # file; falling back would misscore it as SURVIVED).
    tests = bad = None
    if not timed_out and os.path.exists(results):
        try:
            tests, bad = parse_junit(results)
        except ET.ParseError:
            tests, bad = None, None
    shutil.rmtree(workbuild, ignore_errors=True)
    return {"rc": rc, "timed_out": timed_out, "tests": tests, "bad": bad, "out": out}


def outcome_is_failure(res):
    """A run 'fails' (would find a mutant) if it timed out, crashed, or a test failed."""
    if res["timed_out"]:
        return True, "hang/timeout"
    if res["tests"] is None:
        # no parseable results -> the mutant broke the build or crashed the sim
        return (res["rc"] != 0), "build/crash"
    if res["bad"] and res["bad"] > 0:
        return True, "test-failed"
    return False, "passed"


def apply_mutant(src_text, mut):
    find = mut["find"]
    n = src_text.count(find)
    if n == 0:
        raise ValueError(f"mutant {mut['id']}: find-string not present in DUT")
    if n > 1:
        raise ValueError(f"mutant {mut['id']}: find-string occurs {n}x (must be unique)")
    return src_text.replace(find, mut["replace"], 1)


def main():
    ap = argparse.ArgumentParser(description="CRAFT found/total mutation harness")
    ap.add_argument("--tb", required=True, help="testbench dir (has Makefile + test)")
    ap.add_argument("--dut", default=None,
                    help="DUT source to mutate (default: <tb>/../../dut/<pool 'dut'>)")
    ap.add_argument("--dut-dir", default=None,
                    help="directory holding DUT sources (default: <tb>/../../dut)")
    ap.add_argument("--pool", required=True, help="mutant pool YAML")
    ap.add_argument("--sim", default="verilator")
    ap.add_argument("--timeout", type=int, default=120)
    ap.add_argument("--threshold", type=float, default=90.0)
    ap.add_argument("--json", default=None)
    ap.add_argument("--gate", action="store_true")
    args = ap.parse_args()

    tbdir = os.path.abspath(args.tb)
    pool = yaml.safe_load(open(args.pool))
    if args.dut:
        dut = os.path.abspath(args.dut)
    else:
        dut_dir = args.dut_dir or os.path.join(tbdir, "..", "..", "dut")
        dut = os.path.abspath(os.path.join(dut_dir, pool["dut"]))
    mutants = pool["mutants"]
    src = open(dut).read()
    dut_name = os.path.basename(dut)

    # --- baseline: clean DUT must pass ---
    print(f"[baseline] running clean {dut_name} through {os.path.basename(tbdir)} ...")
    base = run_tb(tbdir, dut, args.sim, args.timeout)
    base_fail, base_why = outcome_is_failure(base)
    if base_fail or (base["tests"] or 0) == 0:
        print(f"  ERROR: testbench does not pass on clean RTL ({base_why}). "
              f"Fix the testbench before scoring.")
        print(base["out"][-1500:])
        sys.exit(2)
    print(f"  clean RTL: {base['tests']} tests passed.\n")

    found = 0
    rows = []
    with tempfile.TemporaryDirectory(prefix="mut_") as td:
        for mut in mutants:
            mut_src = apply_mutant(src, mut)
            mpath = os.path.join(td, dut_name)
            open(mpath, "w").write(mut_src)
            res = run_tb(tbdir, mpath, args.sim, args.timeout)
            is_fail, why = outcome_is_failure(res)
            found += int(is_fail)
            mark = "found  " if is_fail else "SURVIVED"
            rows.append({"id": mut["id"], "found": is_fail, "why": why,
                         "desc": mut.get("desc", "")})
            print(f"  [{mark}] {mut['id']:<20} ({why})  -- {mut.get('desc','')}")

    total = len(mutants)
    pct = 100.0 * found / total if total else 0.0
    print(f"\n==== found/total = {found}/{total}  =  {pct:.1f}%  "
          f"(threshold {args.threshold:.0f}%) ====")
    survivors = [r["id"] for r in rows if not r["found"]]
    if survivors:
        print("surviving mutants:", ", ".join(survivors))

    if args.json:
        json.dump({"found": found, "total": total, "percent": pct,
                   "threshold": args.threshold, "pass": pct >= args.threshold,
                   "mutants": rows}, open(args.json, "w"), indent=2)

    if args.gate and pct < args.threshold:
        print(f"GATE FAIL: {pct:.1f}% < {args.threshold:.0f}%")
        sys.exit(1)


if __name__ == "__main__":
    main()
