#!/usr/bin/env bash
# CRAFT V&V -- put `just` in your own account on eustis.
#
# eustis has no `just`, and you cannot install system packages there. You do not
# need to. `just` is a single file: this drops it in ~/.local/bin, which you own,
# and makes sure your shell can still find it after you log out and back in.
#
#   bash setup/install_just.sh
#
# Safe to run twice. It will not download a second copy and it will not add the
# PATH line to your shell config twice.
#
# You never have to run this. Every recipe in the justfile is one make or python
# command you can type by hand -- `just` only saves you the typing.
set -euo pipefail

GREEN='\033[0;32m'; RED='\033[0;31m'; YEL='\033[0;33m'; NC='\033[0m'
ok(){   printf "${GREEN}OK${NC}   %s\n" "$1"; }
note(){ printf "${YEL}note${NC} %s\n" "$1"; }
die(){  printf "${RED}FAIL${NC} %s\n" "$1" >&2; exit 1; }

BIN="$HOME/.local/bin"
MARK="# >>> CRAFT V&V: just on PATH >>>"
END="# <<< CRAFT V&V: just on PATH <<<"
# Written into your shell config with $HOME left un-expanded on purpose, so the
# line keeps working if your home directory ever moves.
# shellcheck disable=SC2016
LINE='export PATH="$HOME/.local/bin:$PATH"'

# Append the PATH block to a shell config, but only once. The marker comment is
# how we recognise our own work on a re-run -- grep -F so the >>> is literal.
add_block(){
  local rc="$1"
  if [ -f "$rc" ] && grep -qF "$MARK" "$rc"; then
    return 1                      # already ours, nothing to do
  fi
  printf '\n%s\n%s\n%s\n' "$MARK" "$LINE" "$END" >> "$rc"
  return 0
}

echo "=== CRAFT V&V: installing just ==="

# ---------------------------------------------------------------- 1. install
if [ -x "$BIN/just" ]; then
  ok "already installed: $BIN/just ($("$BIN/just" --version 2>&1 | head -1))"
elif command -v just >/dev/null 2>&1; then
  # Someone else's copy is already on the PATH -- a module, or a system install.
  # Leave it alone; a second copy would only be confusing.
  ok "just is already available: $(command -v just) ($(just --version 2>&1 | head -1))"
  echo ""
  echo "Nothing to do. Try: just --list"
  exit 0
else
  command -v curl >/dev/null 2>&1 \
    || die "curl not found. Download just by hand from https://just.systems and put it in $BIN"
  mkdir -p "$BIN"
  echo "Downloading into $BIN ..."
  # --proto '=https' and --tlsv1.2 refuse to be redirected onto a weaker
  # connection. Note the flag is --tlsv1.2, with no "l" after "tls".
  curl --proto '=https' --tlsv1.2 -sSf https://just.systems/install.sh \
    | bash -s -- --to "$BIN" \
    || die "download failed. Off campus this usually means the VPN is not connected."
  [ -x "$BIN/just" ] || die "the installer finished but $BIN/just is not there"
  ok "installed $("$BIN/just" --version 2>&1 | head -1)"
fi

# ------------------------------------------------------- 2. make it findable
# Installing the file is the easy half. If ~/.local/bin is not on your PATH the
# shell reports "just: command not found", which reads like the install failed
# when in fact the binary is sitting right there.
if case ":${PATH}:" in *":$BIN:"*) true;; *) false;; esac; then
  ok "$BIN is already on your PATH"
else
  if add_block "$HOME/.bashrc"; then
    ok "added $BIN to your PATH in ~/.bashrc"
  else
    note "your ~/.bashrc already carries the CRAFT PATH block; this shell has not read it yet"
  fi

  # An ssh login shell does NOT read ~/.bashrc. It reads the first of
  # ~/.bash_profile, ~/.bash_login, ~/.profile -- and most distributions ship one
  # that sources ~/.bashrc for you. If this account has none that does, the line
  # above would never run at login and just would "disappear" every session.
  login_rc=""
  for f in "$HOME/.bash_profile" "$HOME/.bash_login" "$HOME/.profile"; do
    [ -f "$f" ] && { login_rc="$f"; break; }
  done
  if [ -z "$login_rc" ]; then
    add_block "$HOME/.bash_profile" >/dev/null || true
    ok "created ~/.bash_profile so login shells set the PATH too"
  elif ! grep -Eq '^[^#]*(\.|source)[[:space:]]+.*bashrc' "$login_rc"; then
    if add_block "$login_rc"; then
      ok "$(basename "$login_rc") does not read ~/.bashrc, so the PATH line went there as well"
    fi
  fi

  export PATH="$BIN:$PATH"
  note "this window is set for now; new logins pick it up on their own"
  note "to fix another window that is already open:  source ~/.bashrc"
fi

# ------------------------------------------------------------- 3. prove it
hash -r 2>/dev/null || true
command -v just >/dev/null 2>&1 || die "just is installed but not on the PATH. Run: source ~/.bashrc"
ok "just --version -> $(just --version 2>&1 | head -1)"

echo ""
echo "Next: cd to the course code and run  just --list  to see every recipe."
