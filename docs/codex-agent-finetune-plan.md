# Fine-tuning the Codex agents — implementation plan

> **Scope note / assumption.** "The Codex agents codebase" is read here as the open-source
> **openai/codex** CLI (surveyed at commit `b9800de`, July 21 2026 — a ~100-crate Rust
> workspace). No other codex codebase exists on this machine (`~/.codex` is CLI state only).
> "Fine-tuning them" = producing fine-tuned model weights that *power* the Codex agents —
> specialized for our IC-package/substrate EDA verification workflows (pkgtk) — and plugging
> them back into the unmodified Codex harness. Every file path below is relative to the
> openai/codex repo unless prefixed with `packagent/`.

---

## 0. What "the agents" actually are (survey result)

Codex is not one agent. At this commit there are ~9 model-facing roles, each with its own
prompt and output contract, each separately fine-tunable because rollouts tag them by
`SessionSource`/`SubAgentSource`:

| # | Agent role | System prompt source | Output contract |
|---|------------|---------------------|-----------------|
| 1 | **Main coding agent** | per-model `base_instructions` in `codex-rs/models-manager/models.json` (fallback: `models-manager/prompt.md`) | tool calls + final message |
| 2 | Review subagent (`/review`) | `codex-rs/prompts/templates/review/rubric.md` | JSON `ReviewOutputEvent` |
| 3 | Guardian approval judge | `codex-rs/core/src/guardian/policy_template.md` | `{user_authorization, risk_level}` |
| 4 | Compaction summarizer | `codex-rs/prompts/templates/compact/prompt.md` | free-text handoff summary |
| 5 | Memory extraction (phase 1) | `codex-rs/memories/write/templates/memories/stage_one_system.md` | strict JSON |
| 6 | Memory consolidation (phase 2) | `.../consolidation.md` | file edits |
| 7 | Multi-agent workers (spawn roles default/explorer/worker) | role TOML layers, `codex-rs/core/src/agent/role.rs` | tool calls |
| 8 | Realtime voice intermediary | `prompts/templates/realtime/backend_prompt.md` | speech |
| 9 | (user-shell task — no model) | — | — |

**This plan targets role #1 (main coding agent) first**; the review agent (#2) is the natural
second target because its trajectories are short, single-shot, and graded by a JSON schema.
Everything else stays on stock models via existing per-role config keys (`review_model`,
`memories.extract_model`, etc.).

Key harness facts that constrain everything below (verified in source):

- **Responses API only.** `wire_api = "chat"` is a hard error
  (`codex-rs/model-provider-info/src/lib.rs`). A fine-tuned model must sit behind an
  OpenAI-Responses-compatible server (`POST {base}/responses`, SSE
  `response.output_item.done` / `response.completed`).
- **Full history resent every request** (`core/src/session/turn.rs`); no server-side state.
- **The system prompt and tool surface are *data*, not code** — they come from a per-model
  `ModelInfo` catalog (`models.json` or a `/models` endpoint). An unknown model slug falls
  back to degraded metadata: generic prompt, **no `apply_patch` tool**, no parallel tool
  calls (`models-manager/src/model_info.rs`). Controlling the catalog entry for our model is
  the single most important integration point.
- **Two tool conventions coexist.** The newest catalog models (gpt-5.6 family) are
  `tool_mode=code_mode_only`: nearly the whole tool surface collapses into one freeform
  `exec` tool taking raw JavaScript against TypeScript-typed `tools.*` declarations. Older
  models (gpt-5.5/5.2 style) use **direct mode**: `shell_command` function tool +
  `apply_patch` freeform tool (Lark grammar `'*** Begin Patch'…`) + `update_plan` etc.
  **We train against direct mode** — it matches what open-weight models already know and
  what the fallback/OSS path serves.
- **Tool outputs have exact, load-bearing shapes** the model conditions on:
  `Exit code: {n}\nWall time: {secs} seconds\n…Output:\n{truncated}`, middle-truncation with
  `Warning: truncated output (original token count: N)` markers, `apply_patch verification
  failed: …` error strings (`core/src/tools/mod.rs`, `utils/output-truncation`). Training
  data must byte-match these.

---

## 1. Strategic decision: which weights to fine-tune

