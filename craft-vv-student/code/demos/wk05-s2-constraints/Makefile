# Week 5 / Session 2 live demo -- "constraint solving and its two failure modes"
#   make STEP=0      carry-in from Session 1: unshaped, 7/8, full never reached
#   make STEP=1      over-constrained, LOUD  -> SolveFailure at the boundary
#   make STEP=2      over-constrained, QUIET -> solves fine, deletes the bug
#   make STEP=3      the dist-inside-implies trap: shaping that shapes nothing
#   make STEP=4      shaping that survives measurement -> parks on both boundaries
#   make STEP=5      the same shaping across 8 seeds -- a regression, not a run
# Add SIM=verilator to switch simulators; icarus recompiles faster.
# Override the stream:  make STEP=3 DEMO_SEED=7
TOPLEVEL_LANG ?= verilog
SIM           ?= icarus

STEP  ?= 0
STEPS := step0_start step1_overconstrained_fail step2_overconstrained_quiet \
         step3_dist_trap step4_shaped step5_seeded
MODULE = $(word $(shell expr $(STEP) + 1),$(STEPS))

DUT ?= $(CURDIR)/../../dut/fifo.sv
VERILOG_SOURCES = $(DUT)
TOPLEVEL = fifo

export PYTHONPATH := $(CURDIR):$(CURDIR)/../../lib:$(PYTHONPATH)

include $(shell cocotb-config --makefiles)/Makefile.sim
