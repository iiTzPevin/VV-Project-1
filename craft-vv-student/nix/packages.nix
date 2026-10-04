# Shared toolchain package list for both flake.nix and shell.nix.
# Everything the CRAFT V&V code base needs on a PERSONAL machine.
# University machines use /opt/course/cocotb-env instead -- see INSTALL.md.
#
# The Python stack (cocotb 1.9.2, pyuvm, pyvsc, ...) is NOT taken from nixpkgs;
# it is pip-installed into a repo-local .venv from code/requirements.txt by the
# shellHook, so it is byte-identical to the eustis course env. Nix pins only the
# system EDA tools + interpreter so every personal machine matches.
pkgs:
with pkgs; [
  # --- EDA / simulation ---
  verilator        # RTL simulation (Weeks 3-10)
  iverilog         # Icarus Verilog -- fast recompiles for the mutation harness
  yosys            # synthesis / formal front end (Week 8)
  symbiyosys       # the `sby` formal driver (Week 8)
  z3               # SMT solver behind the proofs (Week 8)
  gtkwave          # waveform viewer (optional, handy for debugging)
  # --- build / language / cli ---
  python311        # interpreter the .venv is cloned from
  gnumake
  gcc
  git
  just             # optional task runner (code/justfile)
  cacert           # TLS roots so pip can fetch inside the pure shell
]

# ----------------------------------------------------------------------------
# ADVANCED (optional): pin Verilator to the exact eustis patch (5.020).
# nixos-24.05 ships a 5.0xx Verilator that runs this course correctly, and the
# GRADED runner uses the canonical eustis/CI toolchain regardless, so most users
# do not need this. If you want a byte-exact local Verilator, apply an overlay
# in flake.nix / shell.nix like the following and fill in the real hashes with
# `nix-prefetch-url --unpack https://github.com/verilator/verilator/archive/refs/tags/v5.020.tar.gz`:
#
#   overlays = [ (final: prev: {
#     verilator = prev.verilator.overrideAttrs (old: rec {
#       version = "5.020";
#       src = final.fetchFromGitHub {
#         owner = "verilator"; repo = "verilator"; rev = "v${version}";
#         hash = "sha256-AAAA...replace-me...";   # <- nix-prefetch to get this
#       };
#     });
#   }) ];
# ----------------------------------------------------------------------------
