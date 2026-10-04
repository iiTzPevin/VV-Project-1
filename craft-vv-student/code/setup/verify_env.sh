#!/usr/bin/env bash
# CRAFT V&V environment check. Run after setup:  bash setup/verify_env.sh
GREEN='\033[0;32m'; RED='\033[0;31m'; YEL='\033[0;33m'; NC='\033[0m'
ok(){ printf "${GREEN}OK${NC}   %s: %s\n" "$1" "$2"; }
miss(){ printf "${RED}MISS${NC} %s (needed for %s)\n" "$1" "$2"; }
opt(){ printf "${YEL}opt${NC}  %s (%s)\n" "$1" "$2"; }

# /tmp is not writable for students on eustis, so every scratch file the course
# writes goes here instead. Override with CRAFT_TMP.
CRAFT_TMP="${CRAFT_TMP:-$HOME/.vvtemp}"
SMOKE_LOG="$CRAFT_TMP/craft_smoke.log"

echo "=== scratch ==="
if mkdir -p "$CRAFT_TMP" 2>/dev/null && [ -w "$CRAFT_TMP" ]; then
  ok "scratch" "$CRAFT_TMP is writable ('just clean-tmp' empties it)"
else
  miss "scratch" "every step that writes a file. Cannot write $CRAFT_TMP -- set CRAFT_TMP to a directory you own"
fi

echo ""
echo "=== CRAFT V&V toolchain ==="
for pair in "verilator:Wk3-10" "iverilog:Wk3-10 (fast harness)" "yosys:Wk8" "z3:Wk8"; do
  t=${pair%%:*}; why=${pair#*:}
  if command -v "$t" >/dev/null 2>&1; then
    # Icarus uses -V; the rest use --version.
    case "$t" in iverilog) v=$("$t" -V 2>&1 | head -1);; *) v=$("$t" --version 2>&1 | head -1);; esac
    ok "$t" "$v"
  else miss "$t" "$why"; fi
done
command -v sby >/dev/null 2>&1 && ok "sby" "$(sby --version 2>&1 | head -1)" || miss "sby" "Wk8 formal"
command -v gtkwave >/dev/null 2>&1 && ok "gtkwave" "waveviewer" || opt "gtkwave" "waveform viewing"
command -v just >/dev/null 2>&1 && ok "just" "$(just --version 2>&1 | head -1)" || opt "just" "recipe runner -- bash setup/install_just.sh"

echo ""
echo "=== Python stack ==="
echo "python: $(python3 --version 2>&1);  venv: ${VIRTUAL_ENV:-<none active>}"
for m in "cocotb:Wk3-10" "cocotb_coverage:Wk6" "vsc:Wk5" "pyuvm:Wk9-10" "yaml:harness"; do
  mod=${m%%:*}; why=${m#*:}
  if python3 -c "import $mod" >/dev/null 2>&1; then
    v=$(python3 -c "import $mod; print(getattr($mod,'__version__',''))" 2>/dev/null)
    ok "$mod" "$v"
  else miss "python:$mod" "$why"; fi
done

echo ""
echo "=== lecture-demo premises ==="
# Week 5 Session 2 is built on pyvsc applying a `dist` even when the `implies`
# guarding it is false. That is a tool behavior, not a law of nature: if a
# future pyvsc gates dist correctly, the demo teaches the opposite of what the
# room will see. Assert it here so the failure surfaces at setup, not in class.
if python3 -c "import vsc" >/dev/null 2>&1; then
  guard=$(python3 - <<'PYEOF' 2>/dev/null
import random, vsc
FILL, DRAIN = 0, 1
@vsc.randobj
class T:
    def __init__(self):
        self.w = vsc.rand_bit_t(1); self.p = vsc.uint8_t(FILL)
    @vsc.constraint
    def c(self):
        with vsc.implies(self.p == FILL):
            vsc.dist(self.w, [vsc.weight(1, 85), vsc.weight(0, 15)])
random.seed(5); t = T(); out = []
for ph in (FILL, DRAIN):
    t.p = ph; n = 0
    for _ in range(400):
        t.randomize(); n += int(t.w)
    out.append(n / 400)
print(f"{out[0]:.2f} {out[1]:.2f}")
PYEOF
)
  set -- $guard
  if [ -n "$2" ] && python3 -c "import sys; sys.exit(0 if float('$2') > 0.7 else 1)" 2>/dev/null; then
    ok "wk5-dist-guard" "dist ignores implies (P=$2 with guard false) -- demo premise holds"
  else
    miss "wk5-dist-guard" "pyvsc now gates dist (P=${2:-?}); Week 5 Session 2 demo + slides need revisiting"
  fi
else
  opt "wk5-dist-guard" "install pyvsc first"
fi

echo ""
echo "=== end-to-end smoke (ALU under icarus) ==="
# The instructor master carries solutions/; the student packet ships only tb/
# (make_student_dist.sh strips solutions/ on purpose). Prefer the reference
# testbench when it is present, otherwise smoke-test the starter -- which is
# exactly what HW1 asks students to run.
CODE_DIR="$(dirname "$0")/.."
if   [ -d "$CODE_DIR/solutions/alu" ]; then SMOKE_DIR="$CODE_DIR/solutions/alu"; SMOKE_WHAT="ALU reference testbench passes"
elif [ -d "$CODE_DIR/tb/alu" ];        then SMOKE_DIR="$CODE_DIR/tb/alu";        SMOKE_WHAT="ALU starter testbench passes"
else SMOKE_DIR=""; fi

if [ -z "$SMOKE_DIR" ]; then
  miss "smoke" "no ALU testbench found (expected code/tb/alu)"
elif command -v iverilog >/dev/null 2>&1 && python3 -c "import cocotb" >/dev/null 2>&1; then
  if make -s -C "$SMOKE_DIR" SIM=icarus >"$SMOKE_LOG" 2>&1 && grep -q "FAIL=0" "$SMOKE_LOG"; then
    ok "smoke" "$SMOKE_WHAT"
  else
    miss "smoke" "see $SMOKE_LOG"
  fi
else
  opt "smoke" "install iverilog + cocotb first"
fi
echo "=== done ==="
