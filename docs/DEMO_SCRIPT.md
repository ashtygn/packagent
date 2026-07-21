# pkgtk 6am Open Demo Script

Driver: `C:\scratch\open-demo\stage\demo.cmd` (interactive menu, or `demo.cmd <beat>`
for one beat: `1 2 2B 3 4 5 6 7 all`). The driver sets UTF-8 itself (`chcp 65001` +
`PYTHONUTF8=1`), never aborts on the expected exit-code-1 "findings" results, and
prints every command before running it plus a prebaked fallback path after it.
If anything misbehaves live, `type` the fallback transcript and keep talking.

All wall times below were measured on this machine during the dry run (every beat
run end-to-end through the driver, cold interpreter each time).

---

## 30-second cold open (say this before touching the keyboard)

"Everything you are about to see is open-source-safe. There is no customer data,
no proprietary design, nothing under NDA anywhere in this demo. The package you
will watch being checked is generated live, on this machine, by the tool's own
seeded synthetic generator -- 2025 balls, deterministic, byte-stable, seed 2025.
The manufacturing rules are an open, IPC-cited deck. The one commercial artifact
in the whole show is a receipt: a SIwave field-solver result computed on a plane
pair we built 100% from scratch in code -- our structure, zero design data -- and
the tool's own physics oracle predicts that solver's resonances to within a few
percent. Every check you will see runs twice: once on a clean build to prove zero
false positives, once on seeded defects to prove exact catches. Nothing here is a
mock-up, and every number is reproducible from a seed."

---

## Beat 1 -- Generate PHOTON-X1 ("a 2025-ball package in a quarter second")

**Say:** "First, the data source. This is `pkgtk.synth.ballmap_gen` -- the tool's
own generator -- building PHOTON-X1: a 45-by-45 grid, 2025 balls, 1591 nets,
792 differential pairs, four interfaces, 0.8 millimeter pitch. Seed 2025.
Run it twice and the JSON is byte-identical. This is the design everything else
in the demo runs against, and it did not exist two hundred milliseconds ago."

**Type:** `demo.cmd` then `1`

**Expect (0.29 s measured; core generate 21 ms):** the generation story --
2025 balls (1590 signal / 399 gnd / 36 nc), 1591 nets, 1590 die pads,
4 interfaces IF0-IF3, 3579 edges, 0.8 mm pitch -- then
`wrote ...graph_photonx1.json` + `runconfig_photonx1.json`, rc=0.

**Fallback:** `type C:\scratch\open-demo\stage\pkg\prebaked\01_generate.txt`

---

## Beat 2 -- Verify ("zero false alarms first, then one seeded defect")

**Say:** "The honesty doctrine, part one. Before we show a catch, we show the
false-positive gate: the clean build verifies to exactly zero violations --
exit code 0. Then we seed exactly one defect from the benchmark registry:
ball A11 is a signal ball that also gets strapped to ground -- the classic
ground-repurpose edit. Re-verify: exactly one violation, named, at A11.
Exit code 1 here means 'ran fine and found something' -- findings are success,
never a crash."

**Type:** `2`

**Expect (1.13 s measured, three commands):**
`PHOTON-X1 rev A: 0 violation(s)`, rc=0; the seeder printing
`expected catch: bijection.multi_assignment @ A11`; then
`PHOTON-X1 rev A-defect1: 1 violation(s)` / `[hard] bijection.multi_assignment @ A11`, rc=1.

**Fallback:** `type C:\scratch\open-demo\stage\pkg\prebaked\02_verify_clean.txt`
(also `03_seed_defect.txt`, `04_verify_defect.txt`)

---

## Beat 2B -- The 20-case benchmark ("the honesty doctrine, in one line")

**Say:** "Don't take one seeded defect's word for it. The repo ships a benchmark:
twenty defect classes -- swaps, drops, duplicate assignments, broken pairs --
each seeded into a fresh build and verified. The bar is exact: every case must be
caught with the exact expected violation, and the clean build must stay at zero.
One and a half seconds: clean equals zero, caught twenty of twenty, exact
failures empty. That line is regenerated from seeds, not curated."

**Type:** `2B`

**Expect (1.57 s measured):** `clean=0 caught=20/20 exact_failures=[]`, rc=0,
then the driver's cleanup note.

