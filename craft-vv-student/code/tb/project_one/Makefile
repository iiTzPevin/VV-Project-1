# cocotb + Verilator flow for the Project 1 FIFO testbench.
#   make            # run with Verilator (default)
#   make SIM=icarus # run with Icarus Verilog
#   make DUT=/path/to/fifo.sv   # override the DUT (used by the mutation harness)
TOPLEVEL_LANG ?= verilog
SIM           ?= verilator

DUT ?= $(CURDIR)/../../dut/fifo.sv
VERILOG_SOURCES = $(DUT)
TOPLEVEL = fifo
MODULE   = test_fifo

export PYTHONPATH := $(CURDIR):$(CURDIR)/../../lib:$(PYTHONPATH)

include $(shell cocotb-config --makefiles)/Makefile.sim