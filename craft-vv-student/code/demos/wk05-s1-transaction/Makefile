# Week 5 / Session 1 live demo -- "the transaction is the unit of randomization"
#   make STEP=0      hand vectors (where Week 4 left us)
#   make STEP=1      pyvsc transaction, uniform random
#   make STEP=2      + full/empty/rd_data scoreboard
# Add SIM=verilator to switch simulators; icarus is faster to recompile.
TOPLEVEL_LANG ?= verilog
SIM           ?= icarus

STEP  ?= 0
STEPS := step0_hand step1_txn step2_scoreboard
MODULE = $(word $(shell expr $(STEP) + 1),$(STEPS))

DUT ?= $(CURDIR)/../../dut/fifo.sv
VERILOG_SOURCES = $(DUT)
TOPLEVEL = fifo

export PYTHONPATH := $(CURDIR):$(CURDIR)/../../lib:$(PYTHONPATH)

include $(shell cocotb-config --makefiles)/Makefile.sim
