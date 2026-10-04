# Week 4 / Session 1 live demo -- "structure buys reuse, not detection"
#   make STEP=0      the Week-3 way: one function does every job -- green
#   make STEP=1      driver extracted: transactions in, pin wiggles out
#   make STEP=2      monitor + reference-queue scoreboard (FifoModel)
#   make STEP=3      the same tests rerun through the layers -- same digest,
#                    same found/total as step 0 (that is the claim)
# Add SIM=verilator to switch simulators; icarus recompiles faster.
# The stimulus is directed; DEMO_SEED is honored but changes nothing here.
TOPLEVEL_LANG ?= verilog
SIM           ?= icarus

STEP  ?= 0
STEPS := step0_monolith step1_driver step2_monitor_scoreboard step3_layers
MODULE = $(word $(shell expr $(STEP) + 1),$(STEPS))

DUT ?= $(CURDIR)/../../dut/fifo.sv
VERILOG_SOURCES = $(DUT)
TOPLEVEL = fifo

export PYTHONPATH := $(CURDIR):$(CURDIR)/../../lib:$(PYTHONPATH)

include $(shell cocotb-config --makefiles)/Makefile.sim
