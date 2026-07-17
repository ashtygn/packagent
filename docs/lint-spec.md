# lint-spec.md — package-lint geometry semantics (Phase 2, normative)

The geometry engine implements exactly these check semantics on `klayout.db` Regions.
Work in integer database units (DBU): read `layout.dbu` (µm/DBU), convert µm→DBU once at
the boundary, keep everything internal integer, emit locations back in µm. `gdstk` is used
only to *generate* synthetic geometry (fixtures); never for checks.

Each check is a pure function `(layout, layer_map, params) -> list[Violation]`.
`layer_map` maps a layer-class name (e.g. `signal`, `plane`, `outline`) to a GDS
`(layer, datatype)` pair. Violations use `violation.schema.json`, `location.kind =
physical`, coordinates in µm, `check_version = "0.1.0"`.

## Implemented checks (v0)

### trace_width_min  (parameter `trace_width_min`)
`Region.width_check(w_min_dbu)` on the routing layer for the given layer class. Each
returned edge pair is one violation. `measured` = the offending width in µm (edge-pair
spacing), `required` = `w_min`, location = the edge pair's bounding-box center.

### spacing_min  (parameter `spacing_min`)
`Region.space_check(s_min_dbu)` within the layer. Each edge pair is one violation.
`measured` = the offending spacing in µm, `required` = `s_min`.

### degas_to_trace_clearance_min  (parameter `degas_to_trace_clearance_min`)
Degas voids = holes in the plane layer, derived as `plane.hulls() - plane` (the filled
outline minus the copper). Violation region = `traces & degas_voids.sized(c_dbu)`; each
resulting polygon is one violation located at its bbox center. `measured` = actual
clearance (approximated by `c - overlap_extent`), `required` = `c`.

### copper_to_edge_min  (parameter `copper_to_edge_min`)
Board keep-out = `outline - outline.sized(-margin_dbu)` (a ring inside the outline edge).
Violation region = `all_copper & keepout`; each polygon is one violation at its bbox
center. `measured` = 0-ish (copper intrudes into the margin), `required` = `margin`.

## Deferred (surface as `coverage: unimplemented`, never silent pass)
`degas_coverage_window`, `copper_balance_window` (windowed density), `annular_ring_min`
(needs padstack table), `ball_grid` (pad-diameter/pitch/depop — reuses Phase-1 depop on
extracted centroids). Net-aware spacing is explicitly deferred (v0 does geometric
spacing only). These are honest coverage gaps, reported by `pkgtk.lint.coverage`.

## Determinism
Within each check, sort violations by `(round(x,3), round(y,3))` so output is stable.
Locations within 1 DBU of the hand-measured golden value are considered correct.
