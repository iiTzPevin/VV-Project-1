#!/usr/bin/env python3
"""Print what every `cover property` counted, from Verilator's coverage.dat.

The Makefile runs this after the sim for steps compiled with
--coverage-user. Verilator writes one line per cover point; each key packs
\\x01-separated key\\x02value fields -- we want o (the label), l (the source
line) and the trailing count. Steps without coverage produce no file, and
this script then says nothing.
"""
import re
import sys


def main():
    try:
        lines = open(sys.argv[1]).read().splitlines()
    except OSError:
        return
    rows = []
    for line in lines:
        m = re.match(r"C '(.*)' (\d+)$", line)
        if not m:
            continue
        fields = dict(f.split("\x02", 1)
                      for f in m.group(1).split("\x01") if "\x02" in f)
        rows.append((fields.get("o", "?"), fields.get("l", "?"),
                     int(m.group(2))))
    if not rows:
        return
    print("[covers] what each `cover property` counted this run:")
    for name, lineno, count in sorted(rows):
        flag = "   <- NEVER FIRED" if count == 0 else ""
        print(f"[covers]   {name:<18} line {lineno:>3}   count {count}{flag}")


if __name__ == "__main__":
    main()
