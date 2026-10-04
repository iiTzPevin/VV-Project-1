# Week 3 / Session 1 live demo -- "your first self-checking testbench"
#   make STEP=0      drive without checking: green and unfalsifiable
#   make STEP=1      + golden model, sampled BEFORE the settle -> KEPT BROKEN
#   make STEP=2      the fix: settle, then sample
#   make STEP=3      assert all four outputs, not only result
# Add SIM=verilator to switch simulators; icarus recompiles faster.
TOPLEVEL_LANG ?= verilog
SIM           ?= icarus

STEP  ?= 0
STEPS := step0_drive_only step1_sample_early step2_settle_then_sample \
         step3_check_flags
MODULE = $(word $(shell expr $(STEP) + 1),$(STEPS))

DUT ?= $(CURDIR)/../../dut/alu.sv
VERILOG_SOURCES = $(DUT)
TOPLEVEL = alu

export PYTHONPATH := $(CURDIR):$(CURDIR)/../../lib:$(PYTHONPATH)

include $(shell cocotb-config --makefiles)/Makefile.sim
