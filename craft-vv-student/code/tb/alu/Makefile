# cocotb + Verilator flow for the ALU testbench.
#   make            # run with Verilator (default)
#   make SIM=icarus # run with Icarus Verilog
#   make DUT=/path/to/alu.sv   # override the DUT (used by the mutation harness)
TOPLEVEL_LANG ?= verilog
SIM           ?= verilator

DUT ?= $(CURDIR)/../../dut/alu.sv
VERILOG_SOURCES = $(DUT)
TOPLEVEL = alu
MODULE   = test_alu

export PYTHONPATH := $(CURDIR)/../../lib:$(PYTHONPATH)

include $(shell cocotb-config --makefiles)/Makefile.sim
