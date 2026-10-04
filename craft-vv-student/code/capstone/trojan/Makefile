# cocotb flow for the secure_gate security track (Track 3).
#   make SIM=icarus                          # smoke test on the CLEAN variant (default)
#   make SIM=icarus DUT=$(CURDIR)/secure_gate_trojan.sv   # run against the trojan
#   make DUT=/path/to/secure_gate_clean.sv   # override the mutated DUT (mutation harness)
# Both variants share module name `secure_gate`; only one is compiled at a time.
# The smoke test PASSES on the clean variant and FAILS on the trojan (magic key).
TOPLEVEL_LANG ?= verilog
SIM           ?= icarus

DUT ?= $(CURDIR)/secure_gate_clean.sv
VERILOG_SOURCES = $(DUT)
TOPLEVEL = secure_gate
MODULE   = test_smoke

export PYTHONPATH := $(CURDIR)/../../lib:$(PYTHONPATH)

include $(shell cocotb-config --makefiles)/Makefile.sim
