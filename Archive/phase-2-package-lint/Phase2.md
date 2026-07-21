# Phase 2 — package-lint Geometry Checker (22 hrs)

## Goal
The open oracle that doesn't exist anywhere: a substrate DRC engine that loads a
Rule-IR deck (YAML), checks GDS + layer map + netlist, and emits Violation JSON **and**
a KLayout report database (.lyrdb) so every violation is click-to-zoom in a free viewer
— that is the entire UI budget. Ships with a clearly-labeled generic default deck from
public sources, a synthetic demo substrate, and one golden fixture per rule class wired
into CI.

## Entry Gate
- [ ] Phase 0 schemas frozen (Rule IR + Violation).
- [ ] Phase 1 benchmark-harness pattern exists (this phase reuses it).
- [ ] You have written `docs/lint-spec.md` and curated `decks/generic-substrate-v0.yaml`
      (see Human-only tasks).

## Exit Gate
- [ ] Every golden fixture GDS fires exactly its planted violation, nothing else.
- [ ] Clean synthetic substrate: zero violations.
- [ ] Full run on the demo substrate < 60 s on a laptop.
- [ ] `out.lyrdb` opens in KLayout with clickable, correctly-located markers
      (screenshot committed to docs/).
- [ ] Deck loader rejects malformed decks with cited line numbers.

## Human-only tasks (~6 hrs)
1. **Curate `decks/generic-substrate-v0.yaml`** — representative values from genuinely
   public sources only (IPC-2221/2226 as named references, JEDEC ball-pitch families,
   public PCB-fab capability pages as inspiration for the HDI-adjacent numbers). Every
   value carries a `citation`. Header block in caps: **GENERIC DEFAULTS — NOT
   MANUFACTURING VALID — DO NOT TAPE OUT ON THIS DECK.** No number traceable to any
   NDA'd vendor document. This is the ASAP7 move.
2. **Write `docs/lint-spec.md`** — exact semantics per check (below, refine as needed).
3. **Author golden fixtures**: for each check, a tiny GDS (make them with KLayout's
   editor or a 10-line gdstk script you write yourself) containing exactly one planted
   violation, plus `expected.json` with the violation's measured/required/location that
   you verified by hand with KLayout's ruler. ~12 fixtures. This is the core oracle
   work — budget 3 hrs here alone.

## Research pack

**Engine choice — important.** Use the `klayout` pip module (`import klayout.db as kdb`)
for the check primitives, and `gdstk` only for *generating* synthetic geometry. KLayout's
`Region` class ships production-grade DRC operations:
- `Region.width_check(d)` / `Region.space_check(d)` → `EdgePairs` of violations
- boolean ops (`&`, `-`, `+`, `^`), `Region.sized(d)` for grow/shrink
- `ReportDatabase` — build categories/items programmatically and `.save("out.lyrdb")`;
  no hand-crafted XML needed. Items carry polygons/edge-pairs so markers are clickable.
Work in integer DBU: read `layout.dbu`, convert µm→dbu once at the boundary, everything
internal is int. the coding agent must fetch the KLayout Python API docs for Region /
ReportDatabase into `reference/klayout/` before implementing.

**Check semantics (put the precise versions in docs/lint-spec.md):**
- *trace_width_min* (per layer class): `Region.width_check(w_min)` on the routing
  layers listed for that class.
- *spacing_min* (line-line, line-shape): `space_check` within a layer; between nets
  requires net-aware regions — v0 scope: geometric spacing only, net-aware deferred;
  say so in the coverage report.
- *degas_to_trace_clearance_min*: degas voids = plane layer holes on the degas layer
  (or derived: plane polygons XOR bounding plane). Violation = `traces & degas_voids.sized(c)`
  non-empty; each resulting polygon is one violation with its bbox as location.
- *degas_coverage_window*: sliding window (configurable, e.g. 5×5 mm step 2.5) —
  void_area/window_area within [min,max] per deck.
- *copper_balance_window*: same windowing, copper density per layer within band;
  report worst window per layer.
- *annular_ring_min*: GDS has no drill intent → input includes `padstacks.csv`
  (pad name, pad dia, drill dia, layer span). Check = (pad_dia − drill_dia)/2 ≥ min,
  cross-checked against drawn pad geometry diameter where present.
- *ball_grid*: pad diameter band; grid pitch uniformity; depop conformance vs pattern
  spec (reuse Phase 1 depop logic on extracted ball centroids).
