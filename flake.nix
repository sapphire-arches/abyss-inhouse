{
  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs";
    flake-utils = {
      url = "github:numtide/flake-utils";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    fenix = {
      url = "github:nix-community/fenix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = {self, nixpkgs, flake-utils, fenix}: (
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs {
          inherit system;
          overlays = [
            fenix.overlay
          ];
          config = {
            allowUnfreePredicate = pkg: builtins.elem (pkg.pname) [
              "ngrok"
              "awscli"
            ];
          };
        };
        python-pkg = pkgs.python310.withPackages (pythonPackages: with pythonPackages; [
          # Python tooling
          isort
          mypy
          yapf

          # Postgresql connector
          pgcli
        ]);
      in
      {
        devShell = pkgs.mkShell {
          name = "abyss-inhouse-devel-shell";

          buildInputs = with pkgs; [
            # for formatting Nix expressions
            nixpkgs-fmt

            # Pulumi
            python-pkg
            pulumi-bin
            crd2pulumi
            awscli2
            kubernetes-helm

            # Bot development (js)
            nodejs
            ngrok

            # Rust development
            (fenix.packages.${system}.stable.withComponents [
              "cargo"
              "rustc"
              "rust-src"
              "rustfmt"
            ])
            fenix.packages.${system}.rust-analyzer
          ];

          shellHook = ''
            # To pick up the specific version of Python we're using
            PYTHONPATH=${python-pkg}/${python-pkg.sitePackages}

            # make rust-analyzer work
            export RUST_SRC_PATH=${fenix.packages.${system}.stable.rust-src}/lib/rustlib/src/rust/library
          '';
        };
      }
    )
  );
}
