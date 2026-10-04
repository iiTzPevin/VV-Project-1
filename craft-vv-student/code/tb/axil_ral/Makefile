# cocotb flow for the Week 10 axil_regfile register (RAL-style) tests (starter).
#   make            # run with Verilator (default)
#   make SIM=icarus # run with Icarus Verilog
#   make DUT=/path/to/axil_regfile.sv   # override the DUT (used by the mutation harness)
TOPLEVEL_LANG ?= verilog
SIM           ?= verilator

DUT ?= $(CURDIR)/../../dut/axil_regfile.sv
VERILOG_SOURCES = $(DUT)
TOPLEVEL = axil_regfile
MODULE   = test_axil_ral

export PYTHONPATH := $(CURDIR)/../../lib:$(PYTHONPATH)

include $(shell cocotb-config --makefiles)/Makefile.sim
