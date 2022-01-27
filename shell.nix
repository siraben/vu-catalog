with (import <nixpkgs> {});

let
  py = python3.withPackages (p: [ p.requests ]);
in

mkShell {
  packages = [ py ];
}
