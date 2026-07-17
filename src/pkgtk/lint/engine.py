"""KLayout-based geometry check engine. See docs/lint-spec.md (normative).

Pure functions ``(layout, layer_map, params) -> list[Violation]``. Internal math is in
integer DBU; locations are emitted in µm. gdstk is never imported here (checks only).
"""

from __future__ import annotations

from pathlib import Path

import klayout.db as kdb

from pkgtk.schemas.violation import (
    Extent,
    MeasurementValue,
    PhysicalLocation,
    Violation,
)

CHECK_VERSION = "0.1.0"

# Parameters this engine implements (keep in sync with coverage.IMPLEMENTED_PARAMETERS).
IMPLEMENTED = {
    "trace_width_min",
    "spacing_min",
    "degas_to_trace_clearance_min",
    "copper_to_edge_min",
}


def load_layout(path: str | Path) -> kdb.Layout:
    layout = kdb.Layout()
    layout.read(str(path))
    return layout


def _region(layout: kdb.Layout, layer_map: dict, cls: str) -> kdb.Region:
    layer, datatype = layer_map[cls]
    idx = layout.layer(layer, datatype)
    return kdb.Region(layout.top_cell().begin_shapes_rec(idx))


def _um(v: int, dbu: float) -> float:
    return round(v * dbu, 3)


def _edge_pair_violations(ep, dbu, rule_id, layer, required_um, severity="hard"):
    out = []
    for pair in ep.each():
        e1, e2 = pair.first, pair.second
        bb = pair.bbox()
        cx = _um((bb.left + bb.right) // 2, dbu)
        cy = _um((bb.bottom + bb.top) // 2, dbu)
        d = min(e2.distance_abs(kdb.Point(e1.x1, e1.y1)),
                e2.distance_abs(kdb.Point(e1.x2, e1.y2)))
        measured = _um(int(round(d)), dbu)
        out.append(Violation(
            rule_id=rule_id, severity=severity,
            location=PhysicalLocation(
                kind="physical", layer=layer, x=cx, y=cy,
                extent=Extent(w=_um(bb.width(), dbu), h=_um(bb.height(), dbu)),
            ),
            measured=MeasurementValue(value=measured, units="um"),
            required=MeasurementValue(value=required_um, units="um"),
            delta=round(measured - required_um, 3),
            check_version=CHECK_VERSION,
        ))
    return out


def check_trace_width_min(layout, layer_map, params) -> list[Violation]:
    dbu = layout.dbu
    cls = params.get("layer_class", "signal")
    w_min = params["value_um"]
    reg = _region(layout, layer_map, cls)
    ep = reg.width_check(int(round(w_min / dbu)))
    return _edge_pair_violations(ep, dbu, params["rule_id"], cls, w_min)


def check_spacing_min(layout, layer_map, params) -> list[Violation]:
    dbu = layout.dbu
    cls = params.get("layer_class", "signal")
    s_min = params["value_um"]
    reg = _region(layout, layer_map, cls)
    ep = reg.space_check(int(round(s_min / dbu)))
    return _edge_pair_violations(ep, dbu, params["rule_id"], cls, s_min)


def check_degas_clearance_min(layout, layer_map, params) -> list[Violation]:
    dbu = layout.dbu
    c_min = params["value_um"]
    traces = _region(layout, layer_map, params.get("layer_class", "signal"))
    degas = _region(layout, layer_map, "degas")
    ep = traces.separation_check(degas, int(round(c_min / dbu)))
    return _edge_pair_violations(ep, dbu, params["rule_id"], "degas", c_min)


def check_copper_to_edge_min(layout, layer_map, params) -> list[Violation]:
    dbu = layout.dbu
    margin = params["value_um"]
    margin_dbu = int(round(margin / dbu))
    outline = _region(layout, layer_map, "outline")
    copper = kdb.Region()
    for cls in ("signal", "plane"):
        if cls in layer_map:
            copper += _region(layout, layer_map, cls)
    keepout = outline - outline.sized(-margin_dbu)
    bad = (copper & keepout).merged()
    out = []
    for poly in bad.each():
        bb = poly.bbox()
        out.append(Violation(
            rule_id=params["rule_id"], severity="hard",
            location=PhysicalLocation(
                kind="physical", layer="outline",
                x=_um((bb.left + bb.right) // 2, dbu),
                y=_um((bb.bottom + bb.top) // 2, dbu),
                extent=Extent(w=_um(bb.width(), dbu), h=_um(bb.height(), dbu)),
            ),
            required=MeasurementValue(value=margin, units="um"),
            check_version=CHECK_VERSION,
        ))
    out.sort(key=lambda v: (v.location.x, v.location.y))
    return out


DISPATCH = {
    "trace_width_min": check_trace_width_min,
    "spacing_min": check_spacing_min,
    "degas_to_trace_clearance_min": check_degas_clearance_min,
    "copper_to_edge_min": check_copper_to_edge_min,
}


def run_check(layout, layer_map, parameter, params) -> list[Violation]:
    fn = DISPATCH.get(parameter)
    if fn is None:
        return []
    vs = fn(layout, layer_map, params)
    vs.sort(key=lambda v: (v.location.x, v.location.y))
    return vs
