# Week 9 / Session 2 live demo -- "stimulus is a library; the factory is the reuse lever"
#   make STEP=0      the sequence library: single-write, read-after-write, random-burst
#   make STEP=1      factory override: an error-injecting driver, zero edits elsewhere
#   make STEP=2      score the stub starter and the reference env vs the released pool
# Add SIM=verilator to switch simulators; icarus recompiles faster.
# Override the burst stream:  make STEP=0 DEMO_SEED=7
TOPLEVEL_LANG ?= verilog
SIM           ?= icarus
export SIM

STEP  ?= 0
STEPS := step0_sequences step1_factory step2_score
MODULE = $(word $(shell expr $(STEP) + 1),$(STEPS))

DUT ?= $(CURDIR)/../../dut/axil_regfile.sv
VERILOG_SOURCES = $(DUT)
TOPLEVEL = axil_regfile

export PYTHONPATH := $(CURDIR):$(CURDIR)/../../lib:$(PYTHONPATH)

ifeq ($(MODULE),step2_score)
# step 2 is a harness run, not a simulation -- no cocotb involved
.PHONY: all
all:
	python3 $(CURDIR)/step2_score.py
else
include $(shell cocotb-config --makefiles)/Makefile.sim
endif
