# Week 7 / Session 1 live demo -- "say what must always be true -- then prove it fired"
#   make STEP=0   two layers on clean RTL: immediate scoreboard + bound SVA, both green
#   make STEP=1   same walk, planted ignore_full bug -> a_no_overflow fires by name (kept broken)
#   make STEP=2   the vacuity trap: same bug compiled in, weak stimulus -> all green, covers at 0
# Variants worth showing live:
#   make STEP=2 DEMO_SEED=8                             # the walk reaches full -> same run fires
#   make STEP=2 DEMO_SEED=8 DUT=$$PWD/../../dut/fifo.sv # clean RTL: green AND covers > 0
# SVA needs Verilator's assertion engine; this demo is Verilator-only.
TOPLEVEL_LANG ?= verilog
override SIM  := verilator

STEP  ?= 0
STEPS := step0_two_checkers step1_planted_bug step2_vacuity
MODULE = $(word $(shell expr $(STEP) + 1),$(STEPS))

# Steps 1-2 run dut/fifo.sv with the released ignore_full mutant planted into
# a scratch copy (plant_bug.py); the repo's RTL is never touched. A DUT=... on
# the command line (yours or the mutation harness's) still wins.
DUT ?= $(CURDIR)/../../dut/fifo.sv
ifneq ($(filter 1 2,$(STEP)),)
DUT = $(shell python3 $(CURDIR)/plant_bug.py ignore_full)
endif

VERILOG_SOURCES = $(DUT) \
                  $(CURDIR)/../../dut/fifo_sva.sv \
                  $(CURDIR)/../../dut/fifo_bind.sv
TOPLEVEL = fifo

EXTRA_ARGS   += --assert
COMPILE_ARGS += -Wno-WIDTHEXPAND

# Step 2 adds the student-style property + its covers, and counts the covers.
ifeq ($(STEP),2)
VERILOG_SOURCES += $(CURDIR)/step2_vacuity.sv
EXTRA_ARGS      += --coverage-user
endif

# Sources differ between steps -- and between DUTs within a step (the clean
# vs planted variants of step 2). Key the build dir on both, or make will
# happily reuse a model built from the other RTL: the compiled Vtop is newer
# than any source file, so a plain dependency check never notices the swap.
SIM_BUILD = $(CURDIR)/sim_build/step$(STEP)-$(notdir $(basename $(DUT)))

export PYTHONPATH := $(CURDIR):$(CURDIR)/../../lib:$(PYTHONPATH)
# An SVA $stop abort writes no results file; keep it inside SIM_BUILD so a
# stale passing results.xml can never shadow a failing run (same reasoning
# as tb/fifo_sva).
export COCOTB_RESULTS_FILE = $(SIM_BUILD)/results.xml

# Default goal: run the step, then print what every `cover property` counted.
# Verilator 5.020 always writes coverage.dat into the cwd (its runtime has no
# file argument); park it inside SIM_BUILD so the demo dir stays clean.
step: sim
	@if [ -f $(CURDIR)/coverage.dat ]; then \
	    mv $(CURDIR)/coverage.dat $(SIM_BUILD)/coverage.dat; fi
	@python3 $(CURDIR)/show_covers.py $(SIM_BUILD)/coverage.dat

include $(shell cocotb-config --makefiles)/Makefile.sim
