# LOOP_DEMO — live agentic run: SIwave physics → reasoning → edit inside the .sip/.mcm

This is the live-demo recipe for handing the loop to a coding agent (Codex, Claude
Code, any) and watching it fix a package **because of what the solver said** — not
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

## Reference run (receipts)

A complete reference trajectory with all evidence lives in the loop workspace
(`C:\scratch\loop-ws\`, local only — it contains Cadence-sample derivatives):
baseline FAIL (188.7 kΩ / 1824 Ω) → plane fix → band FIXED (74 Ω, −96%) →
plane-level C = 61.0 pF vs 51 pF predicted → residual low-freq gap root-caused to
an import-model via-connectivity limitation with a triple-tested minimal repro
(see `C:\scratch\loop-ws\CONCLUSIONS.md`).
