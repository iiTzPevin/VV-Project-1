# Week 10 / Session 2 live demo -- "signoff is a dashboard, not a number"
#   make STEP=0      lint the register file (verilator --lint-only as the
#                    verible stand-in; both command lines are printed)
#   make STEP=1      the locked-register assertion (cocotb, icarus)
#   make STEP=2      the signoff dashboard -- measures lint, line coverage,
#                    found/total (reference AND starter), security, checks
# Plant a defect first (python3 plant.py <id>), then re-run a step with
#   make STEP=0 DUT=~/.vvtemp/wk10-mutants/lint_latch/axil_regfile.sv
# Steps 0 and 2 are plain scripts (lint / harness drivers, not simulations);
# step 1 is a cocotb run like every other demo step this course.
TOPLEVEL_LANG ?= verilog
SIM           ?= icarus

STEP  ?= 0
STEPS := step0_lint step1_policy step2_dashboard
MODULE = $(word $(shell expr $(STEP) + 1),$(STEPS))

DUT ?= $(CURDIR)/../../dut/axil_regfile.sv
VERILOG_SOURCES = $(DUT)
TOPLEVEL = axil_regfile

# One build dir per DUT file, so switching DUT= mid-demo can never reuse a
# stale binary compiled from the previous DUT.
SIM_BUILD ?= sim_build/$(notdir $(patsubst %/,%,$(dir $(abspath $(DUT)))))_$(notdir $(basename $(DUT)))

export PYTHONPATH := $(CURDIR):$(CURDIR)/../../lib:$(PYTHONPATH)

ifeq ($(filter $(MODULE),step0_lint step2_dashboard),)
include $(shell cocotb-config --makefiles)/Makefile.sim
else
.PHONY: run
run:
	python3 $(CURDIR)/$(MODULE).py $(DUT)
.DEFAULT_GOAL := run
endif
