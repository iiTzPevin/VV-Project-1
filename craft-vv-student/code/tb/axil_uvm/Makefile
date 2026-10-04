# cocotb + pyuvm flow for the Week 9 axil_regfile UVM environment (starter).
#   make            # run with Verilator (default)
#   make SIM=icarus # run with Icarus Verilog
#   make DUT=/path/to/axil_regfile.sv   # override the DUT (used by the mutation harness)
TOPLEVEL_LANG ?= verilog
SIM           ?= verilator

DUT ?= $(CURDIR)/../../dut/axil_regfile.sv
VERILOG_SOURCES = $(DUT)
TOPLEVEL = axil_regfile
MODULE   = test_axil_uvm

export PYTHONPATH := $(CURDIR)/../../lib:$(PYTHONPATH)

include $(shell cocotb-config --makefiles)/Makefile.sim
