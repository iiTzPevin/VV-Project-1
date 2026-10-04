#!/usr/bin/env python3
"""Read an arbiter counterexample trace and print the trigger.

    python3 show_trigger.py [path/to/trace.vcd]
        default: step1_trojan/engine_0/trace.vcd

Walks the VCD SymbiYosys wrote, prints rst_n / req / grant at every clock
edge the solver drove, and names the violating cycle: the grant bit with no
matching request. Exits non-zero if no violation is in the trace, or if the
trigger is not the documented magic pattern (req == 4'b1010) -- so the demo
self-checks the claim it makes on the slide.

This is the point of the step: a formal FAIL is not a shrug, it is the
EXACT input that reaches the bad state. Nobody wrote this stimulus; the
solver derived it from the property.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MAGIC_REQ, MAGIC_GRANT, N = 0b1010, 0b0100, 4


def parse_vcd(path):
    """Tiny VCD reader: top-scope rst_n/req/grant sampled at each #time."""
    want = {"rst_n", "req", "grant", "clk"}
    ids = {}                      # id char -> signal name
    vals = {}                     # id char -> bitstring
    rows = []                     # (time, {name: int_or_None})
    depth = 0

    def snap(t):
        out = {}
        for i, name in ids.items():
            v = vals.get(i, "x")
            out[name] = int(v, 2) if set(v) <= set("01") else None
        rows.append((t, out))

    t = None
    with open(path) as f:
        for line in f:
            tok = line.split()
            if not tok:
                continue
            if tok[0] == "$scope":
                depth += 1
            elif tok[0] == "$upscope":
                depth -= 1
            elif tok[0] == "$var" and depth == 1 and tok[4] in want:
                ids[tok[3]] = tok[4]
            elif line.startswith("#"):
                if t is not None:
                    snap(t)
                t = int(line[1:])
            elif tok[0][0] in "01xz" and tok[0][1:] in ids:
                vals[tok[0][1:]] = tok[0][0]
            elif tok[0][0] == "b" and len(tok) > 1 and tok[1] in ids:
                vals[tok[1]] = tok[0][1:]
    if t is not None:
        snap(t)
    return rows


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        HERE, "step1_trojan", "engine_0", "trace.vcd")
    if not os.path.exists(path):
        sys.exit(f"show_trigger: no trace at {path} -- run `make STEP=1` first")
    rows = [(t, s) for t, s in parse_vcd(path) if s.get("clk") == 1]

    print(f"counterexample: {os.path.relpath(path, HERE)}")
    print("  edge  rst_n   req    grant   grant&~req")
    violation = None
    for k, (t, s) in enumerate(rows):
        if None in (s.get("rst_n"), s.get("req"), s.get("grant")):
            continue
        bad = s["grant"] & ~s["req"] & ((1 << N) - 1)
        note = ""
        if s["rst_n"] and bad:
            lines = [i for i in range(N) if bad >> i & 1]
            note = f"  <- VIOLATION: line {lines[0]} granted, never requested"
            if violation is None:
                violation = (s["req"], s["grant"])
        print(f"  {k:>4}    {s['rst_n']}    {s['req']:04b}    "
              f"{s['grant']:04b}    {bad:04b}{note}")

    if violation is None:
        sys.exit("show_trigger: trace holds no violation -- wrong trace?")
    req, grant = violation
    print(f"\n  trigger: req = 4'b{req:04b}  ->  grant = 4'b{grant:04b}")
    if (req, grant) != (MAGIC_REQ, MAGIC_GRANT):
        sys.exit("show_trigger: trigger differs from the documented magic "
                 f"pattern (expected req=4'b{MAGIC_REQ:04b} -> "
                 f"grant=4'b{MAGIC_GRANT:04b})")
    print("  matches the backdoor in dut/arbiter_trojan.sv: the solver "
          "recovered the magic pattern nobody told it about.")


if __name__ == "__main__":
    main()
