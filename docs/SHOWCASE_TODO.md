# SHOWCASE TODO — single source of truth (updated 2026-07-21, post PR #1 merge)

Legend: ☐ open · ☑ done · 🔴 blocker · [YOU]/[NM]/[agent] = owner.

## T-0 blockers — CLEARED 2026-07-21

- ☑ **Codex auth** — was never dead; standalone `%LOCALAPPDATA%\OpenAI\Codex\bin\`
  build is logged in (auth.json refreshed today). The "dead auth" was binary
  selection (MSIX blocked / npm absent) + two Windows harness bugs, both now fixed
  (UTF-8 decode + Python-owned timestamp; codex-bin auto-resolves). See
  codex-finetune-STATUS.
- ☐ [YOU] First interactive Codex session in the repo will prompt to trust
  `.codex/hooks.json` — **accept it** or the turn labeler silently won't run.

## Track A — the Codex live loop demo (the centerpiece)

- ☑ Loop toolkit built, hardened, referee-tested (`demo/loop/`, commits b2782e6…fe30f82)
- ☑ Dress-rehearsed clean-room ×3, bit-identical results; round-2 refusal campaign done
- ☑ Prompt + recipe + receipts in `demo/loop/LOOP_DEMO.md`; beat 8 in DEMO_SCRIPT.md
- ☑ Visual pack from real solves: `C:\scratch\open-demo\stage\loop-visuals\`
- ☐ 🔴 [YOU after auth] **Run the LOOP_DEMO prompt through REAL Codex once** (not a
  a scripted stand-in) — fresh workspace, committed tools only. Budget ~10 min + one
  retry. This is the only untested link in the chain: the loop works, Codex-the-
  driver hasn't touched it yet.
- ☐ [NM] Watch that run; if Codex stumbles on tool discovery, decide whether a
  `siwave-sip-loop` skill is the next single-lever change (measured via the eval
  suite — don't add it blind; AGENTS.md already routes to PLAYBOOK.md).

## Track B — Codex tuning/eval (NM's harness, now merged)

- ☑ Eval harness: 28 self-validating tasks, deterministic graders, 19 adversarial
  findings fixed, 12 tests in `make ci` (157 green)
- ☑ Project config + `pkg-verifier`/`eda-runner` roles + 3 skills verified rendering
- ☑ Stop-hook turn labeler (NDA-safe, no message content)
- ☐ [YOU after auth] `make eval` 3-task smoke, then `make eval-full` (levers ON)
  and `make eval-full OUT=/tmp/pkgtk-baseline` (levers OFF) → first real baseline
- ☐ [NM] Rank failure modes from report.md; one lever per iteration; then the
  model bake-off (gpt-5.6-terra/-luna)
- ☐ [NM] Extend the task suite with loop-class tasks (diagnose-from-verdict-JSON,
  predict-then-edit) once Track A's first real run shows the failure surface

## Track C — the open showcase (PHOTON-X1) — READY

- ☑ 8-beat demo, `demo.cmd all` re-regressed green tonight (transcript:
  `stage\transcripts\final_regression.txt`)
- ☑ Dashboard (P0–P7), graphs, DEMO_SCRIPT + PRESENTATION choreography
- ☑ APD GUI (marker db) + SIwave GUI (solved 12 GHz project) staged on taskbar
- ☐ [YOU] 10-min pre-flight from PRESENTATION.md §5 before the room fills
  (includes: close the stray "Untitled" SIwave that's still holding a seat)
- ☐ [YOU] Decide beat 7 (APD live) in or out; both staged

## Track D — hygiene / policy (pre-public-flip)

- ☑ Repo scrubbed (license IPs/hostnames placeholdered), artifacts double-ignored,
  Cadence-derivative binaries kept local-only
- ☐ [YOU] History decision before making the repo public: old commits carry a
  personal-github-username association in PHASE-NOTES blobs — squash/orphan or accept
- ☐ [YOU] EULA question (Cadence/Ansys benchmark-publication clauses) before any
  public post of solver agreement numbers — conservative default: synthetic-only
  numbers public (PHOTON-X1 track is already clean)
- ☐ [NM/agent] Reconcile skill↔AGENTS.md duplication ONE lever at a time via evals
  (their STATUS notes this; don't hand-edit both sides at once)

## Parked (post-showcase, from the moonshot plan)

- M1 cassette layer (registry-keyed tool cassettes) — the loop's runners are its substrate
- .sip→EDB ALinks license ticket (server lacks al4apd; IPC-2581 bridge is the workaround)
- Via-galvanic-connectivity cross-check in PowerSI / HFSS 3D Layout
- UCIe/JEDEC spec-exact maps (corporate email + legal)
