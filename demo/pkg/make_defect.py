"""Beat 2b — inject ONE seeded defect into PHOTON-X1 via the benchmark REGISTRY.

Mutation: `multi_assignment` (benchmarks/mutations.py) — the first signal ball
gets an extra strap to net_GND, i.e. a classic "someone repurposed a signal ball
as ground" edit. Golden-verified (bench01) to produce exactly one violation:
bijection.multi_assignment at that ball.

Writes graph_photonx1_defect.json. Deterministic (target chosen by fixed scan
order over the seeded graph).

Usage: python make_defect.py [outdir]
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from benchmarks.mutations import REGISTRY  # noqa: E402, I001
from photonx1 import build  # noqa: E402

OUTDIR = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent
MUTATION = "multi_assignment"


def main() -> int:
    design = build()
    graph, _config, expected = REGISTRY[MUTATION](design)
    graph.rev = "A-defect1"
    out = OUTDIR / "graph_photonx1_defect.json"
    out.write_text(graph.model_dump_json(indent=2, exclude_none=True),
                   encoding="utf-8")
    print(f"seeded defect : {MUTATION} (benchmarks.mutations REGISTRY)")
    print(f"planted at    : ball {expected.get('node_id')} "
          f"(signal ball also strapped to GND)")
    print(f"expected catch: {expected['rule_id']} @ {expected.get('node_id')}")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
