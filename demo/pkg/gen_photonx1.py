"""Beat 1 — generate PHOTON-X1, a 2025-ball synthetic package, in about a second.

Writes graph_photonx1.json (ConnectivityGraph) and runconfig_photonx1.json
(matching RunConfig for `pkgtk verify --config`). Deterministic / byte-stable.

Usage: python gen_photonx1.py [outdir]
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

from photonx1 import build, story

OUTDIR = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent


def main() -> int:
    t0 = time.perf_counter()
    design = build()
    gen_s = time.perf_counter() - t0

    graph_path = OUTDIR / "graph_photonx1.json"
    config_path = OUTDIR / "runconfig_photonx1.json"
    graph_path.write_text(
        design.graph.model_dump_json(indent=2, exclude_none=True), encoding="utf-8")
    config_path.write_text(
        design.config.model_dump_json(indent=2), encoding="utf-8")

    print("PHOTON-X1 generated (100% synthetic, pkgtk.synth.ballmap_gen)")
    for line in story(design):
        print("  " + line)
    print(f"  generated in: {gen_s * 1000:.0f} ms")
    print(f"  wrote {graph_path}")
    print(f"  wrote {config_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
