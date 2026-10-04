# Week 4 / Session 2 live demo -- "reproduce -> isolate -> waveform -> fix"
#   make STEP=0      plant released mutant ignore_full into $(BUGDIR)/fifo.sv,
#                    then show the Week-3 smoke passing on it (the silent drop)
#   make STEP=1      reproduce: Tuesday's layered TB, unchanged -- RED, on
#                    purpose; the scoreboard logs the divergence cycle
#   make STEP=2      isolate: nine writes, nothing else -- RED on the bug,
#                    green after the fix. Add WAVES=1 for sim_build/fifo.fst
#   make STEP=3      the fix: restore the write gate, rerun steps 2 and 1
# Steps 1-2 run against $(BUGDIR)/fifo.sv (default ~/.vvtemp/wk04-s2-bug) -- run
# STEP=0 first. The course DUT dut/fifo.sv is never touched.
# Scoring (the harness overrides DUT per mutant; STEP picks the module):
#   STEP=1 PYTHONPATH=$PWD/lib python3 -m craft_mutate.mutate \
#       --tb demos/wk04-s2-debug --dut dut/fifo.sv \
#       --pool tb/fifo/mutants_released.yaml --sim icarus
TOPLEVEL_LANG ?= verilog
SIM           ?= icarus

STEP  ?= 0
STEPS := step0_plant step1_reproduce step2_isolate step3_fix
MODULE = $(word $(shell expr $(STEP) + 1),$(STEPS))

CRAFT_TMP ?= $(HOME)/.vvtemp
BUGDIR ?= $(CRAFT_TMP)/wk04-s2-bug
DUT ?= $(BUGDIR)/fifo.sv
VERILOG_SOURCES = $(DUT)
TOPLEVEL = fifo

export PYTHONPATH := $(CURDIR):$(CURDIR)/../../lib:$(PYTHONPATH)
export BUGDIR
export SIM

ifeq ($(MODULE),step0_plant)
.PHONY: all
all:
	python3 $(CURDIR)/step0_plant.py
else ifeq ($(MODULE),step3_fix)
.PHONY: all
all:
	python3 $(CURDIR)/step3_fix.py
else
ifeq ($(wildcard $(DUT)),)
$(error no DUT at $(DUT) -- run 'make STEP=0' to plant the bug first)
endif
include $(shell cocotb-config --makefiles)/Makefile.sim
endif
