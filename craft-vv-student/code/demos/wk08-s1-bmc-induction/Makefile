# Week 8 / Session 1 live demo -- "BMC finds the bug; induction proves it gone"
#   make STEP=0   the shipped FIFO safety proof: bmc + prove, both PASS
#   make STEP=1   plant a released mutant into a scratch copy -> BMC counterexample
#   make STEP=2   a TRUE property (count <= DEPTH+1) that FAILS k-induction
#   make STEP=3   + the strengthening assert (count <= DEPTH) -> converges
# Variants worth showing live:
#   make STEP=1 MUT=count_wr_dec     # a different released mutant, shorter trace
#   make STEP=1 MUT=rd_data_wrptr    # a mutant these properties CANNOT find (PASS)
# Steps are .sby files, not cocotb: each runs SymbiYosys (smtbmc + z3) and
# leaves its work directory (trace.vcd on a FAIL) next to this Makefile.
# score:  python3 formal_score.py   # found/total for the invariant set vs the pool

STEP  ?= 0
STEPS := step0_proof step1_planted_bmc step2_loose_bound step3_strengthened
NAME   = $(word $(shell expr $(STEP) + 1),$(STEPS))

# plant_bug.py mutates a scratch copy of this DUT per the released pool entry
# MUT; the repo RTL is never edited. Steps 0/2/3 name their sources in their
# .sby files (SymbiYosys has no DUT override on the command line).
export DUT  ?= $(CURDIR)/../../dut/fifo.sv
export POOL ?= $(CURDIR)/../../tb/fifo_crv/mutants_released.yaml
MUT   ?= full_offbyone

# STEP=1 runs the .sby plant_bug.py generates, because SymbiYosys cannot expand
# a variable inside [files] and the planted DUT now lives under $CRAFT_TMP.
SBY = $(if $(filter 1,$(STEP)),step1_planted_bmc.gen,$(NAME))

step:
ifeq ($(STEP),1)
	python3 $(CURDIR)/plant_bug.py $(MUT)
endif
	cd $(CURDIR) && sby -f $(SBY).sby

.PHONY: step
