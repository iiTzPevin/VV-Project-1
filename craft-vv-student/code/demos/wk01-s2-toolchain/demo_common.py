"""Shared helpers for the Week 1 Session 2 demo.

Steps 0 and 1 are toolchain commands (see the Makefile); only steps 2-3 are
cocotb modules, and they are a copy of tb/alu/test_alu.py plus one edit each.
"""
import os
import random

import cocotb


def seed(default=5):
    """Pin any randomness so the room sees the run we rehearsed.
    Override from the shell:  make STEP=3 DEMO_SEED=7
    The Week 1 vectors are directed; the habit is what this line teaches.
    """
    s = int(os.environ.get("DEMO_SEED", default))
    random.seed(s)
    cocotb.log.info(f"demo seed = {s}")
    return s
