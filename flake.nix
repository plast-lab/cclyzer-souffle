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

    # Everything the build needs. LLVM is pinned to 22, the version the
    # Docker image uses; Python is nixpkgs' default (any Python 3 that
    # Boost.Python is built for).
    buildDeps = pkgs: let
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
    in [
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
  in {
    devShells = forAllSystems (pkgs: {
      default = pkgs.mkShell {packages = buildDeps pkgs;};
    });

    # `nix flake check`: build the fact generator from a clean checkout and
    # check its facts for tests/ against tests/facts.sha256.
    checks = forAllSystems (pkgs: {
      default = pkgs.stdenv.mkDerivation {
        name = "cclyzer-souffle-check";
        src = self;
        nativeBuildInputs = buildDeps pkgs;
        dontConfigure = true;
        buildPhase = "make -j$NIX_BUILD_CORES fact-generator";
        doCheck = true;
        checkPhase = "make test-facts";
        installPhase = "touch $out";
      };
    });
  };
}
