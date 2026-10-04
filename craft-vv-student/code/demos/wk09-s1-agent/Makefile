# Week 9 / Session 1 live demo -- "the agent is your Week 4 testbench, standardized"
#   make STEP=0      the flat Week-4-style test (drive, sample, check in one loop)
#   make STEP=1      uvm_component skeleton -- phases announce their order
#   make STEP=2      driver + monitor + sequencer wired; subscriber prints traffic
#   make STEP=3      step 0's exact stimulus through the agent -- same digest out
# Add SIM=verilator to switch simulators; icarus recompiles faster.
# Override the stream:  make STEP=3 DEMO_SEED=7
TOPLEVEL_LANG ?= verilog
SIM           ?= icarus

STEP  ?= 0
STEPS := step0_flat step1_phases step2_wired step3_agent
MODULE = $(word $(shell expr $(STEP) + 1),$(STEPS))

DUT ?= $(CURDIR)/../../dut/axil_regfile.sv
VERILOG_SOURCES = $(DUT)
TOPLEVEL = axil_regfile

export PYTHONPATH := $(CURDIR):$(CURDIR)/../../lib:$(PYTHONPATH)

include $(shell cocotb-config --makefiles)/Makefile.sim
