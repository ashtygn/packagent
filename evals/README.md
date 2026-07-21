# evals/ — agent-eval harness for the Codex 5.6 tuning loop

Measures how well a Codex agent drives pkgtk on seeded-defect tasks. This is the
scoring half of the behavioral fine-tuning loop in
[docs/codex-agent-finetune-plan.md](../docs/codex-agent-finetune-plan.md): every
config/skill/instruction change must hold or improve the pass rate here.

## Run

```bash
make eval                    # 3-task smoke (1 per family) -> artifacts/eval-<ts>
make eval-full               # all 28 tasks (live quota - deliberate use only)
make eval OUT=/tmp/base      # OUTSIDE the repo tree = stock agent, no levers
python -m evals.run_eval --out /tmp/r --families diagnose --limit 3 --dry-run
```

Live runs call the real model through `codex exec`; the suite is **never** part of
`make ci`. `--dry-run` generates + self-validates tasks offline.

**Levers on vs off:** runs under the repo tree (`artifacts/...`) load the project
levers (.codex config, `.agents/skills`, AGENTS.md); runs elsewhere measure the
stock agent. The report header records `levers_active` — compare like with like.

## Task families

| Family | Agent must | Graded on (exact, recomputed) |
|---|---|---|
| `diagnose` (20) | run `pkgtk verify`, write `findings.json` | reported set == full violation set (missing AND spurious both fail); inputs untouched |
| `fix` (6) | repair additively-mutated `graph.json` | `pkgtk verify` exit 0; node/edge counts equal the clean design; config untouched |
| `ecodiff` (2) | run `pkgtk diff`, write `eco.json` | changed_nets and classes sets equal the real diff (typed lists required); inputs untouched |

Tasks are generated from `benchmarks/` machinery (`mutations.py` seeded defects)
and **self-validated at generation time**. Generation refuses a non-empty `--out`.

## Anti-gaming posture

The codex sandbox restricts *writes*, not *reads* — nothing near the task dir can
safely hold an answer key. Therefore `meta.json` stores only
`(family, mutation, input hashes)` and graders **recompute ground truth** from the
deterministic generator at grade time. Residual risk: a determined agent could
read the public generator source elsewhere on disk and re-derive answers; the
runner flags commands touching `../`, `meta.json`, or generator paths as
`n_suspect_commands` in every report row — treat nonzero as a contaminated run.

## Reports

Written incrementally after **every** task (a crash or Ctrl-C never discards paid
runs): `<out>/report.json` (grade reasons, command/failed/suspect counts, token
usage, wall time, `levers_active`) and `<out>/report.md`. Record codex version +
model with every comparison; re-baseline after codex or model bumps. Reference
catalog snapshot: `evals/reference/models-catalog-<version>.json`
(regenerate with `codex debug models`).

## Offline tests

`tests/test_eval_harness.py` proves the graders accept an oracle solution and
reject wrong, spammed, incomplete, free-text, cheating, and tampered outputs —
hermetic, runs in `make ci`.
