# CRAFT V&V -- Nix devshell bootstrap (sourced by flake.nix / shell.nix).
# Builds a repo-local .venv from code/requirements.txt so the Python stack
# (cocotb 1.9.2, pyuvm, pyvsc, ...) matches the eustis course env exactly.
# This file is sourced into your interactive shell; it does not set shell flags.

_craft_find_root() {
  local d="${PWD}" r
  if r="$(git rev-parse --show-toplevel 2>/dev/null)"; then printf '%s\n' "$r"; return; fi
  while [ "$d" != "/" ]; do
    [ -f "$d/code/requirements.txt" ] && { printf '%s\n' "$d"; return; }
    d="$(dirname "$d")"
  done
  printf '%s\n' "$PWD"
}

CRAFT_ROOT="$(_craft_find_root)"
CRAFT_VENV="$CRAFT_ROOT/.venv"
CRAFT_REQ="$CRAFT_ROOT/code/requirements.txt"
CRAFT_PY="${CRAFT_PY:-python3}"
CRAFT_STAMP="$CRAFT_VENV/.craft-stamp"

# (Re)create the venv when missing, or when its interpreter no longer runs -- a
# Nix garbage-collection can invalidate the store python the venv was cloned from.
if [ ! -x "$CRAFT_VENV/bin/python" ] || ! "$CRAFT_VENV/bin/python" -c '' 2>/dev/null; then
  echo "[craft] creating virtualenv at .venv ..."
  rm -rf "$CRAFT_VENV"
  "$CRAFT_PY" -m venv "$CRAFT_VENV"
fi
# shellcheck disable=SC1091
. "$CRAFT_VENV/bin/activate"

# Install / refresh deps only when requirements.txt (or the interpreter) changes.
if [ -f "$CRAFT_REQ" ]; then
  _craft_want="$( (cat "$CRAFT_REQ"; "$CRAFT_PY" --version) | sha256sum | cut -d' ' -f1 )"
  _craft_have="$(cat "$CRAFT_STAMP" 2>/dev/null || true)"
  if [ "$_craft_want" != "$_craft_have" ]; then
    echo "[craft] installing Python deps (cocotb 1.9.2 pinned) ..."
    python -m pip -q install --upgrade pip >/dev/null 2>&1
    if python -m pip -q install -r "$CRAFT_REQ"; then
      printf '%s\n' "$_craft_want" > "$CRAFT_STAMP"
    else
      echo "[craft] WARNING: pip install failed -- check your network, then re-enter the shell." >&2
    fi
  fi
fi

export PYTHONPATH="$CRAFT_ROOT/code/lib${PYTHONPATH:+:$PYTHONPATH}"
export COCOTB_ANSI_OUTPUT=1

cat <<'BANNER'

  CRAFT | V&V devshell ready.
    verify:    bash code/setup/verify_env.sh
    run a tb:  cd code && just test alu          (or: make -C tb/alu SIM=icarus)
    score:     cd code && just mutate alu

  NOTE: On UCF/eustis machines do NOT use Nix. Instead run:
        source /opt/course/cocotb-env/bin/activate      (see INSTALL.md)
BANNER

unset -f _craft_find_root
unset _craft_want _craft_have
