# Week 7 / Session 2 live demo -- "the UART on the wire, then the first no-leak assertion"
#   make STEP=0        the starter run: one byte, one weak check (scores 3/8)
#   make STEP=1        loopback + logic-analyzer capture: the frame measured bit-time by bit-time
#   make STEP=2        forged bad stop bit -> frame_err pulses, rx_valid stays silent (8/8)
#   make STEP=3        the information-flow assertion on dut/leak_check.sv (holds)
#   make STEP=3 LEAK=1 inject -DLEAK_BUG: a_no_secret_leak fires on the first secure draw
# SVA needs Verilator's assertion engine; this demo is Verilator-only.
TOPLEVEL_LANG ?= verilog
override SIM  := verilator

STEP  ?= 0
STEPS := step0_starter step1_frame_walk step2_bad_stop step3_no_leak
MODULE = $(word $(shell expr $(STEP) + 1),$(STEPS))

ifeq ($(STEP),3)
# Step 3 swaps the whole bench: leak_check.sv is its own DUT and toplevel,
# with the information-flow assertion living inside it.
DUT ?= $(CURDIR)/../../dut/leak_check.sv
VERILOG_SOURCES = $(DUT)
TOPLEVEL = leak_check
ifeq ($(LEAK),1)
COMPILE_ARGS += -DLEAK_BUG
endif
else
# Steps 0-2: the UART with the SVA checker bound in (same trio as tb/uart_sva).
DUT ?= $(CURDIR)/../../dut/uart.sv
VERILOG_SOURCES = $(DUT) \
                  $(CURDIR)/../../dut/uart_sva.sv \
                  $(CURDIR)/../../dut/uart_bind.sv
TOPLEVEL = uart
endif

EXTRA_ARGS   += --assert
COMPILE_ARGS += -Wno-WIDTHEXPAND -Wno-WIDTHTRUNC

# Sources differ between steps (and with LEAK=1, and with a swapped DUT), so
# never share a build dir: a compiled model is newer than any source, and a
# plain dependency check would happily reuse the wrong one.
SIM_BUILD = $(CURDIR)/sim_build/step$(STEP)-$(notdir $(basename $(DUT)))$(if $(filter 1,$(LEAK)),-leakbug,)

export PYTHONPATH := $(CURDIR):$(CURDIR)/../../lib:$(PYTHONPATH)
# An SVA $stop abort writes no results file; keep it inside SIM_BUILD so a
# stale passing results.xml can never shadow a failing run (same reasoning
# as tb/uart_sva).
export COCOTB_RESULTS_FILE = $(SIM_BUILD)/results.xml

include $(shell cocotb-config --makefiles)/Makefile.sim
