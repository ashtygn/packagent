# LOOP_DEMO — live agentic run: SIwave physics → reasoning → edit inside the .sip/.mcm

This is the live-demo recipe for handing the loop to a coding agent (Codex or any
coding agent) and watching it fix a package **because of what the solver said** — not
just run commands.

## What the audience sees

1. A real Cadence package database whose PDN violates an impedance mask.
2. The agent solves it headless in SIwave, reads the verdict JSON, and **reasons**:
   the 1824 Ω resonance + 0.84 pF plate capacitance mean the design has no working
   reference planes.
3. The agent computes plane dimensions from cavity physics, **edits the .mcm inside
   headless APD** (net-assigned copper on SUPPLY/GROUND, independently verified in a
   fresh APD session), states a numeric prediction, re-exports, re-solves.
4. The referee (`loop_check.py`) confirms: band mask **fixed** (peak −96%), and the
   plane-level measurement lands within ~20% of the agent's capacitance prediction.
5. If anything doesn't add up, the loop *refuses* to call it fixed — that's the
   point (see LIMITATIONS in PLAYBOOK.md for the live-discovered via-model case).

## Workspace prep (before the demo, ~1 min)

```powershell
mkdir C:\scratch\codex-run
copy <uprevved sample.mcm> C:\scratch\codex-run\design.mcm   # any package .mcm works
```
Set solver env in the agent's shell (see PLAYBOOK). Tools live in `demo/loop/`.

## The prompt (hand this to the agent verbatim)

> Read AGENTS.md and demo/loop/PLAYBOOK.md, then work in C:\scratch\codex-run.
> The package design.mcm must meet this PDN requirement: |Z| at the package port
> must stay ≤ 200 Ω across 4–7 GHz, and the power plane pair (once it exists) must
> show ≥ 30 pF plate capacitance measured at the plane terminals.
> Establish the baseline with the demo/loop tools, diagnose what the solver curve
> tells you, fix the package inside the Cadence database with apply_edit.py, and
> prove the fix with loop_check.py. Write a numeric PREDICTION.md before every
> re-solve. Never claim success the referee doesn't confirm.

Expected timeline: baseline ~2 min (translate+solve), reasoning ~1 min, edits ~20 s
(2 × apply_edit with independent verification), re-solve ~2 min, judgment seconds.
Total ≈ 6–8 minutes of genuine agentic engineering.

## Why this can't be faked

- Every edit is verified geometrically in a *separate* APD session before any solve.
- Every solve passes through the pkgtk physics gate (passivity/reciprocity) before
  its numbers are believed.
- `loop_check.py` computes fixed/regressed from the two verdicts — the agent cannot
  declare victory; the referee does.
- Every iteration directory is append-only evidence (design copy, XML, aedb,
  touchstone, verdict, prediction).
- The referee's full truth table is live-tested: `fixed:true` (round-1 fix),
  `fixed:false` without regression (round-2 refusals; also a single-plane
  deletion the physics proved harmless), and `regressed:true` (both planes
  deleted → the 1824 Ω resonance returned bit-identically and was caught).

## Dress rehearsal (clean-room, committed tools only — 2026-07-21 04:53–05:00)

The full prompt was executed start-to-finish in a fresh workspace using nothing but
this repo's committed tools, exactly as an agent would:

| Step | Command | Result | Wall |
|---|---|---|---|
| Baseline | `run_iteration ... --edit none --mask 4:7:200` | FAIL — peak 1824 Ω @ 6.1504 GHz, C=0.84 pF | 121 s |
| Prediction | PREDICTION.md written before solving | band collapse + 55–65 pF | — |
| Edit ×2 | `apply_edit add-plane` VDD/SUPPLY + VSS/GROUND | both `managed_count=1` verified | 8.2 s each |
| Fix solve | `run_iteration ... --baseline-verdict` | mask **PASS**, referee **`fixed: true`**, peak 1824→74.1 Ω (−96%) | 121 s |
| Plane C | `build_and_solve --port-layer SUPPLY --neg-layer GROUND` | **61.0 pF ≥ 30 pF PASS** (predicted 55–65) | 65 s |

Total ≈ 6.5 minutes. Robustness evidence: resize matrix 4/4 (C tracks 1/area to
2–8%, cavity-peak scaling to 0.5%, solver determinism 1.3e-5 worst-case),
error-injection 8/8 after one real tool bug the matrix itself caught and fixed
(via-verify nil deref → false negative). Full trails: `C:\scratch\codex-run\` and
`C:\scratch\loop-ws\` (local only — Cadence-sample derivatives).

## The round-2 refusal campaign (the strongest 5 minutes you can show)

After the round-1 fix, hand the agent a NEW requirement on top of the old one:

> Additional requirement: |Z| must also stay ≤ 100 Ω across 2.5–3.5 GHz. The
> round-1 mask remains in force. Iterate.

What happened when this was run (2026-07-21, receipts in `C:\scratch\codex-run\`):
the fixed design fails the new mask (3.40 GHz / 202 Ω). The agent tried the plane
lever across its whole range — 12 mm satisfied the NEW mask but relocated a
1245 Ω antiresonance into the OLD band (**referee refused**); 13 mm collapsed the
feed coupling entirely (plane edge left the via ring — C crashed 61→2.1 pF,
**refused**, and a new design rule was learned); 15 mm (max legal shrink) left the
curve numerically identical — proving the offending peaks are feed-structure
modes the plane lever cannot touch (**refused**). Terminal answer: requirement
conflict reported with the full lever map and root cause; **nothing shipped**.

Three plausible fixes, three materially justified refusals, one learned design
rule, zero silent wrongs. If the audience remembers one thing, make it this.

## Reference run (receipts)

A complete reference trajectory with all evidence lives in the loop workspace
(`C:\scratch\loop-ws\`, local only — it contains Cadence-sample derivatives):
baseline FAIL (188.7 kΩ / 1824 Ω) → plane fix → band FIXED (74 Ω, −96%) →
plane-level C = 61.0 pF vs 51 pF predicted → residual low-freq gap root-caused to
an import-model via-connectivity limitation with a triple-tested minimal repro
(see `C:\scratch\loop-ws\CONCLUSIONS.md`).
