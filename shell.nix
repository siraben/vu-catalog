with (import <nixpkgs> {});

let
  py = python3.withPackages (p: [ p.requests p.aiohttp ]);
in

mkShell {
  packages = [ py ];
}
