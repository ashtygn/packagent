# DESIGN BRIEF — 3-minute pitch video (for the design agent)

You are producing a **3-minute (180 s) auto-playing video presentation**. The
voiceover script (timed scene-by-scene) is `docs/PITCH_SCRIPT.md` — build to it.
This folder has every image. **Everything below is verified real; do not invent a
number, and do not change a number that sits on a plot.** A signal-integrity
audience will catch a wrong figure instantly — that is the only way this loses.

## The one-sentence thesis
An AI agent reads a commercial field solver's physics, reasons about *why* an
IC-package power-delivery network fails spec, edits copper inside the Cadence
database, re-solves, and an independent referee — not the agent — decides if it's
fixed. Open source. On GitHub.

## Visual direction
- Dark, cinematic, engineering-serious. Background near-black `#0b0e14`, faint
  blueprint grid. Two accents only: **cyan `#39c5cf`** (the tool / the fix) and
  **amber `#e3b341`** (physics / warnings). Red `#f85149` = failure/violation.
- Big bold numerals, generous whitespace, no clutter, no stock icons. The plots
  ARE the visuals — frame them like hero shots, don't shrink them into corners.
- Motion: fade + gentle scale/Ken-Burns, animated counters, a thin top progress
  bar over the full 180 s, one animated pipeline diagram (scene 2), three red
  "REFUSED" stamps (scene 4). Smooth, not busy. It should feel *produced*.
- Tone the design serves: calm, certain, a little awed. Two deliberate silences
  (end of scene 1 and scene 3) — leave visual air there, no motion.

## THE ASSETS (this folder) — with the EXACT caption each must carry

| File | Shows | The number on it (do not alter) | Scene |
|---|---|---|---|
| `01_baseline_fail.png` | \|Z\| curve punching through the red mask line | **1824 Ω @ 6.15 GHz** vs 200 Ω limit, 4–7 GHz | S1 |
| `03_before_after.png` | red BEFORE + green AFTER \|Z\| curves | **1824 → 74 Ω (−96%)** | S3 (hero) |
| `04_round2_refused.png` | a refused fix: new band clean, old band broken | trade-off, ~1245 Ω regressed | S4 |
| `05_cavity_vs_siwave.png` | analytic cavity (cyan) vs SIwave solver (amber dots) | peak deltas **3.68% / 1.00%** | S5 (hero) |
| `06_ballmap_photonx1.png` | 2025-ball synthetic package | 2025 balls, 45×45 | S6 bg |
| `02_fixed_pass.png` | the fixed curve alone, mask green | optional B-roll | — |
| `07_pdn_z.png` | pkgtk's own PDN plot | optional B-roll | — |

## LOCKED FACTS (quote these exactly; provenance in parens)

- Rehearsal fix trajectory — **the plots depict THIS lane, use these numbers on
  the images**: baseline **1824.4 Ω @ 6.15 GHz** → fixed **74.1 Ω @ 6.00 GHz**,
  **−96%**, 4–7 GHz ≤200 Ω mask PASS. Referee `fixed: true`. (proven 3× clean-room,
  bit-identical.)
- Plane capacitance after fix: **61.0 pF** measured, **predicted before solving**
  (51 pF + fringing). Requirement was ≥30 pF. (plane-terminal measurement.)
- Physics receipt: our open-source cavity oracle vs Ansys SIwave, resonance peaks
  agree within **3.68%** and **1.00%**; solver's own output passes our physics
  gate (passivity σ_max 0.999973, reciprocity exact). (demo/graphs.)
- Determinism: **1.3×10⁻⁵** worst-case across the sweep; **3× reproducible,
  bit-identical**. Robustness: **physics matrix 4/4**, **error-injection 8/8**.
- Receipts on disk: **26 solver-signed result trees**; touchstones stamped
  "created by SIwave 2026 R1"; license checkouts logged.
- Round-2 refusal: **3 plausible fixes, 3 justified refusals, nothing shipped.**
- Stack: Cadence Allegro APD 24.1 (headless SKILL), Ansys SIwave 2026 R1
  (siwave_ng), pyedb, KLayout. Repo: **github.com/ashtygn/packagent**.
- Live footnote (optional ad-lib only, NOT on a plot): the live run measured
  **1856 Ω @ 6.14 GHz** — same story, different port pick. Keep it off the images
  so nothing contradicts the 1824 on the plots.

## GUARDRAILS — do NOT do these (each is a real failure mode)

1. **Do not mix the 1824 and 1856 numbers on the same visual.** The plots are the
   1824→74 lane. 1856 is a spoken footnote only.
2. **Never show or name customer/proprietary design data.** The loop ran on a
   Cadence-shipped-sample-derived file; the public package is the *synthetic*
   PHOTON-X1. No company names, no real product names, no internal hostnames/IPs.
3. **Do not claim it edits arbitrary full layouts.** It's a proof of concept; the
   edit vocabulary is reference planes and vias. "Closes the loop" is true;
   "replaces a layout engineer" is not — don't imply it.
4. **Do not claim the via-model limitation is solved.** (It's documented, not
   fixed — just don't mention it; never assert the opposite.)
5. No fabricated logos, no fake UI chrome, no invented benchmark bars. Every
   number shown must be in the LOCKED FACTS list above.

## Deliverable
A single self-contained, offline HTML (or a rendered MP4) that auto-plays 180 s,
scene timings per `PITCH_SCRIPT.md`. A reference build already exists at
`C:\scratch\open-demo\stage\pitch\presentation.html` — you may surpass it; keep the
facts identical.
