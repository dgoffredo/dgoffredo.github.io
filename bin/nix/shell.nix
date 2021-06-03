{ pkgs ? import <nixpkgs> {} }:
  pkgs.mkShell {
    nativeBuildInputs = [ 
        pkgs.buildPackages.cacert
        pkgs.buildPackages.coreutils
        pkgs.buildPackages.findutils
        pkgs.buildPackages.gawk
        pkgs.buildPackages.gnumake
        pkgs.buildPackages.gnused
        pkgs.buildPackages.graphviz
        pkgs.buildPackages.imagemagick
        pkgs.buildPackages.jq
        pkgs.buildPackages.libwebp
        pkgs.buildPackages.nodejs
        pkgs.buildPackages.python37
        pkgs.buildPackages.wget
    ];
}
