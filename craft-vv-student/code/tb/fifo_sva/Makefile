# cocotb + Verilator flow for the Week-7 assertion-based FIFO testbench (STARTER).
#   make                      # run with Verilator, SVA enabled (default)
#   make DUT=/path/to/fifo.sv # override the DUT (used by the mutation harness)
#
# SVA needs Verilator's assertion engine, so this flow is Verilator-only
# (SIM is pinned below).  fifo_sva.sv is a bound checker and fifo_bind.sv wires
# it into every fifo instance; both are always taken from dut/ (never mutated),
# while DUT (the fifo itself) is what the harness swaps out.
TOPLEVEL_LANG ?= verilog
# SVA + `--assert` need Verilator's assertion engine, so force it even if the
# harness/justfile passes SIM=icarus (their default for the non-SVA weeks).
override SIM  := verilator

DUT ?= $(CURDIR)/../../dut/fifo.sv
VERILOG_SOURCES = $(DUT) \
                  $(CURDIR)/../../dut/fifo_sva.sv \
                  $(CURDIR)/../../dut/fifo_bind.sv
TOPLEVEL = fifo
MODULE   = test_fifo_sva

# Enable SystemVerilog assertions (the whole point of this week).
EXTRA_ARGS += --assert
# fifo.sv compares a 4-bit count against the 32-bit int DEPTH; Verilator makes
# that width warning fatal by default.  Waive it (compile-only) so the clean
# DUT builds -- you are not allowed to edit dut/fifo.sv.
COMPILE_ARGS += -Wno-WIDTHEXPAND

export PYTHONPATH := $(CURDIR)/../../lib:$(PYTHONPATH)

# Keep the JUnit results file inside SIM_BUILD so a plain `make` never leaves a
# stale results.xml in this dir. When an SVA `$stop` aborts the sim, cocotb
# writes no results file; the mutation harness would otherwise fall back to a
# leftover passing results.xml here and mis-score the mutant as SURVIVED. The
# harness overrides COCOTB_RESULTS_FILE on its command line, so this line only
# affects manual runs.
export COCOTB_RESULTS_FILE = $(SIM_BUILD)/results.xml

include $(shell cocotb-config --makefiles)/Makefile.sim
