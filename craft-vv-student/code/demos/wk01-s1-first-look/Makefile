# Week 1 / Session 1 live demo -- "the bug a green test walks right past"
#   make STEP=0      the weak directed test: six vectors, both outputs checked -- PASS
#   make STEP=1      the missing vector (a==b, top bit set) -- FAILS, on purpose
#   make STEP=2      all 65,536 pairs, two observation points -- the C/O numbers
# Add SIM=verilator to switch simulators; icarus recompiles faster.
TOPLEVEL_LANG ?= verilog
SIM           ?= icarus

STEP  ?= 0
STEPS := step0_looks_fine step1_the_vector step2_observation
MODULE = $(word $(shell expr $(STEP) + 1),$(STEPS))

DUT ?= $(CURDIR)/addc.sv
VERILOG_SOURCES = $(DUT)
TOPLEVEL = addc

export PYTHONPATH := $(CURDIR):$(CURDIR)/../../lib:$(PYTHONPATH)

include $(shell cocotb-config --makefiles)/Makefile.sim