**Post-demo cleanup (the driver prints this too):** the benchmark writes a
generated report into the repo -- afterwards run
`del C:\Users\MTVPhotonicsPackagin\packagent\packagent\benchmarks\BENCHMARKS.phase1.md`
to leave the repo as found.

**Fallback:** `type C:\scratch\open-demo\stage\pkg\prebaked\05_benchmark_20cases.txt`
(the generated report is prebaked at `prebaked\BENCHMARKS.phase1.md`)

---

## Beat 3 -- Pin-map cross-check ("the hand-maintained spreadsheet vs the database")

**Say:** "Every packaging team maintains a pin-map spreadsheet by hand, and every
team has been burned by it. This emits the pinlist as a real XLSX -- 2025 rows --
plus a copy with three planted errors: a one-character net typo, a deleted row,
and a two-millimeter coordinate slip. Clean sheet against the graph: 2025 out of
2025, zero findings. Drifted sheet: exactly three findings, one per category,
each named with its ball. This is the check that runs on every spreadsheet
revision before it goes to the test house."

**Type:** `3`

**Expect (1.81 s measured, three commands):** the emitter listing the 3 seeded
errors; clean table all-OK ending `CLEAN -- DB and sheet agree (0.21s)`, rc=0;
drift table with `missing in sheet 1 / net mismatches 1 / coord mismatches 1`,
detail lines `O14`, `D9: DB='D8_N' sheet='D8_NX'`,
`Z19: ... dist=2.0`, `3 finding(s)`, rc=1.

**Fallback:** `type C:\scratch\open-demo\stage\pkg\prebaked\08_crosscheck_drift.txt`
(also `07_crosscheck_clean.txt`, `06_make_pinmap.txt`, both `.json` twins)

---

## Beat 4 -- ECO diff ("cut a diff-pair partner, the tool names both halves")

**Say:** "Revision B of this design lost one net: A11_N, the negative half of a
differential pair. Small enough that nobody spots it by eye in 1591 nets. The
semantic diff comes back with exactly two rows: A11_N removed, and A11_P flagged
as a broken pair naming its missing partner -- and silence on the other 1589
nets. Same result as JSON for machines and as a markdown ECO report for humans."

**Type:** `4`

**Expect (1.23 s measured, three commands):** the rev-B builder; JSON with
`"summary": {"pair_broken": 1, "removed": 1}`, both IF0, rc=1; then the markdown
report ending in the two-row changes table, rc=1.

**Fallback:** `type C:\scratch\open-demo\stage\pkg\prebaked\10_eco_diff.json`
(report: `11_eco_report.md`, builder: `09_make_revb.txt`)

---

## Beat 5 -- Geometry lint ("open rules, planted defects, and an honest coverage table")

**Say:** "Now geometry. The generator writes two GDS substrates: one clean, one
with exactly four defects planted by a manifest -- a thin trace, a tight gap, a
degas-clearance hit, and copper too close to the edge. The rule deck is open and
IPC-cited, not mined from anyone's design. Clean: zero violations. Dirty: exactly
four, each with measured versus required and coordinates -- four for four against
the manifest. And then my favorite part, the honesty table: the tool prints which
deck rules it actually executes -- five implemented, four unimplemented, two
manual -- so a rule it cannot run is never a silent pass."

**Type:** `5`

**Expect (1.21 s measured, four commands):** generator listing the 4 planted
defect parameters; `0 violation(s) (0 hard)`, rc=0; `4 violation(s) (4 hard)`,
rc=1 (ground truth: `manifest.json`); coverage table ending
`implemented=5 unimplemented=4 manual=2`, rc=0. Note the check also announces the
one rule it skips (`SUB.TRACE.WIDTH.MIN.SIGNAL.ADV`, non-scalar) -- out loud,
never silently.

**Optional click:** KLayout with the markers --
`C:\Users\MTVPhotonicsPackagin\AppData\Roaming\KLayout\klayout_app.exe C:\scratch\open-demo\stage\geom\dirty.gds -m C:\scratch\open-demo\stage\geom\dirty.lyrdb`
(4 clickable violation markers in the report browser).

**Fallback:** `type C:\scratch\open-demo\stage\geom\check_dirty_transcript.txt`
(also `check_clean_transcript.txt`, `coverage_transcript.txt`, `gen_transcript.txt`)

---

## Beat 6 -- Physics ("the closed-form oracle vs a commercial field solver")

