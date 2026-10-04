# Week 8 / Session 2 live demo -- "prove the backdoor absent -- and know what
# 'absent' bought you"
#   make STEP=0   honest arbiter: k-induction proves the contract for all time
#   make STEP=1   swap in dut/arbiter_trojan.sv -> BMC hands back the trigger,
#                 then show_trigger.py reads req/grant off the trace
#   make STEP=2   add ONE environment assume -> same netlist now "proves clean"
# Steps are .sby files, not cocotb: each runs SymbiYosys (smtbmc + z3) and
# leaves its work directory (trace.vcd on a FAIL) next to this Makefile.
# The safety contract lives inside the DUTs' `ifdef FORMAL` blocks
# (dut/arbiter.sv, dut/arbiter_trojan.sv) -- the same three asserts in both.

STEP  ?= 0
STEPS := step0_good step1_trojan step2_assume_env
NAME   = $(word $(shell expr $(STEP) + 1),$(STEPS))

step:
	cd $(CURDIR) && sby -f $(NAME).sby
ifeq ($(STEP),1)
	python3 $(CURDIR)/show_trigger.py
endif

.PHONY: step
