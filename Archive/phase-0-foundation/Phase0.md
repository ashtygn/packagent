# Phase 0 — Foundation (5 hrs)

## Goal
A working monorepo with CI, the three shared schemas authored **by you** and frozen at
v0.1, loaders/validators for them written by the coding agent, and the golden-fixture
discipline mechanically enforced. Everything downstream consumes this phase; nothing
downstream may force changes to it without a version bump.

## Entry Gate
- [ ] Hour Zero done: employment agreement read, public/private decision made, personal machine.
- [ ] Python 3.11+ and git available.

## Exit Gate (all must pass)
- [ ] `make ci` green (ruff + pytest).
- [ ] Three schemas exist as JSON Schema **and** pydantic models; round-trip tests pass
      (load example → validate → dump → byte-identical or semantically identical).
- [ ] One hand-written example instance per schema under `fixtures/golden/schema-examples/`.
- [ ] CI fails if any commit touches `fixtures/golden/**` (pre-commit hook or CI diff check).
- [ ] `docs/schemas.md` renders and explains every field.

## Human-only tasks (~3 of the 5 hrs) — DO NOT DELEGATE
Author the three schemas yourself. This is the land-grab; the format is the product.

**1. Rule IR** (`schemas/rule_ir.schema.json`) — required fields:
- `id`, `source` {doc, revision, page, table, row}, `scope` {layer_class, net_class,
  region, component_class — all optional},
- `parameter` (controlled vocabulary you define, e.g. `trace_width_min`,
  `degas_to_trace_clearance_min`, `copper_balance_window`),
- `value`: one of scalar {number, units} | expression {expr string} | piecewise
  [{when: "10 < A <= 14", value: 2.0}, …],
- `tier` (e.g. normal/advanced), `severity` (hard/preferred/advisory),
- `conditions` []: structured {param, op, value} with free-text fallback that forces
  `executability: manual`,
- `executability` (dimensional | density | structural | enumerated | manual),
- `routing` (cm | dfx | external | checklist), `lifecycle` {effective_rev, deprecated}.
- Expression grammar decision: a restricted arithmetic AST (numbers, one design
  variable like `A`, + − × ÷, comparisons). **Never raw eval.**

**2. Connectivity Graph** (`schemas/connectivity_graph.schema.json`):
- Node kinds: `die_pad`, `bump`, `substrate_net`, `ball`, `board_pin`; each with `id`,
  `name`, optional `xy`, optional `grid` (row/col for balls).
- Node attrs: `diff_partner`, `match_group`, `domain` (power domain), `interface`
  (e.g. UCIE_M0, HBM_CH2), `role` (signal/gnd/pwr/nc).
- Edges: typed connections between adjacent tiers. Revision metadata at graph root
  {design, rev, source_files[]}.

**3. Violation/Result** (`schemas/violation.schema.json`):
- `rule_id`, `severity`, `location` (physical {layer, x, y, extent} | logical
  {node_id, net}), `measured`, `required`, `delta`, `citation` (source anchor),
  `fix_hint` (optional, free text), `check_version`.

Also write `fixtures/golden/schema-examples/*.json` — one instance each, by hand.

## Research pack
- pydantic v2 for models; `jsonschema` for the canonical schema files. Keep JSON Schema
  as source of truth, pydantic generated or hand-mirrored with a test asserting parity.
- Expression handling: implement with Python `ast.parse` + node whitelist
  (Expression, BinOp, Compare, Num/Constant, Name from an allowed-vars set). Reject
  everything else. ~40 lines. Do not use `asteval`/`eval`.
- Deck versioning: semver per vendor per revision; decks live in git.
- Pre-commit golden-fixture guard: a repo hook that rejects staged changes matching
  `fixtures/golden/` unless env var `GOLDEN_EDIT=1` (human use only).

## the coding agent prompts

### Prompt 0.1 — repo scaffold
```
/goal Scaffold the pkgtk monorepo with CI so `make ci` runs ruff + pytest and a golden-fixture guard blocks edits under fixtures/golden/.
/context Phase 0. Read /README.md (repo root) for layout and standing constraints; copy the standing constraints into AGENTS.md.
/inputs README.md (root)
/constraints Python 3.11; deps: pytest, ruff, pydantic>=2, jsonschema, pre-commit. No src code beyond package skeleton. Makefile targets: ci, test, lint.
/deliverables pyproject.toml, Makefile, AGENTS.md, .pre-commit-config.yaml with golden-guard hook, src/pkgtk/__init__.py, empty dirs per layout with .gitkeep.
/verify `make ci` green on clean clone; staging a change to fixtures/golden/x.txt causes pre-commit failure.
```

### Prompt 0.2 — schema loaders + round-trip tests
```
/goal Implement pydantic models mirroring the three JSON Schemas, plus loaders and round-trip tests.
/context Phase 0. The human has authored schemas/*.schema.json and fixtures/golden/schema-examples/*.json. These are frozen — do not edit them.
/inputs schemas/rule_ir.schema.json, schemas/connectivity_graph.schema.json, schemas/violation.schema.json, fixtures/golden/schema-examples/
/constraints Never modify schemas/ or fixtures/golden/. Add a parity test: every pydantic model validates against its JSON Schema counterpart using jsonschema on dumped output. Implement the restricted expression AST validator described in docs/schemas.md (whitelist parser, no eval).
/deliverables src/pkgtk/schemas/{rule_ir.py,graph.py,violation.py,expr.py}, tests/test_schema_roundtrip.py, tests/test_expr_safety.py (must prove `__import__` / attribute access / calls are rejected).
/verify `make ci` green; round-trip on all three golden examples; expr tests reject 5 malicious strings and accept the piecewise examples.
```

### Prompt 0.3 — schema docs
```
/goal Generate docs/schemas.md documenting every field of the three schemas with one worked example each.
/context Phase 0. Source of truth is schemas/*.schema.json plus the golden examples.
/inputs schemas/, fixtures/golden/schema-examples/
/constraints Documentation only; no code changes. Pull field descriptions from the schema `description` keys; flag any field missing a description as a TODO list at the bottom (the human will fill those in).
/deliverables docs/schemas.md
/verify File exists, covers all fields, TODO list accurate.
```

## Cut line
If over budget: cut Prompt 0.3 (write docs by hand later). Never cut the fixture guard
or the expression-safety tests.