**Say:** "Last technical beat, and it is a receipt, not a claim. Earlier tonight
we built a 10-by-10-millimeter power plane pair 100% from scratch in code --
our structure, zero design data -- and solved it headless with SIwave. Here the
tool's closed-form cavity-resonator oracle goes head-to-head with that solver
output. Low frequency: the raw curves differ by about 19 percent, and the tool
explains why quantitatively -- fringing capacitance; apply the standard Palmer
correction and agreement is 95.6 percent, with the capacitance residual at 1.5
percent. Then the extended sweep to 12 gigahertz: the oracle predicts the plane
resonances at 7.14 and 10.10 gigahertz; the solver measured 6.88 and 10.00 --
3.7 and 1.0 percent off, from a formula that costs microseconds. And the tool's
touchstone gate signs off the solver file itself: passive, reciprocal, sane."

**Type:** `6`

**Expect (1.18 s measured, two commands):** the 1 MHz-1 GHz |Z11| table; `Palmer
fringing-corrected residual vs solver: 1.47%` and `low-freq agreement after
Palmer correction: 95.63%`; ts_gate block `decision: pass`,
`sigma_max=0.999973`, `reciprocity ... 0.0`; then the 12 GHz run with
`cavity peaks: 7.143 / 10.101 GHz`, `siwave peaks: 6.880 / 10.000 GHz`,
deltas `3.68%` / `1.00%`, rc=0 both.

**Optional live re-solve (only if asked "did you really run SIwave?"):**
`PYTHONUTF8=1 python C:\scratch\open-demo\stage\phys\t6_extend_12g.py` rebuilds
the structure and re-solves 601 points to 12 GHz headless -- measured 46.8 s
total (build 12.9 s + solve 33.9 s) with a 400 s timebox and clean skip if the
solver or a license seat is unavailable. Requires `ANSYSEM_ROOT261` and
`ANSYSLMD_LICENSE_FILE` (site license server) set in the session. Transcript:
`t6_transcript.txt`.

**Fallback:** `type C:\scratch\open-demo\stage\phys\cavity_vs_solver_12g_transcript.txt`
(also `cavity_vs_solver_transcript.txt`)

---

## Beat 7 (optional) -- APD round trip ("shown, not shipped")

**Provenance -- say it verbatim:** "This design is Cadence's own shipped
getting-started sample from the SPB 24.1 install -- shown from a licensed local
install, never redistributed, and not customer data."

**Say:** "The tool talks to real EDA software in both directions. Watch two
things, all headless. One: a fresh APD session reloads a design we previously
injected findings into, and reads back three DRC markers -- two of them typed
'pkgtk' -- so our findings live inside the native tool and survive a save-reload
round trip. Two: the ECO chain on a real database -- extract connectivity, build
the graph, verify, then a real SKILL ECO deletes net CAS in headless APD,
re-extract, and the diff comes back with exactly one row: removed, CAS."

**Type:** `7` (the driver skips cleanly with fallback paths if Cadence SPB 24.1
is not installed)

**Expect (10.9 s measured):** `DRC markers found on reload: 3` /
`pkgtk-typed markers: 2`; then the ECO narration `ECO-1: deleted one routed
cline of net "CAS"` / `ECO-2: deleted logical net "CAS"`, `pkgtk verify rc=1`,
and the diff JSON `"summary": {"removed": 1}` with net `CAS`, rc=1.
Beat 2 of the chain byte-resets revB from revA every run -- deterministic,
safe to re-run all day.

**Live-GUI variant:** open
`C:\scratch\open-demo\stage\apdbeat\demo_with_pkgtk_markers.sip` in APD,
Display > Status > DRC, click through the same 3 markers.

**Fallback:** `type C:\scratch\open-demo\stage\apdbeat\readback_out.txt` and
`type C:\scratch\open-demo\stage\apdbeat\eco\diff_A_B.json`
(provenance + expectations: `apdbeat\README.txt`)

---

## Closing line

"Everything you saw was generated from a seed on this machine -- which means you
can hand this exact demo to anyone: no NDA, no data room, no redactions. The
checks are open, the benchmark is open, the physics oracle is open, and where we
leaned on commercial tools we showed you receipts, not slides. Point it at a real
design and the only thing that changes is the adapter."

---

## Pre-demo checklist (run at 5:40)

