{
  description = "cclyzer-souffle development environment (LLVM bitcode analysis via Soufflé Datalog)";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs = {
    self,
    nixpkgs,
  }: let
    systems = ["x86_64-linux" "aarch64-linux"];
    forAllSystems = f:
      nixpkgs.lib.genAttrs systems (system: f (import nixpkgs {inherit system;}));
  in {
    devShells = forAllSystems (pkgs: let
      llvm = pkgs.llvmPackages_22;
      python = pkgs.python3;

      # Boost.Python for the factgen.so / astexport.so bindings
      boostPython = pkgs.boost.override {
        enablePython = true;
        inherit python;
      };

      # Soufflé built with a 64-bit domain. The default 32-bit build fails to load
      # facts containing LLVM's ~0U sentinel (4294967295)
      souffle64 = pkgs.souffle.overrideAttrs (old: {
        cmakeFlags = old.cmakeFlags ++ ["-DSOUFFLE_DOMAIN_64BIT=ON"];
      });
    in {
      default = pkgs.mkShell {
        packages = [
          pkgs.m4
          souffle64

          # Nix-wrapped clang so it finds libc headers. Comes before libclang
          # which also ships unwrapped `clang`
          llvm.clang
          llvm.llvm.dev
          llvm.libclang
          llvm.libclang.dev

          boostPython
          python
        ];
      };
    });
  };
}
