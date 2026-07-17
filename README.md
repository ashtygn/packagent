# pkgtk — package-design verification toolkit

`pkgtk` is a deterministic, read-only verification toolkit for IC-package and substrate
design. It ingests ball maps and die data into a shared connectivity graph, runs
netlist-stage checks and semantic ECO diffs, lints substrate geometry against a Rule-IR
deck with a KLayout report database you can click through, gates SI/PI models
(Touchstone passivity, IBIS golden-parser), and computes tier-0 physics oracles (PDN
cavity impedance, escape capacity, interface-template compliance). Every wedge is
bottom-of-the-trust-ladder analysis: it tells you what is wrong, it never silently
"fixes" your design.

The project's thesis is a discipline, not a feature: **no agent-written component merges
without a human-authored golden fixture that was hand-computed.** The three shared JSON
Schemas (Rule IR, Connectivity Graph, Violation) are frozen at v0.1.0 and are the
product's real land-grab — every wedge consumes or emits one of them.

The second thesis is honesty. **A flagged gap is fine; a silent wrong answer is fatal.**
Coverage is mechanized: an unknown rule parameter surfaces as `coverage: unimplemented`,
never as a silent pass. What this toolkit does *not* do is documented as prominently as
what it does — see the Honesty section below.

## Quickstart

```bash
python -m venv .venv && . .venv/Scripts/activate   # or .venv/bin/activate
pip install -e ".[dev]"
pre-commit install
make ci        # ruff + pytest, must be green
make bench     # regenerate benchmark numbers
make demo      # run every wedge on bundled fixtures -> artifacts/
```

Geometry lint needs KLayout: `pip install -e ".[geometry]"` (platform-specific wheels).
SI extras: `pip install -e ".[si]"`; LLM extras: `pip install -e ".[llm]"`.

```bash
pkgtk verify design_graph.json --config run.json     # netlist-stage checks
pkgtk diff revA.json revB.json                        # semantic ECO diff
pkgtk check design.gds --deck deck.yaml --layers layers.yaml   # geometry DRC + lyrdb
pkgtk pdn --png z.png                                  # PDN |Z| curve
pkgtk escape --deck deck.yaml --pitch-um 800 ...       # escape-capacity verdict
pkgtk template map.json --template iface.yaml          # template compliance
```

## Coverage

| Wedge | Status |
|-------|--------|
| Schemas (Rule IR / Connectivity Graph / Violation) + round-trip/parity | ✅ frozen v0.1.0 |
| Restricted expression AST (no `eval`) | ✅ |
| Ball-map checks (8 families) + ECO diff | ✅ 20/20 seeded, 0 false positives |
| AIF ingestion | ✅ (Excel/CSV ingestion deferred) |
| Geometry lint (width, spacing, degas clearance, copper-to-edge) + lyrdb | ✅ 4 checks |
| Touchstone passivity/reciprocity gate | ✅ |
| IBIS golden-parser wrapper | ✅ (captured-stdout tests; live behind `PKGTK_IBISCHK`) |
| Model librarian (state machine + chase email) | ✅ |
| LLM paranoia battery + cassette replay harness | ✅ (live extraction flows deferred) |
| PDN cavity model / escape oracle / template checker | ✅ physics-verified |

**Generic deck coverage** (`decks/generic-substrate-v0.yaml`, 11 rules):
**5 implemented, 4 unimplemented (flagged), 2 manual-checklist.**

## Benchmarks

See [`benchmarks/BENCHMARKS.md`](benchmarks/BENCHMARKS.md) (generated). Headline:
ball-map **20/20** seeded defects caught with **0** false positives on a 2025-ball
design; geometry lint **4/4** dirty defects caught with a clean substrate at zero; PDN
low-frequency |Z| within **0.02%** of the analytic 1/(ωC); Touchstone non-passive and
port-mismatch fixtures correctly rejected.

## Honesty — what this does NOT do (v0.1.0)

- **The generic deck is NOT manufacturing-valid.** `decks/generic-substrate-v0.yaml`
  carries only representative values from public sources (IPC-2221/2226, JEDEC pitch
  families, public fab pages). Header banner: **GENERIC DEFAULTS — NOT MANUFACTURING
  VALID — DO NOT TAPE OUT ON THIS DECK.**
- **Geometry coverage is partial.** Implemented: width, spacing, degas-to-trace
  clearance, copper-to-edge. Unimplemented (surfaced by the coverage reporter, never a
  silent pass): windowed density (`copper_balance_window`, `degas_coverage_window`),
  `annular_ring_min`, `ball_grid`. **Net-aware spacing is deferred** — v0 does geometric
  spacing only.
- **COM (Channel Operating Margin) is not included.** It requires vendoring a maintained
  Python port with provenance; per plan it is the first cut. Any future COM output must
  be stamped `UNVALIDATED_AGAINST_MATLAB_REFERENCE`.
- **PDN v0 omits conductor/skin loss** (dielectric loss only). This affects peak Q, not
  peak location — which is what the physics invariant checks.
- **Excel/CSV ball-map ingestion is deferred** (AIF ingestion is implemented); the
  deterministic checks are fully tested via JSON graphs and AIF.
- **The LLM live extraction flows are deferred.** The deterministic paranoia battery that
  gates them and the replay-only cassette harness are built and tested; wiring to a live
  Anthropic API needs a key.
- **IBIS fixtures are captured representative stdout**, not real vendor model runs; the
  interface-template is an illustrative demo map, not a spec-exact UCIe/JEDEC map.

Every interpretation decision made while building is logged in
[`docs/PHASE-NOTES.md`](docs/PHASE-NOTES.md). The 100-hour build plan is preserved at
[`docs/build-plan.md`](docs/build-plan.md); per-check semantics live in `docs/*-spec.md`.

## Layout

```
schemas/        frozen JSON Schemas (v0.1.0), source of truth
src/pkgtk/      ingest/ checks/ diff/ lint/ models/ oracles/ llm/ cli/ synth/ schemas/
decks/          generic-substrate-v0.yaml (NOT manufacturing valid)
fixtures/golden human-authored ground truth (guarded read-only)
benchmarks/     seeded-defect cases + generated BENCHMARKS.md
docs/           schemas.md, *-spec.md, PHASE-NOTES.md, build-plan.md
```
