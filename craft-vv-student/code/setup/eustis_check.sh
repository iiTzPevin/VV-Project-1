#!/usr/bin/env bash
# ============================================================
#  eustis_check.sh -- functional smoke tests for the CRAFT V&V toolchain.
#
#  verify_env.sh answers "is it installed?".  This answers "does it work?".
#  Run from the packet root:   bash code/setup/eustis_check.sh
#  Add --waves to also generate a waveform and launch GTKWave (needs ssh -Y).
# ============================================================
GRN='\033[0;32m'; RED='\033[0;31m'; YEL='\033[0;33m'; NC='\033[0m'
pass(){ printf "${GRN}PASS${NC} %s\n" "$1"; }
fail(){ printf "${RED}FAIL${NC} %s -- %s\n" "$1" "$2"; RC=1; }
warn(){ printf "${YEL}WARN${NC} %s -- %s\n" "$1" "$2"; }
RC=0
HERE="$(cd "$(dirname "$0")/.." && pwd)"     # .../code
cd "$HERE" || exit 1

# /tmp is not writable for students on eustis. Every log this script writes goes
# under the course scratch root instead; `just clean-tmp` empties it.
CRAFT_TMP="${CRAFT_TMP:-$HOME/.vvtemp}"
if ! mkdir -p "$CRAFT_TMP" 2>/dev/null || [ ! -w "$CRAFT_TMP" ]; then
  printf "${RED}FAIL${NC} scratch -- cannot write %s. Set CRAFT_TMP to a directory you own.\n" "$CRAFT_TMP"
  exit 1
fi

echo "=== 1. versions ==="
for t in verilator iverilog gtkwave yosys z3 sby just; do
  if command -v "$t" >/dev/null 2>&1; then
    case "$t" in
      iverilog) v=$(iverilog -V 2>&1 | head -1);;
      gtkwave)  v=$(gtkwave --version 2>&1 | head -1);;
      *)        v=$("$t" --version 2>&1 | head -1);;
    esac
    pass "$t: $v"
  else
    case "$t" in
      yosys|z3|sby) warn "$t" "absent -- TIER 2, first needed Week 8 (Oct 13)";;
      just)         warn "just" "absent -- optional; use the make commands below instead";;
      *)            fail "$t" "MISSING -- required from Week 3";;
    esac
  fi
done

echo; echo "=== 2. simulation: does the ALU testbench actually pass? ==="
for sim in icarus verilator; do
  command -v "$( [ $sim = icarus ] && echo iverilog || echo verilator )" >/dev/null 2>&1 || { warn "$sim" "simulator absent, skipped"; continue; }
  rm -rf tb/alu/sim_build
  if make -s -C tb/alu SIM=$sim >"$CRAFT_TMP/craft_$sim.log" 2>&1 && grep -q "FAIL=0" "$CRAFT_TMP/craft_$sim.log"; then
    pass "$sim: $(grep -oE 'TESTS=[0-9]+ PASS=[0-9]+ FAIL=[0-9]+' "$CRAFT_TMP/craft_$sim.log" | tail -1)"
  else
    fail "$sim" "see $CRAFT_TMP/craft_$sim.log"
  fi
done

echo; echo "=== 3. mutation harness (the graded mechanism) ==="
rm -rf tb/alu/sim_build
if PYTHONPATH=lib timeout 600 python -m craft_mutate.mutate \
     --tb tb/alu --pool tb/alu/mutants_released.yaml --sim icarus >"$CRAFT_TMP/craft_mut.log" 2>&1; then
  SCORE=$(grep -oE 'found/total = [0-9]+/[0-9]+ +=  ?[0-9.]+%' "$CRAFT_TMP/craft_mut.log" | tail -1)
  [ -n "$SCORE" ] && pass "harness: $SCORE (a LOW score here is correct -- the starter is meant to be weak)" \
                  || fail "harness" "ran but printed no score; see $CRAFT_TMP/craft_mut.log"
else
  fail "harness" "see $CRAFT_TMP/craft_mut.log"
fi

echo; echo "=== 4. python stack (exercised, not just imported) ==="
python - <<'PY'
import sys
def ok(n,d=""): print(f"\033[0;32mPASS\033[0m {n}" + (f": {d}" if d else ""))
def bad(n,e):   print(f"\033[0;31mFAIL\033[0m {n} -- {e}"); sys.exit(0)
try:
    import cocotb; ok("cocotb", cocotb.__version__)
except Exception as e: bad("cocotb", e)
try:                                    # solver actually solves
    import vsc
    @vsc.randobj
    class C:
        def __init__(self): self.a = vsc.rand_bit_t(8)
        @vsc.constraint
        def lim(self): self.a < 10
    o=C(); o.randomize()
    assert o.a < 10, f"constraint violated (a={o.a})"
    ok("pyvsc", f"randomize() honoured a<10 -> a={o.a}")
except Exception as e: print(f"\033[0;31mFAIL\033[0m pyvsc -- {e}")
try:                                    # coverage actually samples
    from cocotb_coverage.coverage import CoverPoint, coverage_db
    @CoverPoint("top.v", xf=lambda x: x, bins=[0,1,2])
    def s(x): pass
    for i in (0,1,2): s(i)
    ok("cocotb-coverage", f"coverage {coverage_db['top.v'].cover_percentage:.0f}% after 3 samples")
except Exception as e: print(f"\033[0;31mFAIL\033[0m cocotb-coverage -- {e}")
try:
    import pyuvm
    from pyuvm import uvm_component, uvm_sequence
    ok("pyuvm", f"{getattr(pyuvm,'__version__','?')} (uvm_component, uvm_sequence resolve)")
