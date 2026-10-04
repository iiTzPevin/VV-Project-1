# How the code in this packet is laid out (and the style your testbenches follow)

Read this once, in Week 1. It is the map of the `code/` folder and the handful
of rules every testbench in the course obeys. The **ALU** (Week 3) is the
worked example of all of it: `dut/alu.sv`, `lib/models/alu_model.py`, and
`tb/alu/`. When you start a new testbench, copy the shape of `tb/alu/`.

## Where things live

```
code/
  dut/            the designs you verify (alu.sv, fifo.sv, uart.sv, ...)
  dut/specs/      one short .md spec per design -- the contract you check against
  lib/models/     golden models in Python (imported as models.<name>)
  lib/craft_mutate/  the found/total mutation harness (use it; do not fork it)
  tb/<name>/      your testbench: Makefile + test_*.py + mutants_released.yaml
  formal/<name>/  SymbiYosys proofs (Week 8 on)
  capstone/       the three capstone tracks (Weeks 11-14)
  demos/          the class demos, each with a DEMO.md you can replay alone
  lib/craft_tmp.py   where scratch goes -- see below
  justfile        shortcuts: just test / mutate / cover / waves / demo / formal
```

Scratch files -- mutated copies of a DUT, simulator logs, formal work
directories -- go in `~/.vvtemp`, never `/tmp`, which you cannot write to on
eustis. Nothing scratch is written inside this directory, so a bugged DUT can
never end up in a commit by accident. `just clean-tmp` shows you what has piled
up and asks before deleting it; set `CRAFT_TMP` to put scratch elsewhere.

`../templates/` holds the starters for every Markdown file you turn in.
`../templates/INDEX.md` lists them.

## Two words that matter

**Released pool.** `tb/<name>/mutants_released.yaml` is your practice set. Run
it as often as you like: `just mutate alu`.

**Hidden pool.** Grading runs a larger set of bugs you have not seen. A suite
tuned to the released pool alone will score lower on the hidden one. That gap
is the point of the exercise -- close it by testing the design, not the list.

Scores are reported as **found / total**. This course says *found*, never
"killed."

## RTL style (when you write or modify RTL)

Everything must run under **both** Verilator 5.020 and Icarus.

- Synthesizable and cycle-based. No `#delay` in the design. Do not depend on
  X-propagation.
- ANSI ports, `logic` types, `always_ff` / `always_comb`. Parameterize widths.

## The Makefile

Copy `tb/alu/Makefile` and change three lines: `TOPLEVEL`, `MODULE`, and the
DUT path.

```make
TOPLEVEL_LANG ?= verilog
SIM ?= verilator
DUT ?= $(CURDIR)/../../dut/<name>.sv
VERILOG_SOURCES = $(DUT)
TOPLEVEL = <top_module>
MODULE   = test_<name>
export PYTHONPATH := $(CURDIR)/../../lib:$(PYTHONPATH)
include $(shell cocotb-config --makefiles)/Makefile.sim
```

If the design spans several files, add them:
`VERILOG_SOURCES = $(DUT) $(CURDIR)/../../dut/<extra>.sv`.

## Running things

Activate your environment first (see `../INSTALL.md`); on eustis that is
`source /opt/course/cocotb-env/bin/activate`. Then, from `code/`:

```bash
just test alu               # run the testbench under Verilator
just test alu icarus        # ...under Icarus
just mutate alu             # score your suite against the released pool
just waves alu              # write a waveform and print the file to open
just clean-tmp              # show what is in ~/.vvtemp, then clear it
```

Use **Icarus** while you iterate -- it recompiles faster. Use **Verilator**
for the assertion and coverage weeks, which need it. Keep any single run under
120 seconds; bound your stimulus.

## cocotb notes (v1.9.2)

- `from cocotb.triggers import RisingEdge, FallingEdge, Timer, ClockCycles`
- Clocked design: `cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())`
- Read an output with `int(dut.sig.value)`. Drive an input with
  `dut.sig.value = x`.
- Combinational design: set the inputs, `await Timer(1, units="ns")`, then read.
- The golden model is in `lib/models/`. Import it as
  `from models.<name> import ...`.
