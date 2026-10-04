# Week 1 / Session 2 live demo -- "the toolchain, end to end"
#   make STEP=0      the environment check: bash ../../setup/verify_env.sh
#   make STEP=1      first green run: the provided ALU testbench, untouched
#                    (add WAVES=1 to also write tb/alu/sim_build/alu.fst for GTKWave)
#   make STEP=2      the first edit: one added vector -- FAILS, on purpose
#   make STEP=3      the fix: the expectation moves into the golden model
# Steps 2-3 run a COPY of tb/alu/test_alu.py held in this directory, so the
# course starter stays untouched. Add SIM=verilator to match the deck;
# icarus recompiles faster.
TOPLEVEL_LANG ?= verilog
SIM           ?= icarus

STEP  ?= 0
STEPS := step0_verify_env step1_first_green step2_add_vector step3_model_width
MODULE = $(word $(shell expr $(STEP) + 1),$(STEPS))

DUT ?= $(CURDIR)/../../dut/alu.sv
VERILOG_SOURCES = $(DUT)
TOPLEVEL = alu

export PYTHONPATH := $(CURDIR):$(CURDIR)/../../lib:$(PYTHONPATH)

ifeq ($(MODULE),step0_verify_env)
.PHONY: all
all:
	bash $(CURDIR)/../../setup/verify_env.sh
else ifeq ($(MODULE),step1_first_green)
.PHONY: all
all:
	$(MAKE) -C $(CURDIR)/../../tb/alu SIM=$(SIM)
else
include $(shell cocotb-config --makefiles)/Makefile.sim
endif
