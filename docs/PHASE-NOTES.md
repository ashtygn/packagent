# Phase notes — interpretation decisions & flagged gaps

This is the honesty ledger for the autonomous overnight build. The project rule is
**flagged gap = fine, silent wrong = fatal**. Every place where the agent acted as the
delegated human oracle (authoring schemas, spec docs, or golden fixtures that the plan
reserves for the human) is recorded here so the human can review and, where needed,
override. Nothing here was decided silently.

## Standing context
- The user explicitly delegated oracle authority for this run ("no permissions needed
  from me… agent running all night… go through every readme and complete the sub-goals").
- Where a phase reserves work as "human-only" (schemas, `*-spec.md`, hand-authored golden
  fixtures), the agent authored a best-effort version from the detailed field/semantics
  specs in each `PhaseN.md`, and recorded the interpretation choices below.
- `GOLDEN_EDIT=1` was used to commit initial `fixtures/golden/**` content, since that is
  the human-oracle escape hatch and the directory started empty.
- **Push to GitHub**: was blocked during the overnight build (cached credential for a
  different account, HTTP 403); resolved since — verified 2026-07-20 that origin is
  fully synced and the v0.1.0 tag is pushed.

## Phase 0 — Foundation
Schemas authored (frozen v0.1.0): `rule_ir`, `connectivity_graph`, `violation`.
Decisions:
- **Rule IR `value`** modeled as a discriminated union on `kind` (`scalar` /
  `expression` / `piecewise`) rather than an untagged oneOf, for clean pydantic mapping.
- **`parameter`** is an open string (not a closed enum): unknown parameters must surface
  as `coverage: unimplemented` at run time per the honest-coverage doctrine, not be
  rejected at schema level.
- **`severity`/`executability`/`routing`** are closed enums (they map to behavior);
  **`tier`** is an open string (vendor tier names vary).
- **Free-text condition ⇒ `executability: manual`** is enforced as a pydantic
  model-validator invariant (JSON Schema if/then left out for readability; documented).
- **`connectivity_graph` node roles** standardized to `signal/gnd/pwr/nc`. Phase 5's
  template uses `sig`; the template checker will map `sig → signal`.
- **`violation.measured/required`** accept either `{value, units}` or a bare string
  (for non-numeric results like a role swap).
- Round-trip is asserted **semantically** (parsed-JSON equality of `model_dump(
  exclude_none=True)` vs input), not byte-identical, since JSON key order/whitespace are
  not meaningful. Model defaults are left as `None` (not the schema's documented
  defaults) so round-trip fidelity holds.

## Phase 1 — Ball-map verifier + ECO diff
Done: `docs/checks-spec.md` (normative), check engine (8 families, `pkgtk verify`),
ECO diff (`pkgtk diff`), synthetic generator + 20-case benchmark (`make bench`,
BENCHMARKS.md), AIF parser (`pkgtk` ingest side). All golden fixtures hand-authored; the
20/20 catch rate and 0 false positives on a 2025-ball design are real.
Decisions / flagged:
- **Benchmark = 20 cases** across the 8 check families (15 distinct + 5 locality
  variants). The plan said "20 defects"; padding to 20 with near-duplicates adds no
  coverage, so 5 cases re-run a family at a different grid location to prove locality.
- **5 exact golden bench cases** (`fixtures/golden/bench/bench01-05.json`) are frozen
  snapshots of hand-verified single-defect runs; the other 15 assert catch+location.
- **Connectivity semantics** were under-specified by the plan (it lists check names, not
  graph encoding). checks-spec.md pins them: nets = `substrate_net` nodes, ball↔net =
  edges, roles/domains/interfaces = node attrs. Adjustable if real data disagrees.
- **AIF NETLIST row layout** is a documented simplification (the fetched spec lists the
  section catalog, not per-row columns). See reference/aif/README.md. Section-skipping
  and lossless `extras` preservation are layout-independent and correct.
- **DEFERRED (cut per Phase-1 cut-line): Prompt 1.2 Excel/CSV ballmap ingestion + the
  `mapping.yaml` mechanism.** It needs binary xlsx goldens and is not in the Phase-1
  exit gate (which is checks/diff/bench). The deterministic pipeline it would feed
  (checks) is complete and tested via JSON graphs and AIF. Phase 4's mapping-inference
  seam depends on this; flagged there too. This is the one real Phase-1 gap.

## Phase 2 — package-lint geometry checker
klayout 0.30.9 + gdstk 1.0.1 install and import cleanly on this Windows box, so the
KLayout DRC engine is real. Done: `decks/generic-substrate-v0.yaml` (NOT-MANUFACTURING-
VALID banner, cited public values), `docs/lint-spec.md` (normative), deck loader +
coverage reporter, geometry engine (4 checks), lyrdb emitter + `pkgtk check` CLI,
synthetic demo substrate (clean + dirty). Golden GDS fixtures each fire exactly their
planted violation with hand-verified measured (12/10/30 µm); clean substrate = 0.
Decisions / flagged:
- **Implemented checks (4)**: trace_width_min, spacing_min,
  degas_to_trace_clearance_min, copper_to_edge_min. **Unimplemented (surfaced by the
  coverage reporter, never silent)**: degas_coverage_window, copper_balance_window
  (windowed density), annular_ring_min (needs padstack table), ball_grid. Net-aware
  spacing deferred (v0 = geometric spacing only). This matches the honest-coverage
  doctrine and the Phase-2 cut-line.
- **degas clearance** is always measured signal-traces↔degas voids; a deck rule's
  `scope.layer_class` names the plane/degas context, not the trace layer.
- **CLI runs scalar-valued rules only.** Piecewise/expression rules (e.g. the advanced
  width table) need a design-variable (`A`) binding not available at the `pkgtk check`
  boundary in v0; they are skipped with a printed note. Flagged for a future
  variable-binding mechanism.
- **lyrdb screenshot** (Exit-Gate item "out.lyrdb opens in KLayout with clickable
  markers, screenshot committed") is DEFERRED — needs a GUI/human. The .lyrdb is
  generated and its categories/items round-trip-verified programmatically
  (tests/test_lyrdb.py); a real KLayout screenshot is a human task.
- Golden GDS `measured`/`required` are hand-computed physical truths (I drew a 12-µm
  trace); `location`/`extent` are tool-derived-then-frozen (standard snapshot).

## Phase 3 — SI/PI validator stack
Done: `docs/models-spec.md` (normative), Touchstone quality gate, IBIS gate wrapper,
model librarian. Decisions / flagged:
- **Touchstone gate is self-contained numpy** (own parser + passivity via per-frequency
  max singular value + reciprocity), NOT scikit-rf. Rationale: keeps the gate in core CI
  without a heavy platform-specific dependency; skrf can be swapped behind the same
  interface. IEEE-370 causality is **not** implemented — emitted as
  `causality: unassessed` (the human-decided fallback). Fixtures are hand-authored with
  the passivity math verified by hand (σ_max: good=0.6, non-passive=1.2; port-mismatch
  rejected pre-parse).
- **IBIS gate** parses captured ibischk stdout (recorded mode) — CI needs no executable;
  live run behind `PKGTK_IBISCHK`. Real vendor IBIS files (TI/ADI) were NOT downloaded
  (network/manual); the captured-stdout fixtures are hand-authored representative
  ibischk output. Flagged: swap in real captured output when an executable is available.
- **COM runner (3.3) CUT** per the Phase-3 cut-line. It requires vendoring a maintained
  Python COM port from GitHub with license/provenance (network + trust review) and the
  instruction is to STOP rather than write COM from scratch. Not attempted offline; the
  validator stack stands without it. `pkgtk com` is absent; flagged as the known Phase-3
  gap. Any future COM output must carry `UNVALIDATED_AGAINST_MATLAB_REFERENCE`.
- **Librarian** uses stdlib sqlite3 + a numbered migration + jinja2 chase template; full
  state machine + rejected-intake-holds-at-received verified.

## Phase 5 — Wow tier (PDN / escape / template)
Done: `docs/pdn-spec.md` + `escape-spec.md` (normative), cavity-model PDN engine,
escape oracle, template checker. All pure numpy/scipy. Physics is real:
- **PDN**: analytic resonances match hand-computed golden EXACTLY (f₁₀=1.8737,
  f₀₁=2.4983, f₁₁=3.1228 GHz); simulated |Z| peaks within 1%; low-freq |Z|=2995 Ω vs
  1/(ωC)=2996 Ω (0.02%); M=N=30 over 1000 pts in 0.011 s; decap drops low-freq |Z| >10×.
  Conductor/skin loss omitted (documented) — affects peak Q not location.
- **Escape**: n_tracks and capacity reproduce the hand-counted golden exactly (8 tracks,
  160 capacity); feasible/infeasible verdicts with utilization %. Line/space pulled from
  a Rule-IR deck (not hardcoded). v2 max-flow cited, not implemented (v0 scope).
- **Template**: role-swap caught at the right position; conforming map clean; unknown
  positions flagged not errored. FLAGGED: the encoded template is an illustrative demo
  map, NOT a spec-exact UCIe/JEDEC map (spec access friction); swap in a real map from
  UCIe/JEDEC public docs when available. Anchor-offset alignment simplified to identity
  in v0.
- Phase gating note: Phase 5 was built before Phase 4's LLM core because Phase 4 is
  input-blocked (no API key, deferred xlsx) while Phase 5's entry gate (Phase-1 checks +
  Phase-2 deck) is green. Flagged deviation.

## Phase 4 — LLM layer (core built; live flows deferred)
Built the two "never cut" items (per the Phase-4 cut-line) plus the provider harness:
- **Paranoia battery** (`src/pkgtk/llm/battery.py`): all five deterministic checks —
  double-extraction, physics sanity (plausible ranges + inequality direction + piecewise
  monotonicity + restricted-AST expr), header inheritance, footnote binding (noted cell
  without a bound condition = auto-reject), and "---" → not_offered. Auto-accept policy
  (confidence ≥ 0.90 AND agreement AND battery pass) implemented and tested against every
  adversarial trap from the plan. This is pure code, no LLM — fully verified offline.
- **Provider + cassette harness** (`provider.py` / `cassette.py`): Anthropic behind a
  single abstraction (SDK imported lazily, live only), record/replay cassettes keyed by
  sha256(model, system, messages, schema), CI replay-only and **fails on cache miss**.
  A committed cassette fixture proves replay; live mode records. Token usage logged.
- **DEFERRED (need live Anthropic API + the deferred Phase-1 xlsx ingestion)**:
  4.2 Excel mapping inference, 4.3 net-name semantics, 4.4 two-pass rule-sheet extraction
  + review table, and the ground-truth `clean.xlsx`/`adversarial.xlsx` eval sheets. The
  deterministic battery that gates all of these IS built and tested; wiring it to real
  LLM calls needs an API key (set `ANTHROPIC_API_KEY` + `PKGTK_LLM_LIVE=1` to record
  cassettes) and the xlsx layer. Flagged as the Phase-4 gap. The cut-line's protected
  items (battery, cassette replay CI) are done.

## Phase 6 — Integration + launch artifact
Done: unified `pkgtk` CLI (dispatcher over verify/diff/check/models/escape/template/pdn;
absent com/extract/ingest reported cleanly), exit-code convention (0/1/2), `make demo`
(runs every wedge on fixtures → artifacts/ + MANIFEST.md in 3.9 s, well under 5 min,
including the PDN PNG and clickable lyrdb), combined `benchmarks/BENCHMARKS.md` via
`benchmarks.rollup` with a CI staleness guard, and the top-level README rewritten as the
launch artifact (what/why, quickstart, coverage table, benchmark summary, and a
prominent Honesty section listing every gap).
Decisions / flagged:
- The original 100-hour **build-plan README was preserved at `docs/build-plan.md`** (not
  destroyed) before the top-level README was replaced with the product/launch README, as
  Phase 6.3 specifies.
- `benchmarks.run` now writes `BENCHMARKS.phase1.md`; the canonical combined
  `BENCHMARKS.md` is written by `benchmarks.rollup` (avoids clobbering).
- Screenshots/GIF media (Exit-Gate human task 2) and the v0.1.0 git tag's push are the
  remaining human/GUI steps; the tag is created locally. Push to GitHub is still blocked
  on credentials (see Standing context).
- Wheel packaging: schemas/ resolve from the repo root for editable installs (what CI +
  demo use); packaging schemas into a wheel is a follow-up (models SQL/templates are
  already declared as package-data).
