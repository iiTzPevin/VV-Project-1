"""Shared helpers for the Week 6 demos. Keeps each step file short enough to
read on a projector -- the step files hold only what the demo is about.

Carried from Week 5: seed pinning, reset/apply, the histogram, and the
scoreboard. New this week: the coverage reporters -- a per-item summary line,
the cross as a grid with empty cells marked, and a convergence row.
"""
import os
import random

import cocotb
from cocotb.triggers import RisingEdge, FallingEdge, Timer
from cocotb_coverage.coverage import coverage_db

WIDTH, DEPTH = 8, 8
OCC_BINS = ["empty", "partial", "full"]
OP_BINS = ["idle", "write", "read", "simul"]


def seed(default=5):
    """Pin the stream so the room sees the same report we rehearsed.
    Override from the shell:  make STEP=1 DEMO_SEED=7
    """
    s = int(os.environ.get("DEMO_SEED", default))
    random.seed(s)
    cocotb.log.info(f"demo seed = {s}")
    return s


async def reset(dut):
    """Drive a clean reset and leave us parked on a falling edge."""
    dut.wr_en.value = 0
    dut.rd_en.value = 0
    dut.wr_data.value = 0
    dut.rst_n.value = 0
    for _ in range(3):
        await RisingEdge(dut.clk)
    dut.rst_n.value = 1
    await FallingEdge(dut.clk)


async def apply(dut, wr, rd, data):
    """Drive one transaction, advance one clock, settle. Returns nothing."""
    dut.wr_en.value = wr
    dut.rd_en.value = rd
    dut.wr_data.value = data
    await RisingEdge(dut.clk)
    await Timer(1, units="ns")


def histogram(counts, depth=DEPTH):
    """An occupancy histogram you can read from the back row."""
    bins = [0] * (depth + 1)
    for c in counts:
        bins[c] += 1
    peak = max(bins) or 1
    out = ["", "  occupancy   cycles", "  ---------   ------"]
    for i, n in enumerate(bins):
        bar = "#" * round(20 * n / peak)
        tag = " <- EMPTY" if i == 0 else (" <- FULL" if i == depth else "")
        out.append(f"  {i:>9}   {n:>6}  {bar}{tag}")
    reach = sum(1 for i in (0, depth) if bins[i] > 0)
    out.append(f"  boundaries reached: {reach}/2   "
               f"(empty={bins[0]} cycles, full={bins[depth]} cycles)")
    return "\n".join(out)


def report(dut, counts):
    cocotb.log.info(histogram(counts))


def check(dut, model):
    """The scoreboard from Week 5, carried forward unchanged. This week
    changes what we MEASURE, never what we check or drive.
    """
    assert int(dut.count.value) == model.count, \
        f"count {int(dut.count.value)} != model {model.count}"
    assert bool(dut.full.value) == model.full, \
        f"full {bool(dut.full.value)} != model {model.full}"
    assert bool(dut.empty.value) == model.empty, \
        f"empty {bool(dut.empty.value)} != model {model.empty}"
    if not model.empty:                       # FWFT: head valid only when !empty
        assert int(dut.rd_data.value) == model.head, \
            f"rd_data {int(dut.rd_data.value):#04x} != head {model.head:#04x}"


# ------------------------------------------------------- the coverage side ---

def occ_bin(count):
    """Occupancy, in the three states the Week 2 vplan names."""
    if count == 0:
        return "empty"
    if count == DEPTH:
        return "full"
    return "partial"


def op_bin(wr_en, rd_en):
    """The operation requested this cycle, as driven -- not as accepted."""
    if wr_en and rd_en:
        return "simul"
    if wr_en:
        return "write"
    if rd_en:
        return "read"
    return "idle"


def cov_pct(name):
    return coverage_db[name].cover_percentage


def cov_lines(*names):
    """One line per coverage item: bins hit and percentage. The headline view
    -- and the reason to keep reading past it.
    """
    out = [""]
    for name in names:
        det = coverage_db[name].detailed_coverage
        hit = sum(1 for v in det.values() if v > 0)
        out.append(f"  {name:<13} {hit:>2}/{len(det):<2} bins hit  "
                   f"{cov_pct(name):6.1f}%")
    return "\n".join(out)


def cov_grid(cross):
    """The cross as a grid: occupancy rows, operation columns, hits in the
    cells. '-' marks an empty bin. This is the picture the headline hides.
    """
    det = coverage_db[cross].detailed_coverage
    hits = {}
    for key, n in det.items():
        o, p = key if isinstance(key, tuple) else tuple(
            s.strip(" '()\"") for s in str(key).split(","))
        hits[(o, p)] = n
    out = ["", "  occ \\ op  " + "".join(f"{p:>8}" for p in OP_BINS)]
    for o in OCC_BINS:
        row = f"  {o:<9}"
        for p in OP_BINS:
            n = hits.get((o, p), 0)
            row += f"{n if n else '-':>8}"
        out.append(row)
    n_hit = sum(1 for v in hits.values() if v > 0)
    out.append(f"  cross {cross}: {n_hit}/{len(hits)} bins hit = "
               f"{cov_pct(cross):.1f}%   ('-' = empty bin)")
    empty = [f"({o},{p})" for o in OCC_BINS for p in OP_BINS
             if hits.get((o, p), 0) == 0]
    if empty:
        out.append(f"  empty bins ({len(empty)}): " + "  ".join(empty))
    return "\n".join(out)


def trace_row(rows):
    """The convergence table: cross coverage sampled as the run advances.
    Flat is a plateau; the question a plateau asks is 'closure, or a bin the
    constraints cannot reach?' -- and only reading the bin answers it.
    """
    out = ["",
           "  cycle   " + "".join(f"{c:>7}" for c, _ in rows),
           "  cross%  " + "".join(f"{p:>7.1f}" for _, p in rows)]
    return "\n".join(out)
