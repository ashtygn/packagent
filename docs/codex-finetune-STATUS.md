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
| Stop-hook turn labeler → `~/.codex/labels/packagent-turns.jsonl` | `.codex/hooks.json`, `.codex/hooks/stop_label.py` | schema matches 0.144.6 `HooksFile`; script always exits 0; sync (0.144.6 skips async non-SessionEnd hooks); repo-root-anchored command path; no message content captured (NDA posture) |
| Adversarial review pass (19 confirmed findings fixed) | commit history | multi-agent review with per-finding reproduction; regression tests added for every grader hole (spam, incomplete sets, free-text, answer-key leak, crash paths) |
| Machine setup | `~/.codex/config.toml` marks this repo `trust_level = "trusted"` | skills/AGENTS.md render only for trusted projects |

## Resolved 2026-07-21 — auth was fine; it was binary selection + Windows portability

The earlier "auth is dead" symptom was a **which-codex** problem, not a token
problem. Three codex installs coexist on this machine:

- **MSIX / WindowsApps** (`Program Files\WindowsApps\...\codex.exe`) — sandboxed;
  returns "Access is denied" when driven programmatically. Do not target this one.
- **npm `@openai/codex`** (the `codex` on PATH the harness defaulted to) — **not
  actually installed here**, so `--codex-bin codex` didn't resolve.
- **Standalone** `%LOCALAPPDATA%\OpenAI\Codex\bin\<hash>\codex.exe` (v0.145.0-
  alpha.27) — **installed and logged in** ("Logged in using ChatGPT"; `auth.json`
  refreshed 2026-07-21). This is the runnable one.

Two Windows-portability bugs in the harness itself (both now fixed, `make ci` green):

1. **`make eval` default OUT hung on interactive `date`.** `$(shell date +...)` is
   valid on Unix but Windows `date` prompts. Fixed: `run_eval` owns the default
   output dir (`artifacts/eval-<timestamp>` stamped in Python); the Makefile no
   longer shells out to `date`, and passes `--out` only when `OUT=` is given.
2. **cp1252 decode crash → NoneType harness error.** `subprocess.run(text=True)`
   decoded codex's UTF-8 output with the Windows locale codec and died on the first
   non-cp1252 byte, recording every task as `harness error: AttributeError(...)`.
   Fixed: explicit `encoding="utf-8", errors="replace"` + `_coerce_text` on both
   the exec call and the `--version` call.

Also added: `run_eval._resolve_codex_bin` auto-finds the standalone binary when
`codex` isn't on PATH, so `make eval` works with no `--codex-bin` on this machine.

→ Just run (auth already live):

```bash
make eval          # 3-task smoke (~minutes, small quota) - codex auto-resolved
make eval-full     # full 28-task baseline (levers ON under artifacts/)
make eval-full OUT=/tmp/pkgtk-baseline   # stock-agent baseline (levers OFF)
```
If `codex` ever needs to be explicit:
`EVAL_ARGS='--codex-bin "%LOCALAPPDATA%\OpenAI\Codex\bin\<hash>\codex.exe"'`.

## Next (per plan §Phase 3, after baseline exists)

1. Rank failure modes from `report.md`; move ONE lever (skill/AGENTS.md/role);
   re-run; keep only non-regressing changes.
2. Model bake-off on the same suite: `--model gpt-5.6-terra` / `-luna`, reasoning
   efforts. Record codex version + model in every comparison.
3. First interactive in-repo session will prompt to trust `.codex/hooks.json` —
   accept it or the turn labeler silently won't run (hook trust is recorded as a
   content hash in `~/.codex/config.toml` hook state; re-trust after editing the
   hook). The project itself is already trusted on this machine.

## Notes / known limitations

- `make ci`'s `python` alias doesn't exist on this machine (pre-existing);
  `python3 -m ruff check . && python3 -m pytest` is the equivalent and is green.
- Plumbing was additionally validated with a local Ollama model (no auth path);
  local 7B models are not expected to pass tasks — that path validates the harness,
  not the agent.
- Skills duplicate some AGENTS.md content (APD recipes) — intentional for now; a
  future measured iteration may slim AGENTS.md (one lever at a time).
