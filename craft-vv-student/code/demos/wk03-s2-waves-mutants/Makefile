# Week 3 / Session 2 live demo -- "waves to localize, mutants to measure"
#   make plant MUTANT=add2sub    apply one released mutant -> $(CRAFT_TMP)/alu_add2sub.sv
#   make STEP=0 DUT=~/.vvtemp/alu_add2sub.sv SIM=verilator VERILATOR_TRACE=1
#                                run on the planted bug; the log and dump.vcd name
#                                the first divergent time
#   make STEP=1                  Session 1's endpoint, green on clean RTL
#   make STEP=2                  + the equal-operand carry vector
# Score a step against the released pool (STEP selects the module):
#   STEP=1 python3 -m craft_mutate.mutate --tb demos/wk03-s2-waves-mutants \
#       --pool tb/alu/mutants_released.yaml --sim icarus
TOPLEVEL_LANG ?= verilog
SIM           ?= icarus

STEP  ?= 0
STEPS := step0_first_divergence step1_survivors step2_strengthened
MODULE = $(word $(shell expr $(STEP) + 1),$(STEPS))

DUT ?= $(CURDIR)/../../dut/alu.sv
VERILOG_SOURCES = $(DUT)
TOPLEVEL = alu

export PYTHONPATH := $(CURDIR):$(CURDIR)/../../lib:$(PYTHONPATH)

include $(shell cocotb-config --makefiles)/Makefile.sim

# Write a copy of the DUT with one released mutant applied, for the step 0
# wave walk. Uses the same apply code the harness scores with.
MUTANT ?= add2sub
CRAFT_TMP ?= $(HOME)/.vvtemp
.PHONY: plant
plant:
	@mkdir -p "$(CRAFT_TMP)"
	cd $(CURDIR)/../.. && PYTHONPATH=$$PWD/lib python3 -c "import yaml; from craft_mutate.mutate import apply_mutant; from craft_tmp import craft_tmp_file; mut = next(m for m in yaml.safe_load(open('tb/alu/mutants_released.yaml'))['mutants'] if m['id'] == '$(MUTANT)'); out = str(craft_tmp_file('alu_$(MUTANT).sv')); open(out, 'w').write(apply_mutant(open('dut/alu.sv').read(), mut)); print('planted', mut['id'], '->', out, '--', mut['desc'])"
