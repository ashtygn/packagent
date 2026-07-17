"""`pkgtk check design.gds --deck deck.yaml --layers layers.yaml`.

Runs every implemented, scalar-valued geometry rule in the deck against the layout,
writes violations.json + out.lyrdb (clickable markers), and exits nonzero iff any
hard-severity violation is found. Piecewise/expression-valued rules need a design-
variable binding not available at the CLI boundary in v0 and are skipped with a note
(honest coverage; see docs/PHASE-NOTES.md).
"""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from pkgtk.lint.coverage import classify
from pkgtk.lint.deck import load_deck
from pkgtk.lint.engine import IMPLEMENTED, load_layout, run_check
from pkgtk.lint.lyrdb import write_lyrdb
from pkgtk.schemas.rule_ir import RuleIR

_UNIT_TO_UM = {"um": 1.0, "mm": 1000.0, "nm": 0.001}


def _scalar_um(rule: RuleIR) -> float | None:
    val = rule.value
    if val.kind != "scalar":
        return None
    return val.number * _UNIT_TO_UM.get(val.units, 1.0)


def run_lint(gds, deck_path, layers_path):
    deck = load_deck(deck_path)
    layers = {k: tuple(v)
              for k, v in yaml.safe_load(Path(layers_path).read_text("utf-8")).items()}
    layout = load_layout(gds)
    violations = []
    skipped = []
    for rule in deck.rules:
        if rule.parameter not in IMPLEMENTED:
            continue
        value_um = _scalar_um(rule)
        if value_um is None:
            skipped.append(rule.id)
            continue
        params = {
            "rule_id": rule.id,
            "value_um": value_um,
            "layer_class": (rule.scope.layer_class if rule.scope else None) or "signal",
        }
        violations.extend(run_check(layout, layers, rule.parameter, params))
    return violations, classify(deck), skipped


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(prog="pkgtk check")
    parser.add_argument("gds")
    parser.add_argument("--deck", required=True)
    parser.add_argument("--layers", required=True)
    parser.add_argument("--out-json", default="violations.json")
    parser.add_argument("--out-lyrdb", default="out.lyrdb")
    args = parser.parse_args(argv)

    violations, coverage, skipped = run_lint(args.gds, args.deck, args.layers)
    dumped = [v.model_dump(mode="json", exclude_none=True) for v in violations]
    Path(args.out_json).write_text(
        json.dumps(dumped, indent=2, sort_keys=True), "utf-8")
    write_lyrdb(violations, args.out_lyrdb)

    hard = sum(1 for v in violations if v.severity == "hard")
    print(f"{len(violations)} violation(s) ({hard} hard); wrote {args.out_json} "
          f"+ {args.out_lyrdb}")
    if skipped:
        print(f"skipped (non-scalar, needs variable binding): {skipped}")
    return 1 if hard else 0


if __name__ == "__main__":
    raise SystemExit(main())
