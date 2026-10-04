{
  description = "CRAFT | Verification & Validation of Digital Systems -- reproducible local toolchain for personal machines (NOT university/eustis; there use /opt/course/cocotb-env).";

  inputs = {
    # Pinned to a stable release branch. Commit the generated flake.lock
    # (`nix flake lock`) for a byte-exact, shared toolchain across everyone.
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.05";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; };
      in {
        devShells.default = pkgs.mkShell {
          packages = import ./nix/packages.nix pkgs;
          shellHook = ''
            export SSL_CERT_FILE=${pkgs.cacert}/etc/ssl/certs/ca-bundle.crt
            export NIX_SSL_CERT_FILE=$SSL_CERT_FILE
            export CRAFT_PY=${pkgs.python311}/bin/python3.11
            source ${./nix/shellhook.sh}
          '';
        };
      });
}
