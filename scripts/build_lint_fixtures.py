"""Build the Phase-2 golden lint fixtures with gdstk (generation only).

For each implemented check, draws a tiny GDS containing exactly one planted violation,
writes layers.yaml + case.yaml, runs the engine, asserts the physically hand-computed
measured/required, and freezes expected.json. gdstk is used ONLY here to generate
geometry; the checks themselves are pure klayout (src/pkgtk/lint/engine.py).

Usage: python scripts/build_lint_fixtures.py
"""

from __future__ import annotations

import json
from pathlib import Path

import gdstk
import yaml

from pkgtk.lint.engine import load_layout, run_check

REPO = Path(__file__).resolve().parents[1]
LINT = REPO / "fixtures" / "golden" / "lint"
LAYERS = {"signal": [1, 0], "plane": [2, 0], "outline": [10, 0], "degas": [3, 0]}


def _write_gds(cell_shapes, path: Path):
    lib = gdstk.Library(unit=1e-6, precision=1e-9)
    cell = lib.new_cell("TOP")
    for layer, dt, (x0, y0, x1, y1) in cell_shapes:
        cell.add(gdstk.rectangle((x0, y0), (x1, y1), layer=layer, datatype=dt))
    lib.write_gds(str(path))


def _params(rule_id, parameter, value_um, layer_class="signal"):
    return {"rule_id": rule_id, "value_um": value_um, "layer_class": layer_class}


CASES = {
    # name: (shapes, parameter, value_um, hand_measured)
    "width_min": ([(1, 0, (0, 0, 100, 12))], "trace_width_min", 25.0, 12.0),
    "spacing_min": ([(1, 0, (0, 0, 40, 40)), (1, 0, (50, 0, 90, 40))],
                    "spacing_min", 25.0, 10.0),
    "degas_clearance": ([(1, 0, (0, 0, 40, 40)), (3, 0, (70, 0, 110, 40))],
                        "degas_to_trace_clearance_min", 50.0, 30.0),
    "copper_to_edge": ([(10, 0, (0, 0, 1000, 1000)), (1, 0, (10, 400, 60, 600))],
                       "copper_to_edge_min", 200.0, None),
    "clean": ([(10, 0, (0, 0, 1000, 1000)), (1, 0, (400, 400, 460, 600))],
              "trace_width_min", 25.0, None),
}


def main() -> int:
    for name, (shapes, parameter, value_um, hand_measured) in CASES.items():
        d = LINT / name
        d.mkdir(parents=True, exist_ok=True)
        gds = d / "in.gds"
        _write_gds(shapes, gds)
        (d / "layers.yaml").write_text(yaml.safe_dump(LAYERS, sort_keys=True), "utf-8")
        (d / "case.yaml").write_text(
            yaml.safe_dump({"parameter": parameter, "value_um": value_um,
                            "layer_class": "signal"}, sort_keys=True), "utf-8")
        layout = load_layout(gds)
        params = _params(f"TEST.{name}", parameter, value_um)
        vs = run_check(layout, LAYERS, parameter, params)
        dumped = [v.model_dump(mode="json", exclude_none=True) for v in vs]
        if name == "clean":
            assert dumped == [], f"clean fixture {name} fired {len(dumped)}"
        else:
            assert len(dumped) == 1, f"{name}: expected 1 violation, got {len(dumped)}"
            if hand_measured is not None:
                got = dumped[0]["measured"]["value"]
                assert got == hand_measured, f"{name}: {got} != {hand_measured}"
        (d / "expected.json").write_text(json.dumps(dumped, indent=2) + "\n", "utf-8")
        print(f"{name:16} violations={len(dumped)} measured_ok")
    print("all lint fixtures built")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