except Exception as e: print(f"\033[0;31mFAIL\033[0m pyuvm -- {e}")
try:
    import yaml; ok("pyyaml", yaml.__version__)
except Exception as e: bad("pyyaml", e)
PY

echo; echo "=== 5. waveforms + viewer ==="
rm -rf tb/alu/sim_build
make -s -C tb/alu SIM=icarus WAVES=1 >"$CRAFT_TMP/craft_waves.log" 2>&1
WAVE=$(find tb/alu -name '*.fst' -o -name '*.vcd' 2>/dev/null | head -1)
if [ -n "$WAVE" ]; then
  pass "waveform written: $WAVE  ($(du -h "$WAVE" | cut -f1))"
else
  fail "waveform" "WAVES=1 produced nothing; see $CRAFT_TMP/craft_waves.log"
fi
if [ -n "$DISPLAY" ]; then
  pass "DISPLAY is set ($DISPLAY)"
  if command -v xset >/dev/null 2>&1 && xset q >/dev/null 2>&1; then
    pass "X server reachable -- GTKWave should open a window"
  else
    warn "X server" "DISPLAY set but not reachable; reconnect with: ssh -Y <you>@eustis.eecs.ucf.edu"
  fi
else
  warn "DISPLAY" "not set -- reconnect with: ssh -Y <you>@eustis.eecs.ucf.edu (macOS needs XQuartz)"
fi
if [ "${1:-}" = "--waves" ] && [ -n "$WAVE" ] && [ -n "$DISPLAY" ]; then
  echo "launching GTKWave on $WAVE ... close the window to finish"
  gtkwave "$WAVE" >/dev/null 2>&1
fi

echo; echo "=== 6. home directory and filesystem (VS Code Remote-SSH depends on this) ==="
printf '  %-20s %s\n' "HOME" "$HOME"
printf '  %-20s %s\n' "host" "$(hostname -f 2>/dev/null || hostname)"
FSLINE=$(df -PTh "$HOME" 2>/dev/null | tail -1)
FSTYPE=$(echo "$FSLINE" | awk '{print $2}')
printf '  %-20s %s (%s used, %s free)\n' "home filesystem" "${FSTYPE:-unknown}" \
       "$(echo "$FSLINE"|awk '{print $6}')" "$(echo "$FSLINE"|awk '{print $5}')"
case "$FSTYPE" in
  nfs*|afs*|cifs|smb*|lustre|gpfs|fuse*)
    warn "home is on a NETWORK filesystem ($FSTYPE)" \
         "VS Code Remote-SSH needs remote.SSH.lockfilesInTmp=true, or it reports a lockfile failure as an AUTHENTICATION error -- see templates/MARKDOWN.md" ;;
  "") warn "home filesystem" "could not determine type" ;;
  *)  pass "home is on a local filesystem ($FSTYPE) -- Remote-SSH should behave normally" ;;
esac
if command -v quota >/dev/null 2>&1; then
  quota -s 2>/dev/null | sed 's/^/  /' | grep -q . && quota -s 2>/dev/null | sed 's/^/  /' \
    || echo "  quota: none reported for this user"
else
  echo "  quota: no quota command on this host"
fi
if [ -d "$HOME/.vscode-server" ]; then
  echo "  .vscode-server: $(du -sh "$HOME/.vscode-server" 2>/dev/null | cut -f1)" \
       "in $(find "$HOME/.vscode-server" -type f 2>/dev/null | wc -l | tr -d ' ') files"
else
  echo "  .vscode-server: not installed yet"
fi
# System scratch, reported for diagnosis only. The course does not use any of
# these -- it writes to $CRAFT_TMP, which you own. This table exists because a
# term went by before anyone noticed /tmp is not writable for students here.
echo "  system scratch (course does not rely on these):"
FOUND_SCRATCH=0
for d in /tmp /var/tmp /scratch /local /localscratch "/scratch/$USER" "/local/$USER"; do
  [ -d "$d" ] || continue
  t=$(df -PT "$d" 2>/dev/null | tail -1 | awk '{print $2}')
  if [ -w "$d" ]; then w="writable"; FOUND_SCRATCH=1; else w="NOT writable"; fi
  printf '    %-18s %-8s %s\n' "$d" "${t:-?}" "$w"
done
[ "$FOUND_SCRATCH" = 1 ] || echo "    (none writable -- normal here, and nothing in the course needs them)"
printf '    %-18s %-8s %s\n' "$CRAFT_TMP" "$(df -PT "$CRAFT_TMP" 2>/dev/null | tail -1 | awk '{print $2}')" "course scratch, writable"

echo; echo "  ---- paste the block below back to the course staff ----"
echo "  HOME=$HOME  host=$(hostname -f 2>/dev/null || hostname)  homefs=${FSTYPE:-unknown}"
echo "  crafttmp=$CRAFT_TMP"
echo "  scratch=$(for d in /tmp /var/tmp /scratch /local; do [ -d "$d" ] && [ -w "$d" ] && printf '%s(%s) ' "$d" "$(df -PT "$d" 2>/dev/null|tail -1|awk '{print $2}')"; done)"
echo "  ------------------------------------------------------------"

echo; echo "=== summary ==="
[ $RC -eq 0 ] && printf "${GRN}All required checks passed.${NC}\n" \
              || printf "${RED}Something required failed -- see the FAIL lines above.${NC}\n"
echo "Week 8 tools (yosys/z3/sby) are expected to be absent until IT installs them."
exit $RC
