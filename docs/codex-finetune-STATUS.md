# Codex 5.6 fine-tuning plan — execution status

Tracks execution of [codex-agent-finetune-plan.md](codex-agent-finetune-plan.md) (v2).
Updated 2026-07-21.

## Done

| Item | Where | Verified how |
|---|---|---|
| Codex CLI pinned | codex-cli **0.144.6** (npm `@openai/codex`) | `codex --version`; catalog snapshot at `evals/reference/models-catalog-0.144.6.json` (`codex debug models`) |
| Plan v2 (behavioral tuning, gpt-5.6) | `docs/codex-agent-finetune-plan.md` | — |
| Eval harness: 28 self-validating tasks (20 diagnose / 6 fix / 2 ecodiff), deterministic graders, `codex exec --json` runner, `make eval` | `evals/` | `tests/test_eval_harness.py` (oracle passes, cheating/tampering fails) in `make ci`; `--dry-run` full generation |
| Project config layer + specialist roles (`pkg-verifier`, `eda-runner`) | `.codex/config.toml`, `.codex/agents/*.toml` | config parses, zero startup warnings (`codex doctor`, `codex debug prompt-input` stderr) |
| Repo skills: `pkgtk-verify`, `pkgtk-eco-diff`, `apd-headless` | `.agents/skills/` | skills catalog confirmed in model-visible context via `codex debug prompt-input` (needs project trust, see below) |
| Stop-hook turn labeler → `~/.codex/labels/packagent-turns.jsonl` | `.codex/hooks.json`, `.codex/hooks/stop_label.py` | schema matches 0.144.6 `HooksFile`; script always exits 0 |
| Machine setup | `~/.codex/config.toml` marks this repo `trust_level = "trusted"` | skills/AGENTS.md render only for trusted projects |

## Blocked — needs one user action

**Codex auth is dead on this machine.** Live runs fail with *"Your access token could
not be refreshed because your refresh token was already used. Please log out and
sign in again."* A 3-task smoke (`make eval EVAL_ARGS="--limit 1"`) confirmed the
runner works end-to-end up to the model call (tasks generated, codex spawned, JSONL
parsed, graders produced correct failure reasons).

→ Run **`codex logout && codex login`** (ChatGPT sign-in), then:

```bash
make eval EVAL_ARGS="--limit 1"     # 3-task smoke (~minutes, small quota)
make eval                            # full 28-task gpt-5.6-sol baseline
```

## Next (per plan §Phase 3, after baseline exists)

1. Rank failure modes from `report.md`; move ONE lever (skill/AGENTS.md/role);
   re-run; keep only non-regressing changes.
2. Model bake-off on the same suite: `--model gpt-5.6-terra` / `-luna`, reasoning
   efforts. Record codex version + model in every comparison.
3. First interactive in-repo session will prompt to trust `.codex/hooks.json` —
   accept it or the turn labeler silently won't run.

## Notes / known limitations

- `make ci`'s `python` alias doesn't exist on this machine (pre-existing);
  `python3 -m ruff check . && python3 -m pytest` is the equivalent and is green.
- Plumbing was additionally validated with a local Ollama model (no auth path);
  local 7B models are not expected to pass tasks — that path validates the harness,
  not the agent.
- Skills duplicate some AGENTS.md content (APD recipes) — intentional for now; a
  future measured iteration may slim AGENTS.md (one lever at a time).
