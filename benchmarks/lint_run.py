"""Phase-2 lint benchmark: clean substrate is clean; dirty catches every defect.

Generates the synthetic demo substrate (clean + dirty), runs the generic deck's
implemented scalar rules, and asserts: clean -> 0 violations; dirty -> every manifest
defect parameter produces at least one violation. Writes the result into the Phase-2
section of a JSON summary consumed by the Phase-6 roll-up.

Usage: python -m benchmarks.lint_run
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from pkgtk.cli.check import run_lint
from pkgtk.lint.deck import load_deck
from pkgtk.synth.substrate_gen import layers_yaml, write_clean, write_dirty

ROOT = Path(__file__).resolve().parents[1]
DECK = ROOT / "decks" / "generic-substrate-v0.yaml"


def run() -> dict:
    import json

    deck = load_deck(DECK)
    param_of = {r.id: r.parameter for r in deck.rules}

    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        layers = tdp / "layers.yaml"
        layers.write_text(json.dumps(layers_yaml()), "utf-8")

        clean_gds = tdp / "clean.gds"
        write_clean(clean_gds)
        clean_v, _, _ = run_lint(clean_gds, DECK, layers)

        dirty_gds = tdp / "dirty.gds"
        manifest = write_dirty(dirty_gds, tdp / "manifest.json")
        dirty_v, _, _ = run_lint(dirty_gds, DECK, layers)

    caught_params = {param_of.get(v.rule_id) for v in dirty_v}
    expected_params = {d["parameter"] for d in manifest["defects"]}
    missed = sorted(expected_params - caught_params)

    return {
        "clean_violations": len(clean_v),
        "dirty_violations": len(dirty_v),
        "expected_defects": sorted(expected_params),
        "caught_defects": sorted(p for p in caught_params if p),
        "missed": missed,
        "ok": len(clean_v) == 0 and not missed,
    }


def main() -> int:
    summary = run()
    print(f"clean={summary['clean_violations']} dirty={summary['dirty_violations']} "
          f"missed={summary['missed']}")
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
