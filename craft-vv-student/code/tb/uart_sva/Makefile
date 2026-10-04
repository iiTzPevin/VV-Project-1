# cocotb + Verilator flow for the Week-7 assertion-based UART testbench (STARTER).
#   make                       # run with Verilator, SVA enabled (default)
#   make DUT=/path/to/uart.sv  # override the DUT (used by the mutation harness)
#
# Same structure as tb/fifo_sva: uart_sva.sv is a bound checker and
# uart_bind.sv wires it into every uart instance; both always come from dut/
# (never mutated), while DUT (the uart itself) is what the harness swaps.
TOPLEVEL_LANG ?= verilog
# SVA + `--assert` need Verilator's assertion engine; force it even if the
# harness passes SIM=icarus.
override SIM  := verilator

DUT ?= $(CURDIR)/../../dut/uart.sv
VERILOG_SOURCES = $(DUT) \
                  $(CURDIR)/../../dut/uart_sva.sv \
                  $(CURDIR)/../../dut/uart_bind.sv
TOPLEVEL = uart
MODULE   = test_uart_sva

EXTRA_ARGS   += --assert
COMPILE_ARGS += -Wno-WIDTHEXPAND -Wno-WIDTHTRUNC

export PYTHONPATH := $(CURDIR)/../../lib:$(PYTHONPATH)

# Keep the JUnit results file inside SIM_BUILD (same reasoning as tb/fifo_sva:
# an SVA $stop abort must not leave a stale passing results.xml behind).
export COCOTB_RESULTS_FILE = $(SIM_BUILD)/results.xml

include $(shell cocotb-config --makefiles)/Makefile.sim
