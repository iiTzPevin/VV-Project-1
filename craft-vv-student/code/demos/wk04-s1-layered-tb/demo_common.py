"""Shared helpers for the Week 4 Session 1 demo. The layers themselves are NOT
in here -- building them live is the session, so they live in the step files.
What is shared: the seed, the stimulus, and the corner-case report that proves
steps 0 and 3 drove the same vectors.
"""
import hashlib
import os
import random

import cocotb

from models.fifo_model import FifoModel

WIDTH, DEPTH = 8, 8


def seed(default=5):
    """Pin the stream so every step logs the same numbers we rehearsed.
    Override from the shell:  make STEP=3 DEMO_SEED=7
    (This week's stimulus is directed, so the seed only matters if you add
    random traffic -- but pin it anyway; Week 5 inherits the habit.)
    """
    s = int(os.environ.get("DEMO_SEED", default))
    random.seed(s)
    cocotb.log.info(f"demo seed = {s}")
    return s


# The whole demo drives THESE vectors and nothing else, in every step.
# (wr_en, rd_en, wr_data) per cycle. Step 0 carries the same list written out
# by hand inside the test function -- the digest in the report is the proof
# that the two never drift apart.
SEQUENCES = [
    ("first in, first out", [
        (1, 0, 0xA0), (1, 0, 0xA1), (1, 0, 0xA2), (0, 1, 0x00),
        (1, 1, 0xA3), (0, 1, 0x00), (0, 1, 0x00),
    ]),
    ("fill to full, knock twice", [
        (1, 0, 0xB0), (1, 0, 0xB1), (1, 0, 0xB2), (1, 0, 0xB3),
        (1, 0, 0xB4), (1, 0, 0xB5), (1, 0, 0xB6), (1, 0, 0xB7),
        (1, 0, 0xE0), (1, 0, 0xE1),
    ]),
    ("drain to empty, knock twice", [
        (0, 1, 0x00), (0, 1, 0x00), (0, 1, 0x00), (0, 1, 0x00),
        (0, 1, 0x00), (0, 1, 0x00), (0, 1, 0x00), (0, 1, 0x00),
        (0, 1, 0x00), (0, 1, 0x00),
    ]),
    ("both boundaries, simultaneous", [
        (1, 1, 0xC0),
        (1, 0, 0xC1), (1, 0, 0xC2), (1, 0, 0xC3), (1, 0, 0xC4),
        (1, 0, 0xC5), (1, 0, 0xC6), (1, 0, 0xC7),
        (1, 1, 0xE2),
        (0, 1, 0x00), (0, 1, 0x00), (0, 1, 0x00),
    ]),
    ("mixed traffic across the wrap", [
        (1, 1, 0xD0), (1, 1, 0xD1), (0, 1, 0x00), (1, 0, 0xD2),
        (0, 1, 0x00), (0, 1, 0x00), (0, 1, 0x00), (0, 1, 0x00),
    ]),
]

SCENARIO = [v for _name, _seq in SEQUENCES for v in _seq]


def digest(applied):
    """Eight hex characters over the vectors as driven, not as declared."""
    return hashlib.md5(repr(list(applied)).encode()).hexdigest()[:8]


def corner_report(applied):
    """The HW4 corner-case checklist, measured from the driven vectors.
    Identical stimulus gives an identical table -- diff step0 against step3.
    """
    m = FifoModel(WIDTH, DEPTH)
    full_c = empty_c = writes = 0
    wr_full = wr_full_sim = rd_empty = rd_empty_sim = simul_mid = 0
    for wr, rd, data in applied:
        if wr and m.full:
            wr_full += 1
            wr_full_sim += int(bool(rd))
        if rd and m.empty:
            rd_empty += 1
            rd_empty_sim += int(bool(wr))
        if wr and rd and not m.full and not m.empty:
            simul_mid += 1
        do_wr, _do_rd = m.step(wr, data, rd)
        writes += int(do_wr)
        full_c += int(m.full)
        empty_c += int(m.empty)

    def mark(n):
        return "[x]" if n else "[ ]"

    lines = [
        "",
        "  corner-case checklist -- measured from what was driven",
        f"  {mark(full_c)} full reached              "
        f"{full_c} cycles at count=={DEPTH}",
        f"  {mark(wr_full)} write-while-full refused  "
        f"{wr_full} attempts ({wr_full_sim} simultaneous)",
        f"  {mark(empty_c)} empty re-reached          "
        f"{empty_c} cycles at count==0",
        f"  {mark(rd_empty)} read-while-empty ignored  "
        f"{rd_empty} attempts ({rd_empty_sim} simultaneous)",
        f"  {mark(simul_mid)} simultaneous read+write   "
        f"{simul_mid} mid-stream, count unchanged",
        f"  {mark(writes > DEPTH)} pointer wrap              "
        f"{writes} accepted writes, depth {DEPTH} ({writes // DEPTH} wraps)",
        f"  stimulus: {len(applied)} cycles, digest {digest(applied)}"
        "   (same digest = same vectors)",
    ]
    return "\n".join(lines)


def report(applied):
    cocotb.log.info(corner_report(applied))
