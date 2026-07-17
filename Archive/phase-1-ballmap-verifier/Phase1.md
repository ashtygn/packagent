# Phase 1 — Ball-Map Verifier + ECO Diff (20 hrs)

## Goal
The research-verified beachhead: read-only, zero-trust, unclaimed by incumbents.
Ingest ball maps from Excel/CSV and die data from AIF/CSV into the Connectivity Graph,
run formal netlist-stage checks (the errors that otherwise die at bring-up), and produce
semantic ECO diffs between revisions with impact classification. Ships with a synthetic
2,000-ball generator, the Caravel pad map as a real open example, and a 20-case
seeded-defect benchmark with published catch rates.

## Entry Gate
- [ ] Phase 0 Exit Gate green. Schemas frozen at v0.1.
- [ ] You have hand-written `docs/checks-spec.md` (see Human-only tasks) BEFORE any
      check prompt runs.

## Exit Gate
- [ ] All 20 benchmark cases: seeded defect caught, correct check name, correct location.
- [ ] Clean synthetic design: **zero** violations (false-positive gate).
- [ ] ECO diff on golden rev-pair reproduces the hand-computed expected report exactly.
- [ ] `pkgtk verify <files>` and `pkgtk diff <A> <B>` work from a clean clone per README quickstart.
- [ ] BENCHMARKS.md auto-generates with the catch-rate table.

## Human-only tasks (~5 hrs)
1. **Write `docs/checks-spec.md`** — precise semantics for every check (this is the
   file Claude Code implements against; ambiguity here becomes bugs there):
   - *Bijection/multi-assignment*: a ball maps to ≤1 net; a net may map to many balls
     only if `role ∈ {gnd, pwr}` or explicitly flagged multi-ball.
   - *Missing grounds*: per declared interface region, actual gnd count ≥ template/ratio.
   - *Diff pairs*: nets matching configured regex pairs (default `(.*)_P$`/`\1_N$`,
     plus `(.*)P$`/`\1N$` opt-in) must both exist; if `adjacency_required`, partner
     balls must be grid-adjacent (Chebyshev distance 1).
   - *Match groups*: all members present, same interface, no member reassigned across
     domains.
   - *Domain crossing*: a substrate net may touch balls of exactly one power domain
     unless flagged `bridge`.
   - *Floating/orphan*: die pad with no path to ball; ball with no net; NC collisions.
   - *Duplicates*: ball grid IDs unique; die pad names unique.
   - *Depop conformance*: given a depop pattern spec (corner N×N, ring, custom list),
     flagged positions must be role `nc`.
2. **Hand-author 5 of the 20 benchmark expected outputs** completely (violation JSON,
   exact locations). The other 15 may be generator-derived but you spot-check each.
3. **Hand-write `fixtures/golden/aif/minimal.aif`** (10-pad die, 20-ball map) and its
   expected graph JSON.
4. Export the Caravel pad table (you already have `pad_table.csv` from the caravel
   project — copy it in as a real-world ingestion example; it is Apache-licensed data).

## Research pack
- **AIF format**: Artwork Conversion Software's ASCII interchange format for die /
  bondshell / BGA data — INI-style sections, die pads with net names, balls, wires;
  designed to be trivially parsed; Amkor adopted it as preferred die-exchange format
  and a SKILL reader into APD exists (proof of parseability). Spec pages:
  https://www.artwork.com/package/aif/ and
  https://www.artwork.com/package/aif/what_is_in_aif.htm — Claude Code must fetch both
  into `reference/aif/` before writing the parser. Parser rule: unknown sections are
  preserved losslessly in an `extras` dict, never dropped.
- **Excel reality**: every org's ballmap sheet is shaped differently. Phase 1 uses a
  **declared mapping file** (`mapping.yaml`: sheet name, header row, column→field map,
  grid orientation A1-vs-numeric, NC markers list). Phase 4 later *infers* this file
  with an LLM; the deterministic pipeline is identical either way.
- **Grid conventions**: JEDEC-style ball naming skips letters I, O, Q, S, X, Z in row
  designators on many parts — make the row-letter alphabet configurable in mapping.yaml
  with the JEDEC-skip alphabet as a documented preset. Handle multi-letter rows (AA, AB).
- **Diff identity semantics** (put in checks-spec too): primary identity = net name;
  secondary = ball position. Classification: `net_moved` (same net, new ball),
  `ball_repurposed` (same ball, new net), `added`/`removed`, `pair_broken`,
  `match_group_broken`, `domain_changed`. Impact rollup counts per interface.
- Deps allowed: pandas, openpyxl, networkx, pyyaml, rich (report rendering).

