"""Generate the synthetic demo substrates (clean + dirty) into this directory.

Canonical invocation mirrors benchmarks/lint_run.py: pkgtk's own generator
(src/pkgtk/synth/substrate_gen.py) — 100% synthetic geometry, zero design data,
fully deterministic (no randomness in the generator).

Usage: python gen_substrates.py [outdir]   (default: script's own directory)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from pkgtk.synth.substrate_gen import layers_yaml, write_clean, write_dirty


def main() -> int:
    outdir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent
    outdir.mkdir(parents=True, exist_ok=True)

    layers = outdir / "layers.yaml"
    layers.write_text(json.dumps(layers_yaml()), "utf-8")

    write_clean(outdir / "clean.gds")
    manifest = write_dirty(outdir / "dirty.gds", outdir / "manifest.json")

    print(f"wrote {outdir / 'clean.gds'}")
    print(f"wrote {outdir / 'dirty.gds'}")
    print(f"wrote {layers}")
    print(f"wrote {outdir / 'manifest.json'} "
          f"({len(manifest['defects'])} planted defects: "
          f"{[d['parameter'] for d in manifest['defects']]})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
