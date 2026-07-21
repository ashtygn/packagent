# Fine-tuning the Codex agents for pkgtk — implementation plan (v2)

> **v2 direction (user decision, 2026-07-21):** keep the Codex agents on the **gpt-5.6
> family** ("Codex 5.6" — sol/terra/luna) and fine-tune them **behaviorally** — via the
> configuration surfaces the harness itself exposes — measured by a deterministic eval
> loop. No open-weight training. This supersedes v1's open-weight track (git history has
> it). Weight-level fine-tuning of the GPT-5 family is not offered by OpenAI anyway
> (gpt-5-codex model page: "Fine-tuning: Not supported"; the hosted FT platform is winding
> down entirely), so the configuration loop below is both the chosen and the only
> available fine-tuning mechanism for 5.6.

All openai/codex facts below were verified two ways: source survey at commit `b9800de`
and ground-truth dumps from the **installed binary, codex-cli 0.144.6** (the pinned
version for this program; live ChatGPT auth confirmed).

---

## 1. What we are tuning, and with what levers

Codex 5.6 through this harness means: default model `gpt-5.6-sol` (priority 1 in the
catalog; `tool_mode=code_mode_only`, `use_responses_lite=true`, 272k context, freeform
`apply_patch`, multi-agent v2, skills usage-instructions off). The agent writes
orchestration JavaScript against typed `tools.*` declarations rather than calling many
discrete tools — our instructions must work *with* that, not against it.

The behavioral tuning surfaces, in precedence order (all verified in 0.144.6):

| Lever | Where | What it does |
|---|---|---|
| Project config layer | `<repo>/.codex/config.toml` | Precedence 25 — overrides user config for anyone working in this repo |
| AGENTS.md | repo root (exists) | Injected as a user-role `<INSTRUCTIONS>` fragment every session |
| Repo skills | `<repo>/.agents/skills/<name>/SKILL.md` | Cataloged to the model (`## Skills` block); full body injected on `$name` mention or when the model opens it |
| Custom agent roles | `[agent_roles.<name>]` + role `config_file` TOML layer | Spawnable specialist subagents with their own `developer_instructions` |
| Hooks | `.codex/hooks.json` | Stop/PostToolUse hooks — deterministic graders in the loop; can block turn-end and inject corrective feedback |
| Per-role model routing | `review_model`, memory models, collab-mode masks | Pin cheaper/stronger models per agent role |
| Approval/sandbox policy | config + execpolicy prefix rules | Which commands run friction-free — directly shapes trajectories |

## 2. The fine-tuning loop

```
      ┌──────────────────────────────────────────────┐
      │ evals/: seeded-defect tasks (benchmarks/) +  │
      │ deterministic graders (pkgtk exit codes,     │
      │ make ci) + codex exec --json runner          │
      └───────────────┬──────────────────────────────┘
                      │  pass-rate, tool-error rate, tokens, wall-time
                      ▼
      score baseline → edit ONE lever (AGENTS.md / skill / role /
      config) → re-run suite → keep if better, revert if not → commit
```

This is measurable prompt/config optimization with the same rigor v1 reserved for weight
training: fixed task set, held-out split, one-variable-at-a-time, regression gate.

## 3. Phases

### Phase 1 — Eval harness (`evals/`)
- **Task generator**: seeded-defect agent tasks built from `benchmarks/` machinery
  (mutations across check families, ECO-diff tasks, template-compliance tasks). Each task
  = scratch workdir + `task.md` prompt + machine-readable expectation.
- **Graders**: deterministic, zero-LLM — pkgtk exit-code contract (0/1/2/3), expected
  violation `check` ids present, `make ci` green after agent edits, no golden-fixture
  touches (hard fail).
- **Runner**: `codex exec --json --skip-git-repo-check --sandbox workspace-write -C
  <workdir>` per task; parse the JSONL event stream (thread.started / item.completed /
  turn.completed); score with graders; also record compliance metrics (failed command
  items, declined items, token usage, wall time).
- Baseline stock gpt-5.6-sol on the suite before any lever moves.

### Phase 2 — Integration layer (the levers, checked in)
- `.codex/config.toml`: project defaults (model pin, reasoning effort, web-search off for
  determinism, custom `[agent_roles]`).
- `.agents/skills/`: domain skills distilled from AGENTS.md + docs — `pkgtk-verify`,
  `pkgtk-eco-diff`, `pkgtk-geometry-lint`, `apd-headless`, `siwave-headless`. Skills keep
  AGENTS.md lean (catalog + on-demand injection beats a wall of always-on text).
- `[agent_roles]`: `pkg-verifier` (runs verification suites, never edits sources),
  `eda-runner` (drives APD/SIwave headless recipes with the hard-won rules as
  developer_instructions). Roles inherit the parent model (gpt-5.6) by default.
- `.codex/hooks.json`: Stop hook → grader script writes per-turn labels next to rollouts
  (`session_id`, `turn_id`, transcript path arrive on stdin; feature `hooks` is on by
  default).
- `fixtures/golden/**` protection stays doubled: the AGENTS.md rule plus the existing
  pre-commit guard (eval tasks run in scratch workdirs outside the repo tree, so the
  graders themselves never see goldens).

### Phase 3 — Tuning iterations
Run suite → rank failure modes → move one lever → re-run. Ship gate per change: domain
pass-rate non-decreasing AND no new compliance regressions. Expected early levers, in
order: (1) skills for the two workflows the model gets wrong most, (2) AGENTS.md
tightening for code-mode phrasing, (3) role developer_instructions, (4) reasoning-effort
/ model-slug pin (sol vs terra vs luna bake-off on the same suite).

### Phase 4 — Ops
- `make eval` target; suite in CI-adjacent cadence (manual trigger — live model calls
  cost quota; never in `make ci`).
- Version pinning: codex-cli version + model slug + catalog snapshot
  (`evals/reference/models-catalog-<ver>.json`, dumped via `codex debug models`) recorded
  in every eval report; re-baseline on harness or model bump.
- Rollouts under `~/.codex/sessions` + Stop-hook labels form a growing corpus — if OpenAI
  ever opens fine-tuning for the 5.x family, v1's data pipeline design (git history)
  applies unchanged.

## 4. Status & risks

Executable entirely on this machine (live ChatGPT auth, codex-cli 0.144.6). Main risks:
eval runs consume plan quota (keep suites small, batch deliberately); ChatGPT-auth
backend serves only catalog models (fine for 5.6); prompt-injection surface of skills
(they're instructions, keep them imperative and small); one-lever-at-a-time discipline.
