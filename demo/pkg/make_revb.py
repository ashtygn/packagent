"""Beat 4a â€” build PHOTON-X1 rev B: an ECO that drops one leg of a diff pair.

Mutation: `diffpair_missing_partner` (benchmarks/mutations.py) â€” removes the _N
net, its ball, and its die pad for the first diff pair in scan order. Expected
`pkgtk diff` change classes: exactly one `removed` (the _N net) and one
`pair_broken` (its _P partner).

Writes graph_photonx1_revB.json. Deterministic.

Usage: python make_revb.py [outdir]
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from benchmarks.mutations import REGISTRY  # noqa: E402, I001
from photonx1 import build  # noqa: E402

OUTDIR = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent
MUTATION = "diffpair_missing_partner"


def main() -> int:
    design = build()
    graph, _config, expected = REGISTRY[MUTATION](design)
    graph.rev = "B"
    out = OUTDIR / "graph_photonx1_revB.json"
    out.write_text(graph.model_dump_json(indent=2, exclude_none=True),
                   encoding="utf-8")
    pnet = expected.get("net", "")
    print(f"ECO mutation  : {MUTATION} (benchmarks.mutations REGISTRY)")
    print(f"dropped net   : {pnet[:-2]}_N (net + ball + die pad removed)")
    print(f"expected diff : removed x1 ({pnet[:-2]}_N), pair_broken x1 ({pnet})")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
