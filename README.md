# pkgtk — 100-Hour Build Plan

One toolkit, four wedges, open tooling only. Ball-map verification + ECO diff (Pillar 2),
package-lint geometry checker (Pillar 1), SI/PI model validators (Pillar 3), and the
non-neural tier-0 oracles (Pillar 4) — all on three shared schemas.

## The execution model

Your hours go to **schemas, golden fixtures, and domain judgment**. Claude Code writes
parsers and engines against tests you author. The safety rule is the thesis of the whole
project:

> **No agent-written component merges without a golden fixture you hand-computed.**
> You are the oracle in your own verify-repair loop.

## Hour ledger

| Phase | Name | Hours | Cumulative |
|-------|------|-------|------------|
| 0 | Foundation (schemas + repo) | 5 | 5 |
| 1 | Ball-map verifier + ECO diff | 20 | 25 |
| 2 | package-lint geometry checker | 22 | 47 |
| 3 | SI/PI validator stack | 15 | 62 |
| 4 | LLM layer | 12 | 74 |
| 5 | Wow tier (escape / template / PDN) | 10 | 84 |
| 6 | Integration + launch artifact | 8 | 92 |
| — | Buffer (you WILL spend it) | 8 | 100 |

When a phase overruns: **cut scope, never schedule.** Every phase ends demoable.

## Phase gating — hard rule

You may not start phase N+1 until phase N's **Exit Gate** checklist is fully green.
Each phase README lists its Entry Gate (what it consumes from prior phases) and Exit
Gate (what must pass). The gates are `make ci` targets, not vibes.

## Hour Zero — before Phase 0

Read your employment agreement. Decide: public repo from day one, or private until
cleared. Do all work on a personal machine. One hour, finally spent. This is the entry
gate to Phase 0 and it is not optional.

## Claude Code prompt convention

Every delegated task uses this template. One prompt = one session. Paste verbatim,
fill brackets.

```
/goal <one-sentence outcome>
/context <phase, what exists, which docs to read first>
/inputs <schemas, fixtures, reference files available in-repo>
/constraints <allowed deps; forbidden actions; style rules>
/deliverables <exact files + tests to produce>
/verify <exact commands that must pass before claiming done>
```

Standing constraints that apply to EVERY session (put them in CLAUDE.md at repo root):

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

## Repo layout (created in Phase 0)

```
pkgtk/
  CLAUDE.md                 # standing constraints above
  Makefile                  # ci, demo, bench targets
  schemas/                  # rule_ir, connectivity_graph, violation (JSON Schema + pydantic)
  src/pkgtk/                # ingest/ checks/ diff/ lint/ models/ oracles/ cli/
  fixtures/golden/          # HUMAN-AUTHORED. Agents read-only.
  fixtures/synthetic/       # generated test data (agents may regenerate)
  reference/                # fetched specs/docs with source URLs
  docs/                     # per-check semantics specs, schema docs
  benchmarks/               # seeded-defect cases + auto-generated BENCHMARKS.md
```

## Doctrine (why the build is shaped this way)

- Deterministic core, LLM shell. The LLM appears only in Phase 4, only at ingestion
  seams, always behind a human-confirm step and a paranoia battery.
- Verification before generation. Every wedge is read-only analysis — bottom rung of
  the trust ladder, adoptable day one.
- Flagged gap = fine. Silent wrong = fatal. Asymmetric metrics everywhere: precision
  gates releases; recall may lag if misses are loudly flagged.
- The schemas are the land-grab. They ship first and they are authored by you.
