# pkgtk — standing constraints (apply to EVERY session)

1. Never modify anything under `fixtures/golden/**`. Those are human-authored ground
   truth. If a fixture looks wrong, STOP and report — do not "fix" it.
2. `make ci` (ruff + pytest) must be green before claiming done. Commit per green step.
3. Python 3.11+. Dependencies only from the phase README's allowed list.
4. No network calls at test time. Anything fetched from the web goes into
   `reference/` with a source URL header.
5. Schemas in `schemas/` are frozen per version. Needing a schema change = stop and
   report; the human bumps the version.
6. When uncertain between two interpretations of a spec, implement the one in
   `docs/*-spec.md` and flag the ambiguity in the PR notes. Never guess silently.

## Repo layout

```
CLAUDE.md                 # this file
Makefile                  # ci, test, lint targets
schemas/                  # rule_ir, connectivity_graph, violation (JSON Schema + pydantic)
src/pkgtk/                # ingest/ checks/ diff/ lint/ models/ oracles/ cli/
fixtures/golden/          # HUMAN-AUTHORED. Agents read-only.
fixtures/synthetic/       # generated test data (agents may regenerate)
reference/                # fetched specs/docs with source URLs
docs/                     # per-check semantics specs, schema docs
benchmarks/               # seeded-defect cases + auto-generated BENCHMARKS.md
```

## Dev setup

```
pip install -e .[dev]
pre-commit install
make ci
```

The pre-commit golden-guard hook rejects staged changes under `fixtures/golden/`
unless `GOLDEN_EDIT=1` is set (human use only).