- *copper_to_edge_min*: all-layer copper vs outline layer `sized(-margin)` inversion.

**Windowed density math**: rasterize per window via `Region.area()` of
`region & window_box` — O(windows × polys) fine at substrate scale; note substrates are
10³–10⁶ polygons, not IC-scale, so seconds-to-minutes is achievable single-threaded.

**Deck → checks routing**: the Rule IR `routing: external` rules map to these check
implementations via the `parameter` vocabulary; unknown parameters produce a loud
`coverage: unimplemented` entry in the run report — the honest-coverage doctrine,
mechanized.

**.lyrdb**: KLayout marker/report database; ReportDatabase API writes it natively.
Category per rule id; item per violation; attach the edge-pair or polygon.

Deps allowed: klayout, gdstk, numpy, pyyaml, rich.

## the coding agent prompts

### Prompt 2.1 — deck loader + coverage reporter
```
/goal Load a Rule-IR YAML deck, validate against schema, resolve which rules map to implemented checks, and emit a coverage report (implemented / unimplemented / manual) before any geometry runs.
/context Phase 2. decks/generic-substrate-v0.yaml is human-authored and frozen. Unknown `parameter` values are NOT errors — they are `unimplemented` coverage entries.
/inputs schemas/rule_ir.schema.json, decks/generic-substrate-v0.yaml, docs/lint-spec.md
/constraints Malformed deck → error with YAML line numbers. Coverage report is machine-readable JSON + rich table.
/deliverables src/pkgtk/lint/deck.py, src/pkgtk/lint/coverage.py, tests/test_deck.py
/verify Golden deck loads; a deliberately broken deck fixture fails with line-cited errors; make ci green.
```

### Prompt 2.2 — geometry engine core
```
/goal Implement the check primitives on klayout.db Regions per docs/lint-spec.md: width, spacing, clearance-with-sizing, windowed density, copper-to-edge; all DBU-internal, µm at the boundary.
/context Phase 2. Fetch KLayout Region/ReportDatabase API docs into reference/klayout/ first. Golden fixtures exist: fixtures/golden/lint/<check>/{in.gds,layers.yaml,expected.json}.
/inputs docs/lint-spec.md, fixtures/golden/lint/, schemas/violation.schema.json
/constraints klayout module for checks; gdstk forbidden here. Pure functions (layout, layer_map, params) → [Violation]. Locations in µm in output. Do not modify fixtures.
/deliverables src/pkgtk/lint/engine.py, src/pkgtk/lint/checks/*.py, tests/test_lint_checks.py
/verify Each golden fixture fires exactly its expected violation (measured/required/location within 1 dbu); clean fixture fires zero; make ci green.
```

### Prompt 2.3 — .lyrdb emitter + CLI
```
/goal `pkgtk check design.gds --deck deck.yaml --layers layers.yaml` producing violations.json + out.lyrdb via klayout ReportDatabase, one category per rule, clickable items.
/context Phase 2. Engine from 2.2 is green.
/inputs src/pkgtk/lint/, fixtures/golden/lint/
/constraints ReportDatabase API only (no hand-built XML). Exit code nonzero iff violations at severity hard.
/deliverables src/pkgtk/lint/lyrdb.py, src/pkgtk/cli/check.py, tests/test_lyrdb.py (parse the written lyrdb back and assert item counts/categories)
/verify CLI run on a golden fixture writes both outputs; lyrdb re-parses with correct counts; make ci green.
```

### Prompt 2.4 — synthetic demo substrate
```
/goal gdstk generator for a 2-metal-layer demo substrate: plane with degas hole array, trace bus crossing it, ball grid with corner depop, outline — parameterized and seeded — plus a "dirty" variant embedding one violation per implemented check.
/context Phase 2. This is demo/benchmark data, lives in fixtures/synthetic/ (regenerable).
/inputs docs/lint-spec.md, src/pkgtk/lint/
/constraints Deterministic seed. Dirty-variant defect list encoded in a manifest JSON so the benchmark can assert catch-by-name.
/deliverables src/pkgtk/synth/substrate_gen.py, Makefile target extending `bench` with the lint suite
/verify Clean variant: zero violations. Dirty variant: every manifest defect caught, no extras. Full run < 60 s. make ci green.
```

## Cut line (in order)
Net-aware spacing (already deferred), annular-ring drawn-geometry cross-check (keep the
padstack-table check), copper-balance per-layer-pair symmetry. Never cut the lyrdb
output or the golden fixtures.
