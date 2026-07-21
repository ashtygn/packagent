# PRESENTATION.md — AV / choreography guide for the 6am open demo

This is the "what software, when, showing what" manual. The **talk track** lives in
`docs/DEMO_SCRIPT.md` — say those words; this file only tells you which window is on
the projector and what your hands do. Read this at 5:30, run the pre-flight at 5:40.

---

## 1. Window inventory (pre-load all of these before the room enters)

| # | App | Pre-load state |
|---|-----|----------------|
| W1 | Browser, fullscreen (F11) | `C:\scratch\open-demo\stage\dashboard\index.html`, on panel P0 (hero). Ctrl+0 zoom baseline first, adjust for the projector, then F11. |
| W2 | `cmd.exe` (NOT PowerShell) | `cd /d C:\scratch\open-demo\stage`, run `demo.cmd` so the menu is showing. Consolas 20–24 pt, dark scheme, maximized. |
| W3 | KLayout — `C:\Users\MTVPhotonicsPackagin\AppData\Roaming\KLayout\klayout_app.exe` | Loaded with `stage\geom\dirty.gds`, Marker Browser docked showing `stage\geom\dirty.lyrdb` (4 markers). Fit view, then leave it. |
| W4 | APD GUI (only if you want the beat 7 GUI moment) | Open **your own** session off-camera before the room enters, load `stage\apdbeat\demo_with_pkgtk_markers.sip`, get Display > Status ready. **Never touch the pre-existing APD GUI session (PID 40920) or any process you did not start.** |
| W5 | (optional) agent terminal (Codex) | Open in the repo `C:\Users\MTVPhotonicsPackagin\packagent\packagent`, prompt idle — only for the agent-takeover closer. |

**Pin W1–W5 to taskbar slots 1–5** (drag icons into order, leftmost = W1). Then
`Win+1 … Win+5` switches deterministically — no Alt-Tab roulette on stage.

---

## 2. Choreography table

Dashboard panels (P0–P7, confirmed against the built dashboard): P0 hero · P1
generate · P2 verify **+ the 20/20 benchmark bar (beats 2 and 2B share P2)** ·
P3 cross-check · P4 ECO · P5 geometry · P6 physics · P7 closer (command typewriter —
serves beat 7 and the agent closer). Number keys 0–7 jump directly.

| Beat | On screen | You do | Audience looks at | Transition out |
|------|-----------|--------|-------------------|----------------|
| Settle-in | W1, panel P0 | Nothing. Hero panel up while people sit. | Headline stats: 2025 balls, 1591 nets, 792 pairs, 20/20, 145 tests, 19 s | Stay on W1 for cold open |
| Cold open | W1, P0 | Deliver the 30-second cold open from DEMO_SCRIPT | You, not the screen | `Win+2` to terminal |
| 1 Generate | W2 (+P1 next glance) | Type `1` in demo menu | `wrote ...graph_photonx1.json`, rc=0, ~0.3 s | `Win+1`, →P1, back `Win+2` |
| 2 Verify | W2 / P2 | Type `2` | `0 violation(s)` rc=0, then `bijection.multi_assignment @ A11` rc=1 | →P2 on W1, back to W2 |
| 2B Benchmark | W2 / P2 | Type `2B` | `clean=0 caught=20/20 exact_failures=[]` | stay on P2 (the 20-segment bar fills), back to W2 |
| 3 Cross-check | W2 / P3 | Type `3` | 2025/2025 clean; drift: `O14`, `D9 D8_N→D8_NX`, `Z19 dist=2.0` | →P3, back to W2 |
| 4 ECO diff | W2 / P4 | Type `4` | `"pair_broken": 1, "removed": 1` — A11_N / A11_P, IF0 | →P4, back to W2 |
| 5 Geometry | W2 → **W3** / P5 | Type `5`; then `Win+3` to KLayout, click the 4 markers in the Marker Browser | `4 violation(s) (4 hard)`, coverage `implemented=5 unimplemented=4 manual=2`; then real polygons at the violation coords | `Win+1` →P5, then `Win+2` |
| 6 Physics | W2 / P6 | Type `6` | Palmer 95.63%; peaks 7.143/10.101 vs 6.880/10.000 GHz (3.68% / 1.00%); ts_gate pass | →P6, back to W2 |
| 7 APD (opt.) | W2 → **W4** / P7 | Type `7`; optionally `Win+4`, Display > Status > DRC, click the 3 markers (2 typed pkgtk) | Markers alive inside the native tool; ECO diff `removed: CAS` | `Win+1` →P7 (closer) |
| Closer | W1 / P7 (or **W5**) | Closing line from DEMO_SCRIPT over P7's command typewriter; optional: `Win+5`, hand the repo to the agent live | Dashboard, or the agent typing | Done |

Rhythm per beat: **terminal runs → one line of talk → glance at the dashboard panel
→ back to terminal.** The dashboard is the visual anchor; W2 is where truth happens.

---

## 3. Screen / AV settings (do once at 5:30)

