# Phase 4 — LLM Layer (12 hrs)

## Goal
The LLM enters the system for the first time, at exactly three seams, always behind a
human-confirm step and a deterministic paranoia battery: (1) Excel schema inference for
ball-map ingestion, (2) net-name semantics proposal, (3) rule-sheet → Rule IR
extraction with citations. **The LLM proposes; the deterministic pipeline executes;
the human confirms.** The LLM never touches data rows and never emits a value that
bypasses review thresholds.

## Entry Gate
- [ ] Phase 1 mapping.yaml mechanism and deterministic ingestion green.
- [ ] Phase 2 Rule-IR loader green.
- [ ] You have authored the two ground-truth rule sheets (Human-only task 1).

## Exit Gate
- [ ] Mapping inference produces a correct mapping.yaml for 3 differently-shaped
      ballmap sheets (the two Phase-1 goldens + one new adversarial layout).
- [ ] Adversarial rule sheet: **100% precision on auto-accepted rules.** Misses are
      permitted only if flagged as unparsed. The footnote-condition trap is either
      bound correctly or flagged — never silently dropped. The unit-header trap never
      yields a wrong-unit value.
- [ ] All tests pass offline via recorded responses; live mode behind an env flag.

## Human-only tasks (~4 hrs)
1. **Author two ground-truth rule sheets** in your team's realistic style:
   - `clean.xlsx`: ~25 rules, tidy table, one units header.
   - `adversarial.xlsx`: ~20 rules containing every trap from the thread: a
     units-in-header-only table ("mm, Min."), a piecewise bracket table, a formula rule
     (A×10%), a footnote that conditions a value ("Note 1: not applicable with
     conductive adhesive"), a tiered Normal/Advanced pair with "---" cells
     (meaning *not offered*, not zero), and one merged-cell layout crime.
   - Hand-encode both to expected Rule-IR JSON. This is the eval; do not delegate it.
2. **Set the auto-accept policy** in `docs/llm-spec.md`: auto-accept requires
   (confidence ≥ threshold) AND (double-extraction agreement) AND (physics battery
   pass); everything else goes to the review table. Choose the threshold.
3. Review-table UX decision: terminal `rich` table with accept/edit/reject per row is
   sufficient for the 100 hours; write down that a web UI is explicitly out of scope.

## Research pack
- **Provider layer**: Anthropic API, structured outputs constrained to the JSON Schemas
  from Phase 0, temperature 0, bounded retries with jitter. Abstract behind
  `src/pkgtk/llm/provider.py` so tests inject a fake. **Recorded-response testing**:
  every live call in dev gets recorded (request-hash → response JSON under
  fixtures/synthetic/llm_cassettes/); CI runs replay-only, fails on cache miss.
- **The paranoia battery** (deterministic, runs on every extraction — port the thread
  doctrine verbatim into code):
  1. *Double extraction*: same section, two prompt variants; structural diff of the two
     Rule-IR outputs; any disagreement → review, never auto-accept.
  2. *Physics sanity*: units within plausible ranges per parameter vocabulary (a 15 mm
     trace width is a parse error, not a rule); inequality direction consistent with
     Min/Max headers; monotonicity across piecewise brackets; expressions must parse in
     the Phase-0 restricted AST and evaluate over their bracket domain.
  3. *Header inheritance check*: a table-level units/Min declaration must propagate to
     every extracted row or the rows are flagged.
  4. *Footnote binding check*: any cell with a note reference must yield either a
     structured condition or `executability: manual` — a bare value from a noted cell
     is an automatic reject.
  5. *"---" semantics*: dash/em-dash/blank in a tier column maps to `not_offered`,
     never 0, never null-as-pass.
- **Net-name semantics**: propose diff pairs (regex-pair families), buses (numeric-
  suffix runs), power domains (VDD*/VSS* clustering) as *structured suggestions with
  confidence*, emitted as a proposed verifier config the human confirms — identical
  confirm-then-deterministic pattern as mapping inference.
- **Cost/latency note**: all three seams are cold-path (once per document / per
  project), so model choice can favor quality; log token usage per call.
- Deps allowed: anthropic, rich, plus Phase 0–2 internals.

## the coding agent prompts

### Prompt 4.1 — provider + cassette harness
```
/goal LLM provider abstraction (Anthropic, structured outputs against our JSON Schemas, temp 0, retries) with record/replay cassette testing; CI is replay-only and fails on cache miss.
/context Phase 4. Read docs/llm-spec.md. No other module may import the SDK directly — only through this provider.
/inputs schemas/, docs/llm-spec.md
/constraints API key via env only; live mode behind PKGTK_LLM_LIVE=1; cassette keys = stable hash of (model, system, messages, schema); token usage logged per call.
/deliverables src/pkgtk/llm/provider.py, src/pkgtk/llm/cassette.py, tests/test_provider_replay.py
/verify Replay tests green with no network; live-mode smoke test skips cleanly when env absent; make ci green.
```

### Prompt 4.2 — Excel mapping inference
```
/goal Given an unknown ballmap sheet, have the LLM propose a Phase-1 mapping.yaml (columns, header row, grid convention, NC markers) with per-field confidence; render a confirm table; on accept, run the existing deterministic Phase-1 ingestion unchanged.
/context Phase 4. The LLM sees headers + a 15-row sample, never the full data. Output constrained to the mapping-file schema (write that schema first if Phase 1 left it implicit — flag if so).
/inputs src/pkgtk/ingest/xlsx_ballmap.py, fixtures/golden/xlsx/, one new adversarial sheet fixtures/golden/xlsx/sheetC.xlsx + expected mapping
/constraints Deterministic pipeline is untouched; inference only produces the yaml. Low-confidence fields render as blanks requiring human entry, never guesses.
/deliverables src/pkgtk/llm/map_infer.py, src/pkgtk/cli/ingest.py (--infer-mapping flag), tests/test_map_infer_replay.py
/verify All three sheets: accepted mapping → ingestion matches expected graph JSON; cassettes committed; make ci green.
```

### Prompt 4.3 — net-name semantics
```
/goal Propose diff pairs, buses, and power domains from a net list as structured, confidence-scored verifier-config suggestions with a confirm step; confirmed config feeds the Phase-1 checks.
/context Phase 4. Suggestions must be expressible as the regex/grouping config Phase 1 already consumes — no new check semantics.
/inputs fixtures/golden/graphs/ net lists, src/pkgtk/checks/
/constraints Deterministic post-validation: every proposed pair must actually match both nets; every proposed domain must be non-overlapping; violations of these = drop the suggestion and log.
/deliverables src/pkgtk/llm/net_semantics.py, tests/test_net_semantics_replay.py
/verify On the golden net lists, confirmed suggestions reproduce the hand-written configs; invalid-suggestion injection test proves the post-validator drops them; make ci green.
```

### Prompt 4.4 — rule-sheet extraction + review flow
```
/goal Two-pass extraction from Excel rule sheets to Rule-IR (survey pass classifying regions, then per-region structured extraction with citations to sheet/cell), gated by the full paranoia battery from docs/llm-spec.md, with a rich review table (accept/edit/reject) and auto-accept only per the human-set policy.
/context Phase 4. fixtures/golden/rulesheets/{clean.xlsx,adversarial.xlsx} with hand-encoded expected IR are the eval. The five battery checks are enumerated in docs/llm-spec.md — implement all five as deterministic code, not prompt instructions.
/inputs docs/llm-spec.md, fixtures/golden/rulesheets/, schemas/rule_ir.schema.json, src/pkgtk/schemas/expr.py
/constraints Auto-accept path requires battery-pass AND double-extraction agreement AND confidence ≥ threshold. A noted cell without a bound condition is an automatic reject regardless of confidence. Review decisions are persisted so re-runs don't re-ask.
/deliverables src/pkgtk/llm/rule_extract.py, src/pkgtk/cli/extract.py, tests/test_rule_extract_replay.py, an eval script emitting precision/recall vs expected IR into benchmarks/
/verify Clean sheet ≥ 90% auto-accepted, 100% precision. Adversarial sheet: 100% precision on auto-accepted; footnote and units traps flagged or correct; "---" mapped to not_offered; eval numbers land in BENCHMARKS.md; make ci green.
```

## Cut line (in order)
Net-name semantics (4.3) first — it's the least load-bearing. Then review-decision
persistence. Never cut the paranoia battery, the cassette replay CI, or the
adversarial-sheet eval.