### OpenAI-hosted fine-tuning is a dead end (verified July 2026)

- The platform is **winding down**: closed to new orgs since May 7 2026; orgs without recent
  ft-inference lost job creation July 2 2026; **all job creation ends Jan 6 2027**
  (developers.openai.com/api/docs/deprecations).
- Even inside the window, SFT/DPO cover only gpt-4.1 snapshots and RFT only o4-mini. **No
  GPT-5-family or codex model is fine-tunable** (`gpt-5-codex` model page: "Fine-tuning: Not
  supported").
- Unless our org happens to be grandfathered *and* a gpt-4.1-class model is acceptable,
  this path buys a deprecated capability. **Decision: do not build on it.**

### Primary track: open-weight model behind a Responses server

**Recommended base: `gpt-oss-20b` for the dev loop → `gpt-oss-120b` for production.**
Rationale:

- Trained natively on the **harmony** format, which mirrors the Responses API — so
  train-time and serve-time formats align with what Codex sends.
- First-class serving with tool calling intact: `vllm serve … --tool-call-parser openai
  --enable-auto-tool-choice` with **`/v1/responses` as the premier endpoint**; Ollama
  (≥0.13.4 speaks Responses natively, does harmony server-side) and LM Studio are built-in
  Codex providers (`codex --oss`).
- Mature LoRA/QLoRA recipes: OpenAI cookbook (TRL/PEFT, LoRA r=8 all-linear + MoE expert
  projections, MXFP4 dequantize), Axolotl gpt-oss configs (proper multi-turn masking),
  Unsloth (20b QLoRA in ~14 GB VRAM; 120b in ~65 GB; GRPO support).

**Alternative base (keep as a bake-off candidate): Qwen3-Coder(-Next).** Strongest open
coding-agent lineage (SWE-Gym/SWE-smith/Nebius fine-tunes all build on it), but serving
requires the `qwen3_coder` vLLM parser and a Responses-API shim in front of chat
completions — more format-drift surface against Codex. Run it only if gpt-oss baselines
disappoint.

Hardware envelope: 20b QLoRA fits one 24 GB GPU; 120b LoRA needs ~65 GB (1×H100/B200 or
2×A100-80); 120b MXFP4 inference fits one 80 GB GPU.

---

## 2. Phase-by-phase plan

### Phase A — Freeze the harness contract ("format lock")   *(≈1 week)*

The #1 documented failure mode for agent fine-tunes is silent drift between the training
format and what the harness actually sends. Codex gives us capture tools so we never
reconstruct prompts by hand.

1. **Pin the Codex version.** One binary/commit for the entire program. On any upgrade,
   re-run this phase (tool descriptions are partly dynamic; prompts live in a
   remotely-refreshed catalog).
2. **Stand up the capture rig** (three complementary taps, use all in dev, pick one for the fleet):
   - `CODEX_ROLLOUT_TRACE_ROOT=<dir>` — opt-in trace bundles containing the **exact
     serialized inference request/response JSON per model call**
     (`codex-rs/rollout-trace/`; reduce with `codex debug trace-reduce`).
   - `codex-rs/responses-api-proxy --dump-dir` — provider-side capture of every full
     Responses request/response pair, auth-redacted.
   - App-server `thread/start` with `experimentalRawEvents: true` — streams
     `rawResponseItem/completed` (raw Responses items) + `rawResponse/completed` (exact
     per-request usage) live over JSON-RPC; this is what Codex Cloud uses internally.
3. **Write the contract file** (checked into our training repo): base instructions text
   (start from `models-manager/prompt.md`, the fallback used for custom slugs), the direct-
   mode tool list with schemas regenerated from `core/src/tools/handlers/*_spec.rs`, the
   `apply_patch.lark` grammar, tool-output render strings, truncation policy
   (tokens/10000), `<environment_context>`/`<user_instructions>`/AGENTS.md fragment shapes.
   Verify with `codex debug prompt-input` that our understanding matches reality
   byte-for-byte.
4. **Decide the ModelInfo entry** for our future model now (it defines the training
   distribution): `slug=pkgtk-oss-…`, `tool_mode=direct`, `shell_type=shell_command`,
   `apply_patch_tool_type=freeform`, `use_responses_lite=false` (base instructions travel in
   the API `instructions` field), `supports_parallel_tool_calls=false` initially,
   `truncation_policy={tokens,10000}`, realistic `context_window`.

**Verify:** a captured request replayed through our renderer reproduces identical bytes.

### Phase B — Eval harness before any training   *(≈1–2 weeks, parallel with C)*

No training run starts until we can score a model automatically. Three suites:

1. **Domain suite (the reason we're doing this):** tasks generated from
   `packagent/benchmarks/` — seeded-defect designs (`mutations.py`, `cases.yaml`) where the
   agent must drive `pkgtk` CLIs to find/fix/verify. Graders are already deterministic:
   pkgtk's exit-code contract (0 clean / 1 findings / 2 usage / 3 internal), `make ci`
   green, benchmark catch-rates. ~50–100 tasks, held-out split fixed on day one.
2. **Generic regression suite (forgetting detector):** a fixed Terminal-Bench v2 subset +
   ~50 SWE-bench-Verified instances, run through Codex itself.
3. **Harness-compliance suite (format detector):** % invalid tool calls (unparseable JSON
   args, unknown keys — many handlers are serde `deny_unknown_fields`), % malformed
   `apply_patch` bodies (the classic failure: wrapping the patch in JSON), % harmony markup
   leaking into text, plus quick AIME/GPQA parity spot-checks per OpenAI's gpt-oss
   verification guidance.

**Runner:** the Python SDK (`sdk/python`) — it drives a single long-lived
`codex app-server --listen stdio://` process, observes the full ~70-notification stream,
and supports a pluggable `approval_handler`. Batch alternative:
`codex exec --json --skip-git-repo-check --sandbox workspace-write -C <task_dir>` (exit
code 1 ⇒ failed turn; note exec JSONL is lossy — fine for scoring, not for data capture).

**Baseline everything:** stock gpt-oss-20b, gpt-oss-120b (via `codex --oss` / vLLM), and the
current hosted default model as reference ceiling. Record pass rate, invalid-call rate,
tokens, wall-time per suite.

### Phase C — Data pipeline   *(≈2–3 weeks, the long pole)*

**C1. Task corpus.**
- *Domain:* extend `packagent/benchmarks/mutations.py` into a task generator — hundreds of
  seeded-defect variants across the 8 check families, ECO-diff tasks, escape-capacity and
  PDN tasks, plus tool-bring-up tasks scripted from `docs/tool-bringup-checklist.md`.
  Synthetic fixtures only (`fixtures/synthetic/`, never `fixtures/golden/` as mutation
  targets — goldens are read-only ground truth).
- *Generic:* import public verified-trajectory sets for capability floor — SWE-Gym
  (rejection-sampling FT recipe, +12–14 pts on SWE-bench in the original paper), SWE-smith,
  and Nebius' 32k RFT-filtered OpenHands trajectories — **re-rendered into the Codex
  direct-mode format** from Phase A (they supply tasks + reference solutions; where
  re-rendering is too lossy, regenerate trajectories natively instead, below).

**C2. Trajectory generation (teacher runs).**
- Teacher: **gpt-oss-120b stock** (raw CoT visible — `--oss` auto-sets
  `show_raw_agent_reasoning`) and/or the hosted default model (its reasoning arrives
  encrypted, so hosted-teacher examples train tool-calls/final-answers only — still
  valuable, but open-weight-teacher data is strictly richer).
- Fleet: Python-SDK controller, N parallel threads, `workspace-write` sandbox, per-task git
  worktrees, capture rig from Phase A on. Best-of-n per task via `thread/fork` from a shared
  prefix (fork + resample continuations); n=4 to start.
- **NDA gate (non-negotiable, from `packagent/AGENTS.md`):** the generation fleet runs only
  on repo-generated synthetic data. Customer/NDA design data never enters tasks, prompts,
  or datasets. Enforced structurally: the task generator is the only input source, and a
  scrub pass greps datasets for any path/netname outside the synthetic namespace.

**C3. Filtering (rejection sampling / filtered behavior cloning).**
Keep a trajectory iff: deterministic graders pass (patch applies, `make ci` green, pkgtk
exit codes as expected) AND turn status `completed` (no `TurnAborted`, no
`sandbox_denied`/`tool_error` per-item failures — labels come free from
`analytics`/`thread_history` schemas) AND no dropped-event warnings. Dedupe across forks
(forked threads duplicate parent history — key on `forked_from_id`).

**C4. Transform to training format.**
- Unit of training = **one captured model request → its sampled response** (from raw
  traces, so compaction, `<environment_context>` diffs, and history rewrites are already
  correct — never naively concatenate rollout lines; post-compaction context is replaced by
  `CompactedItem.replacement_history`).
- Render to harmony with `openai-harmony`; **loss masked to assistant tokens only** —
  analysis/commentary/final channels; tool outputs and all user/developer items masked
  (standard practice; Axolotl multi-turn masking supports this directly).
- Include compacted-continuation examples in their real shape (`SUMMARY_PREFIX`-prefixed
  summary as last item) so long-horizon behavior survives.
- Mix: ~60% domain trajectories, ~25% generic SWE trajectories, ~15% general instruction
  data (forgetting mitigation per "LoRA Learns Less and Forgets Less" + emergent-
  misalignment caution against narrow-only SFT).

### Phase D — SFT   *(≈1 week per iteration)*

- Framework: **Axolotl gpt-oss configs** (first choice: proper multi-turn assistant-only
  masking out of the box) or TRL per the OpenAI cookbook. Unsloth for the 24 GB-GPU dev loop.
- Starting hyperparameters (cookbook-derived): LoRA r=8–16, α=16, all-linear +
  `mlp.experts.gate_up_proj/down_proj`, lr 2e-4, MXFP4 dequantized for training, seq len
  32–64k (sample long-context examples across compaction boundaries rather than training at
  272k).
- Loop: train → merge (`merge_and_unload`) → Phase B suites → error taxonomy (which grader,
  which failure kind) → adjust data mix. Two to three iterations expected.
- **Ship gate:** domain suite ≥ target (set after baselining, e.g. ≥1.5× stock-120b pass
  rate), generic regression within 2 pts of stock, compliance suite ≥99% valid calls.

### Phase E — Integration back into Codex   *(≈3 days)*

1. Serve merged weights: `vllm serve <model> --tool-call-parser openai
   --enable-auto-tool-choice` (Responses endpoint); for MXFP4-class deploy perf, NVIDIA's
   QAT recipe closes the dequantize-train/requantize-serve gap. Laptop tier: Ollama.
2. Wire into Codex — one TOML stanza plus a catalog:

   ```toml
   [model_providers.pkgtk-ft]
   name = "pkgtk fine-tune"
   base_url = "http://gpu-box:8000/v1"
   wire_api = "responses"

   [profiles.pkgtk]
   model_provider = "pkgtk-ft"
   model = "pkgtk-oss-120b-v1"
   model_catalog_json = "/etc/codex/pkgtk-models.json"   # the Phase-A ModelInfo entry
   ```

   The catalog entry (or a `/models` endpoint on the vLLM box) carries our
   `base_instructions` (= the training system prompt) and tool capabilities. **Never let
   the model run on fallback metadata** — that silently swaps the prompt and removes
   `apply_patch`. (Slug-prefix inheritance is the fallback trick — `gpt-5.5-…` names inherit
   that family's metadata — but an explicit catalog is deterministic.)
3. Keep stock models for the other roles initially (`review_model`, guardian
   `codex-auto-review`, memory models) — they're independent config keys.
4. **Verification:** full Phase B run through the real CLI (`codex -p pkgtk exec …`), plus
   the compliance suite specifically watching for tool-calls-leaking-as-text (the classic
   parser-mismatch symptom).

### Phase F — Preference/RL stage   *(optional; only after SFT plateaus)*

Ordered by cost-effectiveness:

1. **Self-improvement rounds (more rejection sampling):** the *student* generates on the
   task corpus, deterministic graders filter, retrain. Cheapest on-policy gains; this is the
   SWE-Gym recipe.
2. **DPO pairs, mined for free from the harness:**
   - best-of-n fork winners vs losers on the same prefix (`thread/fork` gives shared-prefix
     branches natively);
   - user-denied vs eventually-approved tool calls (`codex.tool_decision` OTEL events,
     `final_approval_outcome` analytics labels);
   - error-then-success turn sequences.
   Note single-turn DPO granularity → use step/turn-level pairs (Step-DPO line of work).
3. **Full RL (GRPO)** only if a specific capability gap survives: Unsloth gpt-oss GRPO or
   SkyRL/rLLM, environment = the pkgtk task generator with exit-code rewards; the Codex
   **Stop hook** doubles as an environment intervention (a grader can *block* turn-end and
   inject corrective feedback — on-policy retry data). Budget realism: DeepSWE burned 6 days
   × 64 H100s; do not start here.

### Phase G — Continuous loop & ops

- **Live labeling:** a `Stop` hook (hooks feature is on by default) receives
  `transcript_path` (the rollout JSONL) + `turn_id` after every turn — a grader script
  writes labels next to rollouts. Per-turn auto-labels also via debug-build
  `CODEX_ANALYTICS_EVENTS_CAPTURE_FILE` (release builds ignore it).
- **Telemetry hygiene for the fleet:** release builds default-export metrics to Statsig
  (`ab.chatgpt.com`) and analytics to ChatGPT when ChatGPT-authed — set
  `[otel] metrics_exporter = "none"`, `analytics_enabled = false`, `[feedback] enabled =
  false` on generation machines, or run debug builds.
- **Versioning:** dataset snapshots + contract file + codex binary hash move together;
  `codex app-server generate-json-schema` pins the protocol per version. Retrain cadence:
  monthly or on codex-version bump, whichever first.
- Explicit human feedback (`/feedback` good_result/bad_result) uploads to OpenAI's Sentry —
  intercept the `feedback/upload` JSON-RPC method app-server-side if we want those labels
  locally.

---

## 3. Risks and mitigations

| Risk | Likelihood | Mitigation |
|---|---|---|
| Format drift between training data and harness | High (top documented failure) | Phase A capture-don't-reconstruct; byte-equality checks; compliance suite in every eval |
| Fallback ModelInfo silently degrades prompt/tools at inference | High if unmanaged | Explicit `model_catalog_json`; assert non-fallback at session start (warning event fires on fallback) |
| Catastrophic forgetting / narrow-FT side effects | Medium | LoRA (not full FT), 15% general-data mix, generic regression suite as ship gate |
| Hosted-teacher reasoning unavailable (encrypted) | Certain | Open-weight teacher for reasoning-bearing data; hosted teacher only for action supervision |
| NDA data leakage into datasets | Low but fatal | Synthetic-only task generator, structural allowlist, scrub pass (AGENTS.md rule) |
| Codex upgrades change prompts/tools mid-program | Medium | Version pinning; re-run Phase A on upgrade; catalog is remotely refreshed — pin `model_catalog_json` |
| gpt-oss-20b tool-call reliability on long tasks | Medium (documented) | 20b is dev-loop only; ship 120b; compliance gate |
| RL budget blowout | Medium | Phase F ordered by cost; rejection sampling before GRPO; fixed GPU-hour budget per round |

## 4. Milestone summary

| Milestone | Exit criterion |
|---|---|
| A. Format lock | Byte-identical replay of captured requests; contract file committed |
| B. Eval harness | Baselines recorded for stock 20b/120b + hosted reference on all 3 suites |
| C. Dataset v1 | ≥2k filtered domain trajectories + generic mix, rendered + masked, NDA-scrubbed |
| D. SFT v1 | Ship gate met on held-out suites |
| E. Integrated | `codex -p pkgtk` runs the tuned model with full tool surface; compliance ≥99% |
| F. (opt) Pref/RL | Measurable delta over SFT on domain suite at fixed budget |
| G. Ops loop | Hook-based labeling live; retrain runbook exercised once |

---

*Sources: subsystem maps of openai/codex @ b9800de (agents/prompts, rollout persistence,
model providers, tool surface, exec/SDK, telemetry — produced by parallel code-reading
agents with file:line citations, archived in the session workspace); OpenAI fine-tuning
docs & deprecation schedule, gpt-oss cookbook/recipes, vLLM gpt-oss recipe, SWE-Gym /
SWE-smith / SWE-RL / DeepSWE literature (URLs in the research archive), all
web-verified July 21 2026.*
