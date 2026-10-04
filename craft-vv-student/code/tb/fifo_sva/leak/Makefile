# Runnable demo for the information-flow assertion in dut/leak_check.sv.
#   make                     # Verilator + SVA : a_no_secret_leak HOLDS (PASS)
#   make LEAK=1              # inject the leak (-DLEAK_BUG) : assertion FIRES (FAIL)
TOPLEVEL_LANG ?= verilog
override SIM  := verilator     # SVA + --assert need Verilator

DUT ?= $(CURDIR)/../../../dut/leak_check.sv
VERILOG_SOURCES = $(DUT)
TOPLEVEL = leak_check
MODULE   = test_leak

EXTRA_ARGS   += --assert
COMPILE_ARGS += -Wno-WIDTHEXPAND
ifeq ($(LEAK),1)
COMPILE_ARGS += -DLEAK_BUG
endif

export PYTHONPATH := $(CURDIR)/../../../lib:$(PYTHONPATH)

# Keep the results file inside SIM_BUILD so a plain `make` leaves nothing behind.
export COCOTB_RESULTS_FILE = $(SIM_BUILD)/results.xml

include $(shell cocotb-config --makefiles)/Makefile.sim
