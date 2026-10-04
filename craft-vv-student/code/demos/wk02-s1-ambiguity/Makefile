# Week 2 / Session 1 live demo -- "one sentence, two compliant parts"
#   make STEP=0      the overflow test the vague sentence permits: green on BOTH readings
#   make STEP=1      the divergence sweep -> witness vector (deliberately red; keep it broken)
#   make STEP=2      the sharpened requirement R-ADD-OVF vs the course ALU (dut/alu.sv)
# Steps 0-1 elaborate alu_pair.sv (both readings side by side); step 2 the course ALU.
# Override the stream:  make STEP=1 DEMO_SEED=7
TOPLEVEL_LANG ?= verilog
SIM           ?= icarus

STEP  ?= 0
STEPS := step0_two_readings step1_divergence step2_sharpened
MODULE = $(word $(shell expr $(STEP) + 1),$(STEPS))

ifeq ($(STEP),2)
DUT ?= $(CURDIR)/../../dut/alu.sv
VERILOG_SOURCES = $(DUT)
TOPLEVEL = alu
else
DUT ?= $(CURDIR)/alu_pair.sv
VERILOG_SOURCES = $(DUT) $(CURDIR)/alu_ovf_signed.sv $(CURDIR)/alu_ovf_carry.sv
TOPLEVEL = alu_pair
endif

# steps 0-1 and step 2 elaborate different toplevels; keep their builds apart
SIM_BUILD ?= sim_build_$(TOPLEVEL)

export PYTHONPATH := $(CURDIR):$(CURDIR)/../../lib:$(PYTHONPATH)

include $(shell cocotb-config --makefiles)/Makefile.sim