- **Projector:** `Win+P` → Duplicate. Settings > System > Display > Scale = 100%
  (125% if back row can't read; re-check terminal wrap afterwards).
- **Night light OFF:** Settings > System > Display > Night light = Off.
- **Notifications OFF / DND ON:** Settings > System > Notifications → Notifications
  Off **and** Do not disturb = On.
- **Kill chat apps:** fully quit Teams / Slack / Outlook from the system tray
  (right-click > Quit), not just the X button.
- **Taskbar:** Settings > Personalization > Taskbar > Taskbar behaviors →
  "Automatically hide the taskbar" (Win+number still works when hidden).
- **Wallpaper:** Settings > Personalization > Background → Solid color, dark.
- **Power:** plugged in; Settings > System > Power & battery → Power mode = Best
  performance; Screen and sleep → Never (for the session).
- **Terminal:** cmd Properties → Consolas 20–24 pt, dark scheme, ~50 rows, maximized.
- **Browser:** F11 fullscreen; Ctrl+0 then adjust zoom until the hero panel fills
  the projected frame; no extra tabs.

---

## 4. Failure choreography (muscle memory)

Every beat prints its own fallback path. If a beat dies: **stay on W2, `type` the
prebaked transcript, narrate from it, keep the dashboard as the visual.** Never
debug on stage.

| Beat | Fallback (`type` in W2) |
|------|-------------------------|
| 1 | `type C:\scratch\open-demo\stage\pkg\prebaked\01_generate.txt` |
| 2 | `...prebaked\02_verify_clean.txt` then `03_seed_defect.txt` then `04_verify_defect.txt` |
| 2B | `...prebaked\05_benchmark_20cases.txt` |
| 3 | `...prebaked\08_crosscheck_drift.txt` (clean: `07_crosscheck_clean.txt`) |
| 4 | `...prebaked\10_eco_diff.json` (report: `11_eco_report.md`) |
| 5 | `type C:\scratch\open-demo\stage\geom\check_dirty_transcript.txt` (+ `coverage_transcript.txt`); KLayout W3 still works — it reads files, not the run |
| 6 | `type C:\scratch\open-demo\stage\phys\cavity_vs_solver_12g_transcript.txt` (+ `cavity_vs_solver_transcript.txt`) |
| 7 | `type C:\scratch\open-demo\stage\apdbeat\readback_out.txt` + `type C:\scratch\open-demo\stage\apdbeat\eco\diff_A_B.json` |

**Two environment-dependent beats — pre-scripted skip lines:**

- **Beat 7** (needs the Cadence SPB 24.1 install + a license seat; self-skips):
  *"That beat needs an EDA seat that isn't free right now — here is the transcript
  of the identical run from earlier tonight, byte for byte."* Then the beat-7
  fallbacks above.
- **Beat 6 live re-solve** (optional, only if challenged "did you really run
  SIwave?"): needs `ANSYSEM_ROOT261` + `ANSYSLMD_LICENSE_FILE` set and a free seat;
  ~47 s. Skip line: *"The default beat needs no license at all — the receipt you
  just saw was solved headless on this machine tonight; transcript is on screen."*
  If you do run it: `PYTHONUTF8=1 python C:\scratch\open-demo\stage\phys\t6_extend_12g.py`
  — it timeboxes and skips cleanly on its own if no seat.

---

## 5. Rehearsal protocol — the 10-minute pre-flight at 5:40

1. **(1 min) Seat check, off-projector:** in W2:
   `if defined ANSYSEM_ROOT261 if defined ANSYSLMD_LICENSE_FILE (echo solver env OK) else (echo solver env MISSING)`
   — do **not** echo the variable values with the projector live (license server
   string stays off-screen). If you plan beat 7 live, run `demo.cmd 7` once now
   (~11 s) as the real seat test; if it self-skips, demote beat 7 to fallback mode.
2. **(2 min) Stray-GUI sweep:** `tasklist | findstr /i "allegro apd siwave klayout"`.
   Close only sessions **you** opened tonight. Leave the pre-existing APD GUI
   (PID 40920) and anything you don't recognize strictly alone.
3. **(1 min) Smoke test:** `demo.cmd 1` — 0.3 s, harmless, regenerates the graph in
   place. Confirms python + pkgtk + stage paths alive.
4. **(2 min) Dashboard sweep:** W1, F11, arrow-key through all eight panels (P0–P7)
   and back. If the projector machine struggles with animations, reload with
   `?still` appended to the URL (all final states render instantly). Park on P0.
5. **(2 min) Window pins:** confirm taskbar order W1–W5 = slots 1–5; press
   `Win+1 … Win+5` once each, end on `Win+1` (P0). Check W3 marker browser is
   docked and W4 (if used) has the .sip loaded.
6. **(2 min) Sit down, breathe, reread the 30-second cold open in DEMO_SCRIPT.**

**After the demo:** if you ran 2B, delete the generated report to leave the repo
as found: `del C:\Users\MTVPhotonicsPackagin\packagent\packagent\benchmarks\BENCHMARKS.phase1.md`.
