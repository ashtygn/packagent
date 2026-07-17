"""Synthetic 2-metal demo substrate generator (gdstk).

Produces a *clean* substrate (zero geometry violations under the generic deck) and a
*dirty* variant embedding exactly one violation per implemented check, with a manifest
so the lint benchmark can assert catch-by-parameter. gdstk is used only to generate
geometry; checks are pure klayout.

Layers: signal (1,0), plane (2,0), outline (10,0), degas (3,0). Units µm.
"""

from __future__ import annotations

import json
from pathlib import Path

import gdstk

LAYERS = {"signal": (1, 0), "plane": (2, 0), "outline": (10, 0), "degas": (3, 0)}
_OUTLINE = (0, 0, 5000, 5000)


def _rect(cell, layer_dt, box):
    x0, y0, x1, y1 = box
    cell.add(gdstk.rectangle((x0, y0), (x1, y1),
                             layer=layer_dt[0], datatype=layer_dt[1]))


def _base(cell):
    # Outline + a plane inset well away from the edge (> copper_to_edge margin).
    _rect(cell, LAYERS["outline"], _OUTLINE)
    _rect(cell, LAYERS["plane"], (400, 400, 4600, 4600))
    # A bus of wide, well-spaced signal traces, all clear of the board edge.
    for i in range(8):
        x = 1000 + i * 200  # 100-wide traces on a 200 pitch -> 100 space (>=25)
        _rect(cell, LAYERS["signal"], (x, 1000, x + 100, 4000))


def write_clean(path: str | Path) -> None:
    lib = gdstk.Library(unit=1e-6, precision=1e-9)
    cell = lib.new_cell("SUBSTRATE")
    _base(cell)
    lib.write_gds(str(path))


def write_dirty(path: str | Path, manifest_path: str | Path) -> dict:
    lib = gdstk.Library(unit=1e-6, precision=1e-9)
    cell = lib.new_cell("SUBSTRATE")
    _base(cell)
    defects = []

    # 1) trace_width_min: a 12-µm-wide trace (< 25).
    _rect(cell, LAYERS["signal"], (2700, 1000, 2712, 4000))
    defects.append({"parameter": "trace_width_min"})

    # 2) spacing_min: two traces 10 µm apart (< 25).
    _rect(cell, LAYERS["signal"], (3200, 1000, 3260, 4000))
    _rect(cell, LAYERS["signal"], (3270, 1000, 3330, 4000))
    defects.append({"parameter": "spacing_min"})

    # 3) degas_to_trace_clearance_min: a degas void 30 µm from a trace (< 50).
    _rect(cell, LAYERS["signal"], (3600, 2000, 3660, 2400))
    _rect(cell, LAYERS["degas"], (3690, 2000, 3800, 2400))
    defects.append({"parameter": "degas_to_trace_clearance_min"})

    # 4) copper_to_edge_min: signal copper 50 µm from the board edge (< 200).
    _rect(cell, LAYERS["signal"], (50, 2000, 300, 2200))
    defects.append({"parameter": "copper_to_edge_min"})

    lib.write_gds(str(path))
    manifest = {"defects": defects, "layers": {k: list(v) for k, v in LAYERS.items()}}
    Path(manifest_path).write_text(json.dumps(manifest, indent=2) + "\n", "utf-8")
    return manifest


def layers_yaml() -> dict:
    return {k: list(v) for k, v in LAYERS.items()}
