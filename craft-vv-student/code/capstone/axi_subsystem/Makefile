# cocotb flow for the AXI-ish interconnect subsystem (Track 2).
#   make SIM=icarus                    # run the smoke test with Icarus
#   make DUT=/path/to/axi_subsystem.sv # override the mutated DUT (mutation harness)
# axi_subsystem.sv (arbiter + bus + peripherals) is the mutated DUT; fifo.sv is
# copied in from dut/fifo.sv and is always compiled alongside (not mutated here).
TOPLEVEL_LANG ?= verilog
SIM           ?= icarus

DUT ?= $(CURDIR)/axi_subsystem.sv
VERILOG_SOURCES = $(DUT) $(CURDIR)/fifo.sv
TOPLEVEL = axi_subsystem
MODULE   = test_smoke

export PYTHONPATH := $(CURDIR)/../../lib:$(PYTHONPATH)

include $(shell cocotb-config --makefiles)/Makefile.sim
