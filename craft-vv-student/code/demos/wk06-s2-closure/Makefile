# Week 6 / Session 2 live demo -- "closure: the hole, the constraint, the gap"
#   make STEP=0      the hole, re-established: cross parked at 66.7%, trace flat
#   make STEP=1      c_tidy deleted -> trace steps up, cross closes, 8/8
#   make STEP=2      both envs back to back: the coverage half of the correlation
#   make STEP=3      100% of a weak (crossless) model while two mutants survive
# Coverage runs use Verilator, the Week 6 flow (see code/README). SIM=icarus works too.
# Override the stream:  make STEP=1 DEMO_SEED=7
TOPLEVEL_LANG ?= verilog
SIM           ?= verilator

STEP  ?= 0
STEPS := step0_hole step1_close step2_correlate step3_weak_model
MODULE = $(word $(shell expr $(STEP) + 1),$(STEPS))

DUT ?= $(CURDIR)/../../dut/fifo.sv
VERILOG_SOURCES = $(DUT)
TOPLEVEL = fifo

# fifo.sv compares a 4-bit count against the 32-bit int DEPTH; Verilator makes
# that width warning fatal by default. Waive it (compile-only), as fifo_sva does.
ifeq ($(SIM),verilator)
COMPILE_ARGS += -Wno-WIDTHEXPAND
endif

export PYTHONPATH := $(CURDIR):$(CURDIR)/../../lib:$(PYTHONPATH)

include $(shell cocotb-config --makefiles)/Makefile.sim
