# evals/ — agent-eval harness for the Codex 5.6 tuning loop

Measures how well a Codex agent drives pkgtk on seeded-defect tasks. This is the
scoring half of the behavioral fine-tuning loop in
[docs/codex-agent-finetune-plan.md](../docs/codex-agent-finetune-plan.md): every
config/skill/instruction change must hold or improve the pass rate here.

## Run

```bash
make eval                                # full suite (28 tasks) -> artifacts/eval-run
make eval EVAL_ARGS="--limit 1"          # smoke: 1 task per family (3 live runs)
python -m evals.run_eval --out /tmp/r --families diagnose --limit 3 --dry-run
```

Live runs call the real model through `codex exec` and cost quota — the suite is
**never** part of `make ci`. `--dry-run` generates + self-validates tasks offline.

## Task families

| Family | Agent must | Graded on |
|---|---|---|
| `diagnose` (20) | run `pkgtk verify`, write `findings.json` | expected rule_id+location reported; inputs untouched |
| `fix` (6) | repair additively-mutated `graph.json` to verify-clean | `pkgtk verify` exit 0; node/edge counts restored; config untouched |
| `ecodiff` (2) | run `pkgtk diff`, write `eco.json` | expected net + change classes reported; inputs untouched |

Tasks are generated from `benchmarks/` machinery (`mutations.py` seeded defects)
and **self-validated at generation time** — the deterministic engine must catch the
seeded defect or generation fails. Grader-side data (`meta.json`) lives outside the
agent's `work/` directory.

## Reports

`<out>/report.json` (full rows: grade reasons, command counts, failed commands,
token usage, wall time) and `<out>/report.md` (summary table). Record the codex
version + model with every comparison; re-baseline after codex or model bumps.
Reference catalog snapshot: `evals/reference/models-catalog-<version>.json`
(regenerate with `codex debug models`).

## Offline tests

`tests/test_eval_harness.py` proves the graders accept an oracle solution and
reject wrong/cheating/tampered outputs — hermetic, runs in `make ci`.
