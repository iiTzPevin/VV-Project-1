# Non-flakes fallback:  run `nix-shell` in the repo root.
# Pins nixpkgs to the same release branch the flake uses (nixos-24.05).
#
# The flake (flake.nix + a committed flake.lock) is the fully reproducible path;
# this file exists for machines that do not have flakes enabled. The branch
# tarball below tracks security patches, so for a shared, byte-exact toolchain
# prefer the flake and commit its flake.lock.
{ pkgs ? import (fetchTarball {
    url = "https://github.com/NixOS/nixpkgs/archive/nixos-24.05.tar.gz";
  }) { } }:

pkgs.mkShell {
  packages = import ./nix/packages.nix pkgs;
  shellHook = ''
    export SSL_CERT_FILE=${pkgs.cacert}/etc/ssl/certs/ca-bundle.crt
    export NIX_SSL_CERT_FILE=$SSL_CERT_FILE
    export CRAFT_PY=${pkgs.python311}/bin/python3.11
    source ${./nix/shellhook.sh}
  '';
}
