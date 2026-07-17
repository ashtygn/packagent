# llm-spec.md — LLM layer policy (Phase 4, normative)

The LLM *proposes*; the deterministic pipeline *executes*; the human *confirms*. The LLM
never touches data rows and never emits a value that bypasses the review thresholds. All
five paranoia checks below are **deterministic code**, not prompt instructions.

## Provider
Anthropic API behind `src/pkgtk/llm/provider.py`; structured outputs constrained to the
Phase-0 JSON Schemas; temperature 0; bounded retries. No other module imports the SDK.
**Recorded-response testing**: every dev call is recorded (stable hash of
`(model, system, messages, schema)` → response JSON under
`fixtures/synthetic/llm_cassettes/`); CI runs **replay-only** and fails on cache miss.
Live mode behind `PKGTK_LLM_LIVE=1`.

## The paranoia battery (runs on every extraction)
1. **Double extraction** — same section, two prompt variants; structural diff of the two
   Rule-IR outputs. Any disagreement → review, never auto-accept.
2. **Physics sanity** — units within plausible ranges per parameter vocabulary (a 15 mm
   trace width is a parse error, not a rule); inequality direction consistent with
   Min/Max headers; monotonicity across piecewise brackets; expressions must parse in
   the Phase-0 restricted AST and evaluate over their bracket domain.
3. **Header inheritance** — a table-level units/Min declaration must propagate to every
   extracted row, or the row is flagged.
4. **Footnote binding** — any cell with a note reference must yield either a structured
   condition or `executability: manual`. A bare value from a noted cell is an automatic
   **reject** regardless of confidence.
5. **"---" semantics** — dash / em-dash / blank in a tier column maps to `not_offered`,
   never 0, never null-as-pass.

## Auto-accept policy
Auto-accept requires **all** of: `confidence ≥ THRESHOLD` (THRESHOLD = 0.90) AND
double-extraction agreement AND full battery pass. Everything else → the review table
(terminal `rich` accept/edit/reject; a web UI is explicitly out of scope). A noted cell
without a bound condition is an automatic reject regardless of confidence.

## Plausible ranges (physics sanity, µm unless noted)
- `trace_width_min`, `spacing_min`, `degas_to_trace_clearance_min`,
  `annular_ring_min`: [1, 1000] µm.
- `copper_to_edge_min`: [10, 5000] µm.
- `copper_balance_window`, `degas_coverage_window`: [0.1, 50] mm.
A value outside the range for its parameter is a parse error → reject.