## Claude Code prompts

### Prompt 1.1 — AIF parser
```
/goal AIF parser that emits Connectivity Graph JSON (die_pad + net tiers), lossless on unknown sections.
/context Phase 1. Fetch the two artwork.com AIF pages into reference/aif/ first and cite them in the module docstring. Schemas frozen.
/inputs schemas/connectivity_graph.schema.json, fixtures/golden/aif/minimal.aif + minimal.expected.json
/constraints Do not modify fixtures/golden/. Unknown sections → extras, never dropped. Encoding tolerant (latin-1 fallback).
/deliverables src/pkgtk/ingest/aif.py, tests/test_aif.py
/verify pytest green; parsing minimal.aif reproduces minimal.expected.json exactly; make ci green.
```

### Prompt 1.2 — Excel/CSV ballmap ingestion with mapping.yaml
```
/goal Ingest arbitrary ballmap spreadsheets via a declared mapping.yaml into the Connectivity Graph (ball tier), with JEDEC row-letter preset and grid-position validation.
/context Phase 1. Read docs/checks-spec.md §grid conventions. Two golden sheets exist with different shapes plus their mapping.yaml files and expected JSON.
/inputs fixtures/golden/xlsx/{sheetA.xlsx,sheetA.mapping.yaml,sheetA.expected.json, sheetB...}, schemas/
/constraints pandas+openpyxl only. Reject (with actionable error) rather than guess when mapping fields are missing. Round-trip: an export function that writes the graph back to the SAME sheet shape must produce a semantically identical re-ingest.
/deliverables src/pkgtk/ingest/xlsx_ballmap.py, src/pkgtk/export/xlsx_ballmap.py, tests/test_xlsx_roundtrip.py
/verify Both golden sheets ingest to expected JSON; round-trip test green; make ci green.
```

### Prompt 1.3 — check engine
```
/goal Implement all checks in docs/checks-spec.md against the Connectivity Graph, emitting Violation-schema JSON.
/context Phase 1. checks-spec.md is normative; where it is ambiguous, stop and flag — do not decide silently.
/inputs docs/checks-spec.md, schemas/, fixtures/golden/graphs/ (small hand-made graphs, one per check, each with exactly one planted defect + expected violation JSON)
/constraints One module per check family; a registry so `pkgtk verify` runs all; pure functions graph→[Violation]; no I/O inside checks.
/deliverables src/pkgtk/checks/*.py, src/pkgtk/cli/verify.py, tests/test_checks.py
/verify Every golden graph fires exactly its expected violation and nothing else; clean graph fires zero; make ci green.
```

### Prompt 1.4 — ECO diff engine
```
/goal Semantic diff between two Connectivity Graphs with the classification taxonomy from docs/checks-spec.md, plus a rich-rendered impact report and JSON output.
/context Phase 1. Golden rev-pair with fully hand-computed expected report exists.
/inputs fixtures/golden/diff/{revA.json,revB.json,expected_diff.json,expected_report.md}, docs/checks-spec.md §diff
/constraints Deterministic ordering in outputs (sort keys) so diffs are byte-stable. Report sections: summary counts, per-interface rollup, per-change detail table.
/deliverables src/pkgtk/diff/engine.py, src/pkgtk/diff/report.py, src/pkgtk/cli/diff.py, tests/test_diff.py
/verify expected_diff.json and expected_report.md reproduced exactly; make ci green.
```

### Prompt 1.5 — synthetic generator + benchmark harness
```
/goal Parameterized 2,000-ball synthetic design generator (pitch, depop pattern, N interface blocks, domain regions) and a benchmark runner that seeds the 20 defined defects and emits BENCHMARKS.md with catch rates.
/context Phase 1. benchmarks/cases.yaml defines the 20 defects (human-authored). 5 have fully hand-authored expected outputs in fixtures/golden/bench/ — the runner must verify against those exactly; the other 15 verify catch+location only.
/inputs benchmarks/cases.yaml, fixtures/golden/bench/
/constraints Generator must be seeded/deterministic. BENCHMARKS.md is generated, never hand-edited (guard note at top).
/deliverables src/pkgtk/synth/ballmap_gen.py, benchmarks/run.py, Makefile target `bench`
/verify make bench → 20/20 caught, 0 false positives on the clean design, BENCHMARKS.md written; make ci green.
```

## Cut line (in order)
LEF/DEF ingestion (already cut — bump CSV covers the die side), board-symbol export,
sheetB round-trip export (keep ingest). Never cut the false-positive gate or the 5
hand-authored expected outputs.
