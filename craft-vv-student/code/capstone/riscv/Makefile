# cocotb flow for the RV32I capstone core (Track 1).
#   make SIM=icarus                 # run the smoke test with Icarus
#   make DUT=/path/to/rv32i_core.sv # override the mutated core (mutation harness)
# Only rv32i_core.sv is the mutated DUT; the harness (top + memories) is always
# compiled. $readmemh("program.hex") resolves relative to this directory.
TOPLEVEL_LANG ?= verilog
SIM           ?= icarus

DUT ?= $(CURDIR)/rv32i_core.sv
VERILOG_SOURCES = $(DUT) \
                  $(CURDIR)/rv32i_top.sv \
                  $(CURDIR)/rv32i_imem.sv \
                  $(CURDIR)/rv32i_dmem.sv
TOPLEVEL = rv32i_top
MODULE   = test_smoke

export PYTHONPATH := $(CURDIR)/../../lib:$(PYTHONPATH)

include $(shell cocotb-config --makefiles)/Makefile.sim
