# Week 6 / Session 1 live demo -- "the coverage model: coverpoints, bins, the cross"
#   make STEP=0      the inherited env: green, boundaries parked, no odometer
#   make STEP=1      occupancy + operation coverpoints -> both 100%, still blind
#   make STEP=2      the cross -> 66.7%, four empty cells, two of them mutants
# Coverage runs use Verilator, the Week 6 flow (see code/README). SIM=icarus works too.
# Override the stream:  make STEP=2 DEMO_SEED=7
TOPLEVEL_LANG ?= verilog
SIM           ?= verilator

STEP  ?= 0
STEPS := step0_blind step1_coverpoints step2_cross
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
