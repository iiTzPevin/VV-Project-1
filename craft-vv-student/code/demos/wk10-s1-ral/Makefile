# Week 10 / Session 1 live demo -- "a register is a policy, not a signal"
#   make STEP=0      raw read/write pairs vs the map -- no model, passes, proves storage
#   make STEP=1      the register model + generic reset walk (mirror included)
#   make STEP=2      bit-bash + access-policy walk (RO rejects, W1C cannot be set)
#   make STEP=3      the locked SECURE register: unauthorized write dropped, INTR[0] latch
# Plant a released mutant first (python3 plant.py <id>), then re-run a step with
#   make STEP=1 DUT=~/.vvtemp/wk10-mutants/axil_regfile__<id>.sv
# Add SIM=verilator to switch simulators; icarus recompiles faster.
TOPLEVEL_LANG ?= verilog
SIM           ?= icarus

STEP  ?= 0
STEPS := step0_raw step1_reset step2_bitbash step3_secure
MODULE = $(word $(shell expr $(STEP) + 1),$(STEPS))

DUT ?= $(CURDIR)/../../dut/axil_regfile.sv
VERILOG_SOURCES = $(DUT)
TOPLEVEL = axil_regfile

# One build dir per DUT file, so switching DUT= mid-demo can never reuse a
# stale binary compiled from the previous DUT.
SIM_BUILD ?= sim_build/$(notdir $(patsubst %/,%,$(dir $(abspath $(DUT)))))_$(notdir $(basename $(DUT)))

export PYTHONPATH := $(CURDIR):$(CURDIR)/../../lib:$(PYTHONPATH)

include $(shell cocotb-config --makefiles)/Makefile.sim
