# Week 2 / Session 2 live demo -- "the plan predicts the score"
#   make STEP=0      no plan: the instinct test, result-only, green -- and near-blind
#   make STEP=1      three vplan.md rows as three traceable directed tests
#   make STEP=2      + the We Do rows (VP-4 logical, VP-5 shifts): the finished mini plan
# Score a step against the released pool (found/total preview, from code/):
#   STEP=1 PYTHONPATH=$PWD/lib python3 -m craft_mutate.mutate --tb demos/wk02-s2-vplan \
#          --dut dut/alu.sv --pool tb/alu/mutants_released.yaml --sim icarus
TOPLEVEL_LANG ?= verilog
SIM           ?= icarus

STEP  ?= 0
STEPS := step0_no_plan step1_traceable step2_plan_complete
MODULE = $(word $(shell expr $(STEP) + 1),$(STEPS))

DUT ?= $(CURDIR)/../../dut/alu.sv
VERILOG_SOURCES = $(DUT)
TOPLEVEL = alu

export PYTHONPATH := $(CURDIR):$(CURDIR)/../../lib:$(PYTHONPATH)

include $(shell cocotb-config --makefiles)/Makefile.sim