1. **Terminal:** one plain `cmd.exe` window (not PowerShell -- the PS 5.1 `>`
   UTF-16 landmine is why the driver is a `.cmd`), Consolas 18 pt or larger,
   ~50 rows, `cd /d C:\scratch\open-demo\stage`, then run `demo.cmd`.
2. **Smoke test:** `demo.cmd 1` (0.3 s, harmless, regenerates the graph in
   place) to confirm python + pkgtk + stage paths are alive.
3. **Beat 7 only:** needs the local Cadence SPB 24.1 install and a
   SiP_Layout_Bundle_1 seat; each sub-beat spawns its own fresh headless
   `allegro.exe` for ~4 s and exits. Close stray Cadence sessions you own; do
   NOT touch any pre-existing interactive APD session. If the install or seat is
   missing, beat 7 self-skips and prints its fallbacks.
4. **Beat 6 stretch only:** if you plan the live re-solve, set
   `ANSYSEM_ROOT261` and `ANSYSLMD_LICENSE_FILE` in the session first and make
   sure no stray SIwave GUI is open (known landmine: a GUI can camp on the
   license seat -- there are 2 free seats).
5. **Optional: preload KLayout** with `geom\dirty.gds` + `geom\dirty.lyrdb`
   (beat 5 click), minimize.
6. **Windows open when the room walks in:** the cmd window with the menu
   showing, (optional) minimized KLayout, this script on the second monitor.
7. **If a beat dies on stage:** every beat prints its own fallback path --
   `type` it, narrate from it, move on. Full eight-beat rehearsal transcript:
   `C:\scratch\open-demo\stage\demo_all_dryrun.txt`.
8. **After the demo:** if you ran 2B, delete the generated
   `benchmarks\BENCHMARKS.phase1.md` from the repo (the driver prints the exact
   `del` line).

## Dry-run results (measured on this machine, driver end-to-end, cold start)

| Beat | Wall time | Exit behavior | Verdict |
|------|-----------|---------------|---------|
| 1 generate | 0.29 s | rc=0, byte-stable JSON | live |
| 2 verify clean+defect | 1.13 s | 0 then 1 (exactly 1 named catch) | live |
| 2B benchmark 20 cases | 1.57 s | `clean=0 caught=20/20 exact_failures=[]` | live |
| 3 pinmap cross-check | 1.81 s | 0 then 1 (exactly 3 seeded findings) | live |
| 4 ECO diff | 1.23 s | 1 (exactly 2 rows: removed + pair_broken) | live |
| 5 geometry lint + coverage | 1.21 s | 0, then 4/4 planted, coverage honest | live |
| 6 cavity vs SIwave + ts_gate | 1.18 s | rc=0, peaks 3.68% / 1.00% | live |
| 7 APD round trip (optional) | 10.9 s | 3 markers / ECO removes CAS | live |
| `demo.cmd all` | 19.0 s | all of the above in one go | rehearsal only |

No beat was flaky in the dry run -- every beat ran end-to-end through the driver
at the times above, and prebaked transcripts exist for all of them anyway. The
only environment-dependent pieces are beat 7 (Cadence install + license seat;
self-skips with fallbacks) and the beat 6 live re-solve (solver license; the
default beat 6 needs no license at all).

---

## Beat 8 (extended, ~7 min) -- the agentic loop: an agent fixes the package because of the physics

This is the closer for a technical audience with time. Full recipe, the exact
agent prompt, dress-rehearsal receipts, and the round-2 "refusal campaign"
scenario live in `demo/loop/LOOP_DEMO.md`; the agent operating manual is
`demo/loop/PLAYBOOK.md`.

**Say:** "Everything so far checked designs. Now watch an agent change one --
because of what the field solver said. It will solve the package, read the
verdict, compute the fix from cavity physics, edit the Cadence database headless
with independently verified SKILL, predict the outcome numerically before
re-solving, and then a referee tool -- not the agent -- decides whether the fix
is real. In rehearsal the referee confirmed the fix in six and a half minutes:
resonance down 96 percent, plane capacitance within the prediction. And when we
then added a conflicting requirement, the referee refused three plausible fixes
in a row rather than trade one mask for another. That refusal is the product."

**Type:** hand the agent terminal (W5) the prompt from `demo/loop/LOOP_DEMO.md`.

**Fallback:** narrate from the rehearsal receipts in LOOP_DEMO.md -- every number
there was measured, not projected.
