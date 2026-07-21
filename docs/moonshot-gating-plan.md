# Moonshot: open source → fully gated
## pkgtk × Cadence Allegro APD+ 24.1 × Ansys SIwave 2026 R1 (PyAEDT/pyedb)

> **Status addendum 2026-07-21:** substantial de-risking executed ahead of plan.
> M0a spikes A/B/D answered live (headless SKILL incl. DRC marker readout works;
> extracta works on .sip; bare `aif out` is form-modal — see
> docs/tool-bringup-checklist.md). M0b executed: Ansys 2026 R1 installed, first
> headless SYZ solve proven; SPIKE-C answered: native .sip translation blocked on
> an ALinks license, the working bridge is full-content IPC-2581 (`-O -I`
> mandatory). Beyond plan: `demo/loop/` implements a full closed agentic loop
> (solve → reason → verified .mcm edit → re-solve → referee) with a robustness
> matrix, clean-room rehearsals, and two live-discovered model limitations
> documented (IPC-2581 via galvanic connectivity; empty barrel material —
> auto-fixed). The M1 cassette layer remains the next milestone; the loop's
> runners and fail-loud/verify-everything conventions are its intended substrate.

Status: PLAN, rev 2 (not started). Written 2026-07-20 against pkgtk v0.1.0 (commit
dd59358). Rev 2 incorporates an adversarial review pass (accuracy / completeness /
feasibility panels); the material changes vs rev 1: cassette identity re-keyed on a
committed design registry (rev-1 keying was uncomputable in offline CI), Ring-1
re-recording tiered (rev-1 "re-record everything nightly" cannot physically complete),
M0 split so Cadence work does not wait on the Ansys install, mined-deck provenance
moved into the schema-legal `source` object, and the private-overlay repo given an
actual design. Claims that could NOT be verified are marked **SPIKE** — they are the
first things to test, not things to assume.

---

## 0. What "fully gated" means

Today every pkgtk wedge is **tier-0**: deterministic analytic code validated against
hand-computed golden fixtures. The moonshot adds **tier-1**: commercial-tool ground
truth, wired in without breaking the two standing doctrines:

1. **Deterministic core** — CI stays offline and license-free. No test ever needs
   apd.exe, siwave_ng.exe, or a license server. Licensed-tool outputs enter the repo
   only as **recorded cassettes** (extending the pattern proven by
   `src/pkgtk/llm/cassette.py` + `CassetteProvider`: canonical-JSON-keyed request →
   one JSON per key → replay-only CI that **fails loudly on CacheMiss** →
   `PKGTK_<X>_LIVE=1` records).
2. **Honest coverage** — every check gains a `gated_by` provenance with a fixed
   vocabulary: `golden-fixture` (tier-0: hand-computed golden — the acceptable
   baseline), `solver-differential` / `tool-differential` (tier-1: gated by agreement
   with SIwave/Sigrity or APD), and `analytic-only` (has **neither** — the bad state).
   The moonshot's definition of done: no `analytic-only` rows, and every row we chose
   to leave at `golden-fixture` documented as a choice.

The trust ladder per wedge: **analytic screen (fast, tier-0) → recorded solver oracle
(tier-1 cassette) → live solver (record mode, workstation only)**. pkgtk stays the
independent read-only verification layer; APD/SIwave become the oracles it is measured
against — and where they disagree, the disagreement itself becomes a loud, analyzed
artifact instead of silence.

---

## 1. Verified starting position

### On this machine (all verified-local, 2026-07-20)

| Asset | State |
|---|---|
| `C:\Cadence\SPB_24.1` | APD 24.1 installed. `apd.exe`, `extracta.exe`, `extracta_compiler.exe`, `dbdoctor.exe`, `batch_drc.exe`, `techfile.exe`, `ipc2581_out.exe`, `stream_out.exe`, `diacheck.exe`, `allegro_sendcmd.exe` present in `tools\bin`; batch usage docs offline at `share\pcb\batchhelp\*.txt`; full axl SKILL function reference at `share\pcb\examples\skill\DOC\FUNCS` |
| License | `CDS_LIC_FILE=5280@<license-server>` configured. **Installed ≠ licensed** for Sigrity — feature check is an M0 doctor item |
| `C:\Cadence\Sigrity2025.1` | **Potential bonus oracle**: PowerSI, PowerDC, XtractIM, OptimizePI, Clarity3D, Celsius installed (license features unverified) |
| Sample designs | `share\pcb\toolbox\getting_started\panelization\{mcm,sip}_context\databases\sample.{mcm,sip}` + `share\pcb\examples\board_design\Cadence_Demo.brd` — a license-clean internal corpus seed (Cadence install content: usable internally, **never redistributable**) |
| Ansys | **NOT installed.** No `ANSYS Inc` dir, no `AWP/ANSYSEM` env vars, no pyaedt/pyedb in Python 3.11.9. Install is M0b work with external lead time — request filed day one |
| ibischk / PyChOpMarg | Not present; freely obtainable (see M6). scikit-rf: already declared in the `[si]` extra, just not installed |
| GitHub | origin fully synced, v0.1.0 tag pushed (verified 2026-07-20). The "push blocked" paragraph in PHASE-NOTES is **stale** — M0a updates it |

### Key repo seams (all verified by reading the code)

- **Adapters terminate in the three frozen schemas** (`rule_ir`, `connectivity_graph`,
  `violation`, v0.1.0). `rule_ir.parameter` is an **open string** → new rule kinds
  (annular ring, density windows, IR drop) need **no schema change**; unknown params
  surface as `coverage: unimplemented`. The schemas set `additionalProperties: false`
  — no ad-hoc keys; anything new goes through the existing objects or waits for the
  single human-decided version bump (M8.5). Schema changes = STOP, human decides.
- **Reserved CLI slots**: `_ABSENT = {com, extract, ingest}` in `src/pkgtk/cli/main.py`
  are the front doors this plan fills (M2 → `ingest`, M6 → `com`, M7 → `extract`).
  Exit-code convention as documented in `main.py`: 0 clean / 1 violations / 2 usage /
  3 internal — note 3 is documented but currently unreturned; the new tool-facing
  CLIs give it its first real use (tool-unavailable / runner failure).
- **Cassette pattern to extend**: `cassette_key = sha256(canonical-JSON)[:32]`, one
  `<key>.json` per response, `CacheMiss` on CI miss, `PKGTK_LLM_LIVE=1` records.
  (M1 changes *what goes in the key* for tool cassettes — see the blocker fix there.)
- **Licensed-exe pattern to clone**: IBIS gate — exe path only from env
  (`PKGTK_IBISCHK`), pure parser over **captured stdout** committed as text fixtures.
- **Heavy-dep quarantine**: optional extras + conditional CLI registration +
  `pytest.importorskip` (klayout precedent). New extras follow it.
- **Geometry checks** plug into `lint/engine.py DISPATCH` + `IMPLEMENTED` + (keep in
  sync, deliberately duplicated) `lint/coverage.py IMPLEMENTED_PARAMETERS`.
- **PDN loss enters at exactly one line**: `k2 = ω²μ₀ε₀εr(1 − j·tanδ)` in
  `oracles/pdn_cavity.py z_matrix` — the conductor-loss extension point.
- **Golden guard**: `fixtures/golden/**` human-only via `GOLDEN_EDIT=1`. Benchmarks
  kept honest by `test_rollup_staleness.py` regenerate-and-diff.

---

## 2. Phase plan

Dependency shape: **M0a → M1 → M2 → M3 → M4** (Cadence track, starts immediately) and
**M0b → M5** (Ansys track, starts when the install lands) → M6 → M7 → M8.
"Parallel" on one workstation means **time-slicing**: long solver runs are queued to
nights/weekends through the same scheduler machinery Ring-1 will use (built in M1, not
M8); daytime belongs to interactive Cadence-side work. Each phase ends demoable
(`make demo` grows), committed per green `make ci`, decisions logged in
PHASE-NOTES.md — same discipline as Phases 0–6.

### The human critical path (filed at M0a day one, owners explicit)

These have external lead times or are human-only; late filing stalls later phases:

1. **Ansys 2026 R1 install request** (admin rights on a managed Windows 11 box, portal
   entitlements, license-server config) — file day one; M0b/M5 blocked on it.
2. **Ratify the v0.1.0 agent-authored goldens and schemas.** PHASE-NOTES' standing
   context records that the agent authored schemas/spec/goldens under delegated oracle
   authority "for the human to review and, where needed, override" — that review has
   not happened. Before tier-1 differentials anchor to these baselines, the human
   reviews and signs off (or corrects) `fixtures/golden/**` + the three schemas;
   sign-off recorded in PHASE-NOTES.
3. **Legal reviews** (identify who actually performs them; if the answer is "nobody",
   the conservative defaults below are the standing policy, not a stall):
   UCIe map encoding, JEDEC table derivation, committing ibischk logs of vendor
   models, **Cadence/Ansys EULA benchmark-publication clauses** (agreement matrices
   and accuracy deltas may have to be overlay-only, not public), and the
   employment-agreement/IP posture of doing this on an employer-licensed workstation
   (the original build plan's "personal machine" Hour-Zero constraint is already
   contradicted by the corporate license server — surface it, don't bury it).
   Conservative default until reviewed: nothing vendor/spec-derived leaves the
   private overlay; public benchmarks use synthetic + Cadence-sample structures only.
4. **UCIe eval-spec request** via a corporate/edu address (gmail won't qualify).
   Explicitly allowed outcome if unavailable: M6.4 descopes to "illustrative maps
   public, spec-exact maps skipped" — recorded, not silently stalled.
5. **Golden/cassette promotion time** — every milestone's exit gate that promotes
   recorded evidence budgets explicit human hours (stated per phase below).
6. Update the stale PHASE-NOTES "push blocked" paragraph (push verified working).

---

### M0a — Cadence bring-up, `pkgtk doctor`, de-risking spikes (no Ansys dependency)

**Goal:** every Cadence tool proven headless on this workstation before adapter code.

1. **`pkgtk doctor`** (new CLI, always registered): detects and version-stamps
   apd/extracta/techfile/ipc2581_out/stream_out/dbdoctor/batch_drc, ibischk, pyedb
   import, license reachability. Locates `lmutil` under both vendor roots and
   distinguishes three failure rows: *lmutil not found* / *server unreachable* /
   *feature absent*. Checks **Sigrity features** (PowerSI/PowerDC/XtractIM) on
   5280@<license-server> — installed ≠ licensed; SPIKE-F depends on this answer.
   Doctor output = the provenance header every cassette embeds. Env-var conventions:
   `PKGTK_APD_ROOT` (default `C:\Cadence\SPB_24.1`), `PKGTK_ANSYSEM_ROOT`,
   `PKGTK_IBISCHK`, per-tool live switches `PKGTK_APD_LIVE` / `PKGTK_SIWAVE_LIVE` /
   `PKGTK_SIGRITY_LIVE`.
2. **Spikes** (each go/no-go, ~half a day):
   - **SPIKE-A (apd headless + DRC readout):** `apd.exe -s wrapper.scr -nograph
     sample.mcm` (`wrapper.scr` = `skill load("probe.il")` / `skill main()` / `exit`;
     the `exit` is mandatory or the process never terminates; up to 63 `-s` scripts).
     Verify under a **non-interactive scheduled-task session** (`-nographic` is
     documented "pseudo non-graphic"; Windows service behavior unconfirmed).
     In the same probe: run `axlDRCUpdate(t)` and dump per-marker attributes —
     whether markers expose waived-state and actual/required values through SKILL is
     an open question M4's differential DRC depends on. Also evaluate
     **`batch_drc.exe`** (undocumented 26 MB binary) vs `dbdoctor -drc_only` and pick
     M4's headless-DRC primary on evidence. Decide the autologon-vs-service posture
     here (fallback: autologon session + `allegro_sendcmd.exe`), and record it —
     it is a security-posture decision, not a default.
   - **SPIKE-B (extracta on .sip):** shipped views (`conn_bv.txt`,
     `die_stack_view.txt`, `paksi_view.txt`) against `sample.sip`; `-d` dumps legal
     fields. extracta **checks out no license seat** (contention-free; a PCB product
     license must still exist on the server — it is not license-free).
   - **SPIKE-D (aif out in batch):** replay `aif out` from a `.scr` under `-nograph`;
     capture the AIF dialect 24.1 writes; feed existing `parse_aif`; confirm or
     correct the **guessed NETLIST row layout** recorded in PHASE-NOTES Phase 1.
   - **SPIKE-F (Sigrity batch):** contingent on doctor's license answer. Scope the
     PowerSI/PowerDC/XtractIM TCL batch surface (unresearched; treat as unknown).
3. **New extras** in pyproject: `[ansys]` (pyedb==0.80.2, pyaedt==1.3.0), `[com]`
   (PyChOpMarg, pinned), `[apd]` needs nothing (stdlib subprocess).

**Exit gate:** doctor green on all Cadence rows; SPIKE-A/B/D/F verdicts in
PHASE-NOTES; human items 1–6 above filed/answered; M1 may start. (~2h human.)

### M0b — Ansys bring-up (runs whenever the install lands; blocks only M5 + M4's pyedb routes)

1. Install Ansys 2026 R1; record actual root (`C:\Program Files\AnsysEM\v261\Win64`
   standalone vs `C:\Program Files\ANSYS Inc\v261\AnsysEM` unified). Set
   `ANSYSLMD_LICENSE_FILE`. Doctor learns the Ansys rows. **Confirm actual license
   features drawn by a 2026 R1 `siwave_ng` solve** (the elec_solve_siwave →
   elec_solve_level3/2/1 fallback chain is 2022 R2 evidence, not settled fact;
   also observe anshpc draw when `SetNumCpus` exceeds included cores).
2. **SPIKE-C (.sip → EDB):** `Edb(edbpath='sample.sip', version='2026.1')` — the
   translator path supports `sip`/`mcm`/`brd` per pyedb source. Audit: bondwires
   present as EDB `Bondwire` primitives (jedec4/jedec5/**apd** profiles)? Stackup and
   materials faithful vs APD cross-section? Confirm the **gRPC** sweep-setup signature
   (`add_frequency_sweep` list-style is the dotnet form; gRPC may be `add_sweep` —
   or sidestep by using the Configuration 2.0 JSON path, which is Ansys's recommended
   backend-neutral route). Observe whether an open pyedb EDB session draws any license
   feature concurrent with `siwave_ng` (contention question). Fallback bridge if
   translation is unfaithful: IPC-2581 **rev B** (`ipc2581_out.exe` default `-f 1.03`;
   1.04 is rev C) + manual bondwire re-injection via `create_bondwire`.
   Backend fallback: `pip install pyedb[dotnet]`.
3. **SPIKE-E (solver batch outputs):** does 2026 R1 `siwave_ng` accept
   `ExecResModeSim` (resonant mode), and which non-touchstone files under
   `.siwaveresults` actually materialize in pure batch (some reportedly appear only
   via GUI access)? Fallbacks: SYZ |Z| peak-picking; `siwave.exe -RunScriptAndExit`
   report-export path.

**Exit gate:** doctor green on Ansys rows; SPIKE-C/E verdicts logged; one plane-pair
SYZ solved headless end-to-end with a touchstone collected.

---

### M1 — The EDA cassette layer (architectural keystone)

**Goal:** one record/replay mechanism for every licensed tool such that **a machine
with no tools and no design files replays everything green**. That sentence is the
design constraint the rev-1 plan failed; the fixes below are load-bearing.

1. **Identity vs provenance (the blocker fix).** The cassette key must be computable
   from committed data alone:
   `key = sha256(canonical-JSON({tool, logical_design_id, design_rev, args, setup}))[:32]`.
   - A committed **design registry** (`fixtures/tool_cassettes/design_registry.yaml`)
     maps `logical_design_id → {rev, sha256, source_path, generation_recipe}`. The
     design files themselves are never committed (license); the registry is.
   - **Injected/derived designs are keyed by recipe, not by resulting binary**:
     `{base_design_id, injector_script_sha256, injection_params}` — Allegro DB saves
     embed timestamps, so binary hashes are nondeterministic across regeneration and
     must never be identity. Derived `.mcm/.sip` binaries live only in the private
     overlay (they are derivatives of redistribution-restricted install content).
   - `tool_version`, file sha256, host, date, license feature → **provenance block
     only**, never the key. Tool updates and design re-saves therefore keep the key,
     which is exactly what makes drift *diffable*: re-record under the same key,
     numerically compare, report old/new tool_version.
   - A committed manifest maps test-case → cassette key so replay never recomputes.
2. **Size policy.** Cassettes commit **derived quantities** (resonance lists, |Z| on a
   fixed eval grid, mask margins, DRC violation sets, parsed report tables) plus the
   sha256 of raw outputs. Raw solver artifacts (multi-hundred-port touchstones can be
   tens of MB–GB) stay on the workstation / private overlay (git-lfs there), never in
   the public repo; whole-file commits only under ~1 MB (extracta dumps, plane-pair
   SnP, captured stdout).
3. **Cassette-diff spec** (one page, `docs/cassette-diff-spec.md`, written before
   runner code): per-runner derived quantities, per-quantity tolerance, grid-alignment
   rule (SYZ: interpolate both sides to the committed eval grid, gate max|ΔS| and
   |Δf_res|/f_res; DRC: set-compare violations by (rule, net, layer, location±ε);
   DCIR: per-element relative current/voltage bands), and which provenance fields are
   diff-excluded (host, date, runtime, temp paths). Raw sidecars are the source of
   truth; derived values are **re-derived at diff time from raws on the recording
   side**, so a parser code change re-derives both sides identically instead of
   masquerading as tool drift.
4. **Runners**, each = thin subprocess wrapper + **pure parser** unit-tested on
   captured output (the ibischk precedent): `ApdScriptRunner` (wrapper.scr + .il →
   `apd -nograph`, collects declared outputs), `ExtractaRunner`, `TechfileRunner`,
   `Ipc2581Runner`, `StreamOutRunner` (GDS + .cnv), `SiwaveRunner` (pyedb setup →
   .aedb → `siwave_ng <aedb> <exec> -formatOutput -useSubdir` → collect). Runners
   always operate on **scratch copies** of designs, never the originals (protects
   working copies and dodges Allegro lock files).
5. **Guard extension (agents must not self-serve their own evidence).** Tool cassettes
   are the evidence base for tier-1 gates, and agents run on the very workstation
   where `PKGTK_<TOOL>_LIVE=1` works — so a red gate must not be "fixable" by silent
   re-recording. Live runs write to a shadow dir (`fixtures/.rerecord/`) and diff;
   **replacing a committed cassette requires `CASSETTE_ACCEPT=1`**, enforced by
   extending `scripts/golden_guard.py` to cover `fixtures/**/tool_cassettes/**`, with
   the acceptance reason (tool X→Y, design rev bump) logged in PHASE-NOTES.
6. **Solve queue.** A minimal queue/scheduler (the same machinery Ring-1 reuses in
   M8): long jobs enqueue for nights/weekends with a wall-clock budget and hard
   cutoff; daytime interactive work is never blocked by a solver saturating cores.
7. **Private overlay bootstrap** (load-bearing for M3/M6/M8, so it is built now, not
   named later): sibling repo, identical layout, discovered via
   `PKGTK_PRIVATE_FIXTURES` (and `PKGTK_DECK_DIR` for decks). A `conftest.py` hook
   registers overlay fixture/test dirs when set and — critically — when *unset*
   prints an explicit `overlay: ABSENT — N overlay-gated rows unverified` line in the
   coverage report (honest-coverage doctrine survives the split). Overlay shadows
   public on collision, with a doctor warning. golden-guard becomes a console entry
   point installed by `pip install -e pkgtk` so both repos' pre-commit configs share
   one implementation. Overlay pins pkgtk by commit; Ring-1 runs the pinned pair.
   The overlay gets a **private remote (or at minimum a second-disk mirror) on day
   one** — this workstation is simultaneously dev machine, recording rig, and
   Ring-1 runner; a reimage must not erase the only copy of the evidence base.

**Exit gate:** one end-to-end cassette per runner recorded on sample.mcm/sample.sip;
**replayed green from a clean temp checkout with no design files and no tools on
PATH** (verbatim test, not just hiding an env var); diff-spec doc committed; guard
extension active; overlay repo exists with remote. (~2h human: cassette promotion +
overlay repo creation.)

---

### M2 — APD ingestion bridge: `pkgtk ingest` comes alive

**Goal:** real APD designs flow into the connectivity graph through *two independent
paths that must agree*; the deferred Excel/CSV ingestion (Phase 1.2) closes with real
files.

1. **AIF path (zero new parse code):** batch `aif out` (SPIKE-D) → existing
   `parse_aif`. Extend `_KNOWN` sections only as the real dialect demands (extras
   already carries unknowns losslessly). `reference/aif/README.md` updated with the
   confirmed-or-corrected row layout verdict.
2. **extracta path:** custom views (start from `conn_bv.txt` + `die_stack_view.txt`;
   NET_NAME, pin/ball designators + coordinates, die pads, component pins, net
   properties via `-P`) → `src/pkgtk/ingest/extracta.py` → `ConnectivityGraph`, with
   role enrichment (signal/gnd/pwr) from net properties.
3. **Cross-validation gate** with a **specified canonicalization contract** (unit
   normalization, origin anchored on a named ball, name-normalization rules for
   bus/bracket notation, an explicit exclusion list for object classes one exporter
   omits by design — fiducials, mechanical pins): AIF-ingested graph ≡
   extracta-ingested graph after canonicalization, with a categorized mismatch report
   so representational deltas are triaged once and pinned as expected. Remaining
   mismatches are loud translator-bug artifacts. `diacheck.exe` runs as a third
   check on the die-abstract side.
4. **Excel/CSV ball maps (closes Phase 1.2):** `mapping.yaml` + xlsx/csv reader
   (pandas/openpyxl already core deps). Ground truth is free: APD `symbol to
   spreadsheet` / `bga text out` exports (SKILL `axlSpreadsheet*` or wizard commands
   in .scr) — the true mapping is known because we exported it. Human verifies once →
   golden xlsx (`GOLDEN_EDIT=1`). Reader handles .xlsx (openpyxl) and APD-native
   delimited/SpreadsheetML.
5. **ECO diff gating:** SKILL **defect injector** (`inject.il`: swap nets, delete a
   ball, repurpose a gnd ball, move a ball — registry-keyed by recipe per M1) →
   `aif out` both revs → `pkgtk diff` must catch exactly the injected classes at the
   injected positions. New benchmark section, cassette-replayed.

**Exit gate:** `pkgtk ingest design.{aif,xlsx,csv}` live (removed from `_ABSENT`);
dual-path agreement green on corpus with pinned exclusion list; AIF row-layout
verdict recorded; injected-defect ECO benchmark at Phase-1 standards (100% catch,
0 false positives). (~3h human: xlsx golden verification, mismatch triage sign-off.)

---

### M3 — Constraint mining: manufacturing-valid Rule-IR decks from Constraint Manager

**Goal:** kill "the deck is NOT manufacturing-valid" for internal use — decks compile
from the design's own constraint system, with provenance, **without touching the
frozen schema**.

- **Batch export:** `techfile.exe -w -i speuaxnr design.sip rules.tcf` (documented
  section letters: s=spacing, p=physical, e=electrical, u=user, a=assembly/SIP,
  x=stackup, n=netclass, r=properties; use the documented literal `-i speuaxnr`).
  Stackup-only export: `techfile -w -i x`. Design-specific `.dcf` variant likewise.
- **Deck compiler** `src/pkgtk/ingest/techfile.py`: physical CSets →
  `trace_width_min` (+ neck), spacing CSets → `spacing_min` scoped per layer/class,
  same-net rules, via lists → Rule-IR YAML. **Provenance rides in the existing
  `source` object** — `{doc: <design file>, revision: <export timestamp>, table:
  <CSet name>, row: <index>}` — which the frozen schema already allows
  (`additionalProperties: false` forbids a new top-level key; a dedicated
  `provenance` field goes on the M8.5 schema-pressure list for the human). Sidecar
  file carries anything that doesn't fit.
- **RunConfig generation** (moved here from rev-1's M2, which had it depending on M3
  machinery): electrical CSets via SKILL (`axlDBGetDesign()->ecsets`,
  `axlCNSEcsetValueGet`, `axlNetEcsetValueGet`) → diff-pair gap/uncoupled length +
  `match_groups` / `pair_patterns` — the ball-map checks get real configs from the
  design instead of hand-written ones.
- **Deck IP split:** public repo keeps only the generic NOT-MANUFACTURING-VALID deck;
  mined decks (NDA'd numbers) live in the overlay via `PKGTK_DECK_DIR` (built in M1).
- **Cross-gate:** where the M7 LLM rule-sheet extractor and the techfile miner
  overlap, the miner is the referee — a deterministic verifier for the LLM flow.

**Exit gate:** mined deck from sample.sip loads through `load_deck` (schema-valid),
coverage classifies every mined rule, and `pkgtk check` runs the scalar subset
against corpus GDS **produced by the M1 StreamOutRunner cassette with a hand-written
.cnv** (the auto-derived layer bridge arrives in M4.1) with 0 violations on the
untouched design; RunConfig generated from ecsets drives `pkgtk verify` on the
corpus. (~1h human.)

---

### M4 — Geometry gating: close all four unimplemented checks + net-aware spacing,
### then differential-DRC against Allegro itself

**Goal:** geometry coverage all-green, every geometry check gated by agreement with
APD's own DRC on seeded defects.

1. **Geometry bridge, automated:** `stream_out.exe -c layers.cnv -o pkg.sf -n TOP -u
   MICRONS design.mcm`; the `.cnv` and `layers.yaml` auto-derived from the
   cross-section (SKILL `axlGetXSection` in the ApdScriptRunner probe, or
   `techfile -w -i x`) so the layer map is never hand-maintained.
2. **New checks** (each: fn in `DISPATCH` + `IMPLEMENTED` +
   `coverage.IMPLEMENTED_PARAMETERS`, violations with PhysicalLocation):
   - `annular_ring_min` — pyedb padstack route: per instance/layer, ring = (pad
     diameter from `PadstackDef.pad_by_layer[layer]` − effective drill from
     `hole_diameter` / `get_hole_overrides()`)/2. Cross-check sample vs extracta
     `COMPOSITE_PAD` view. (extracta becomes primary if M0b shows pyedb friction;
     it is also the path that works before Ansys lands.)
   - `copper_balance_window` / `degas_coverage_window` — klayout **tiled density via
     TilingProcessor with shifted-origin passes** (`tile_origin`) to approximate a
     sliding window — a fixed grid alone misses worst-case windows straddling tile
     boundaries; the step/window ratio is pinned in lint-spec.md as explicit check
     semantics. Aggregate cross-check vs `edb.stackup.residual_copper_area_per_layer()`.
   - `ball_grid` — pitch/alignment/missing-position from padstack-instance
     coordinates (extracta or pyedb) vs the ConnectivityGraph grid.
   - **Net-aware spacing** — per-net klayout Regions from pyedb
     `layout.primitives_by_net` → cross-net `separation_check` (same-net excluded);
     extracta FULL_GEOMETRY(+NET_NAME) as the independent second source.
3. **Differential DRC (the tier-1 gate):** defect injector (recipe-keyed) plants
   geometry violations → run **both** Allegro DRC (primary chosen in SPIKE-A:
   `batch_drc.exe` or `dbdoctor -drc_only` or `axlDRCUpdate(t)` + marker readout)
   **and** `pkgtk check` on exported GDS. Commit the **agreement matrix**:
   caught-by-both / pkgtk-only / allegro-only, every cell explained. Triaged
   disagreements: pkgtk bug → fix; semantic difference → documented in lint-spec.md.
   Target: 100% agreement on the seeded classes pkgtk claims to cover.
4. **pkgtk findings inside APD:** `axlDBCreateExternalDRC` injects pkgtk violations
   as native clickable DRC markers in the designer's session.
5. **Variable binding for piecewise/expression rules:** bind design variables (layer,
   copper thickness from cross-section) per rule scope so the deferred
   piecewise-width-table rules execute on real designs.
6. **Media (human, ~1h):** the deferred Phase-2 exit-gate artifact — `out.lyrdb`
   opened in KLayout (0.30.9, installed) with clickable markers, **screenshot
   committed to docs/** — plus the new APD-marker screenshot. Both, not a substitute.

**Exit gate:** coverage table for the mined deck shows the four former-unimplemented
checks implemented; differential-DRC benchmark committed at 100% seeded-defect
agreement (or documented semantic deltas); a piecewise width-table rule executes on a
corpus design with bound variables; both screenshots in docs/. (~2h human.)

---

### M5 — Physics gating: SIwave (and Sigrity, if licensed) as PDN/escape ground truth

**Goal:** the cavity model stops being "trust the math" and becomes "within a stated
tolerance of independent commercial solvers, with the divergence quantified".
All solves go through the M1 queue (nights/weekends); setup uses the
**Configuration 2.0 JSON path** as primary (backend-neutral; sidesteps the
dotnet-vs-gRPC sweep-signature question), raw API calls as fallback.

1. **Parametric agreement ladder (synthetic → real):**
   a. Parametric plane-pair EDBs matching `Cavity(a,b,d,εr,tanδ)` exactly (pyedb:
      stackup + planes + ports; `add_djordjevicsarkar_dielectric`;
      `assign_roughness_model('huray',…)` for loss studies). Headless SYZ:
      config-JSON setup → `create_exec_file(add_syz=True, export_touchstone=True,
      touchstone_file_path=…)` → `siwave_ng <aedb> <exec> -formatOutput -useSubdir`.
   b. Gate analytic vs solver: f₁₀/f₀₁/f₁₁ within 2%, low-freq |Z| within 0.5%, and
      **quantify the peak-Q delta** — the measured cost of the documented
      conductor-loss omission.
   c. **Extend the cavity model with conductor loss** at the single k² line:
      `tanδ_eff(f) = tanδ_d + δs(f)/d`, `δs = sqrt(2/(ωμ₀σ))` (standard first-order
      plane-pair result, both planes). The gate is empirical: Q agreement vs SIwave
      within a stated band across the sweep, or it doesn't merge. Golden analytic
      peak locations must not move.
   d. Real designs: ports at die bumps + BGA balls (`create_pin_group_on_net`,
      `create_circuit_port_on_pin_group`), SYZ sweep; `TargetMask`/`worst_margin` on
      BOTH solver and cavity |Z|; `pkgtk pdn --oracle cassette.json` reports both
      verdicts + divergence. Decap studies gate `z_with_decaps` the same way.
   e. Resonant-mode cross-check per SPIKE-E verdict (ExecResModeSim or peak-picking).
2. **Sigrity triangulation** (contingent on M0a license check): PowerSI SYZ + PowerDC
   on the same structures. Three-way agreement (cavity / SIwave / PowerSI) upgrades
   "matches the solver" to "matches two independent solvers"; XtractIM per-pin RLC as
   an extra package-parasitic gate. Not critical path — a bonus lane.
3. **New wedge — `pkgtk dcir`:** SiwaveDCIR headless (config-JSON
   `{'type':'siwave_dc','dc_slider_position':1,…}` → `SiwaveSolve.solve_siwave(…,
   'DCIR')` → `export_dc_report`/element data incl. the **Bondwires** category).
   Deck rules `ir_drop_max` / `via_current_max` (open-string parameters — no schema
   bump) → violations from parsed element tables. New coverage row, honest from day
   one.
4. **Escape oracle gating:** route escapes in APD on corpus designs; count achieved
   tracks from routed geometry (extracta/pyedb) vs `n_tracks`; calibrate utilization
   verdicts; build the documented v2 max-flow (networkx) and gate it against actual
   APD routes.

**Exit gate:** parametric agreement table (cavity vs SIwave [vs PowerSI]) in
BENCHMARKS.md with stated tolerance bands, cassette-replayed (derived quantities per
the M1 size policy); conductor-loss extension merged only past its Q-gate;
`pkgtk dcir` demoable; escape verdicts calibrated on ≥1 real routed design.
(~2h human: solve-result spot verification in the SIwave GUI.)

---

### M6 — SI model chain: real Touchstone, real IBIS, COM validated

1. **Touchstone gate on solver output:** every M5 SYZ touchstone runs through
   `ts_gate.gate()` — solver outputs must pass their own physics gate (failing
   passivity on a solver cassette = translator/setup bug surfaced). `pip install -e
   .[si]` (extra already declares scikit-rf); wire the optional IEEE-370 upgrade
   behind the import: `skrf.calibration.IEEEP370_FD_QM` grades
   passivity/reciprocity/**causality** (percentage scores) — `causality: unassessed`
   finally becomes assessed. The numpy gate stays the default; both run on goldens
   and are compared before the upgrade is enabled (swap-in policy per PHASE-NOTES).
2. **IBIS goes live:** download ibischk7_64 (free binary; source is $2.5k — shell
   out, never vendor). `PKGTK_IBISCHK` set. **Known gotcha our design already
   handles: ibischk7 exits 0 even with ERRORs** — verdicts come from parsed stdout;
   add `-numbered` mode for stable E####/W#### codes. Real TI/ADI models downloaded
   locally, **never committed**; committed fixture = URL + sha256 + captured
   `-numbered` log (flagged as a legal judgment, not documented permission —
   conservative default: overlay-only until reviewed). **Model librarian tie-in**:
   real models flow through `Registry.intake` — the state machine finally tracks a
   real intake, chase emails included.
3. **COM (`pkgtk com` leaves `_ABSENT`):** vendor **PyChOpMarg** (BSD-3, pinned tag +
   upstream commit hash recorded) behind the `[com]` extra. Validation ladder: run on
   the **official IEEE 802-COM** reference configs (BSD-3 per the IEEE SA project
   request — **confirm the actual LICENSE file on first clone** before vendoring
   reference results; releases through COM 4.8) → record reference results as
   cassettes → every pkgtk COM output stamped `UNVALIDATED_AGAINST_MATLAB_REFERENCE`
   until the delta on N reference channels sits inside a stated band, then the stamp
   flips with provenance. Feed M5-extracted channel .sNp → COM as a tier-1 SI verdict
   on real package channels. (SPIKE: does the official MATLAB run under Octave, or do
   we record the MATLAB reference once on a licensed seat?)
4. **Spec-exact template maps:** UCIe eval spec via corporate email (human item 4;
   descope is an allowed recorded outcome). No-derivatives/no-redistribution eval
   terms → spec-exact maps **overlay-only** as derived position→role data pending
   legal comfort. JEDEC: free registration, but **confirm the target JESD standards
   are in the free tier** (non-member paid tier now exists for selected standards);
   encode as derived data. Public repo keeps the illustrative map, labeled as such.
   Template checker gains anchor-offset alignment (from real ball-map exports)
   replacing v0 identity.

**Exit gate:** causality assessed on all touchstone goldens; live ibischk on ≥2 real
vendor models with logs (overlay) + librarian tracking them; COM
validated-or-stamped with reference deltas in BENCHMARKS.md; template check runs a
spec-exact overlay map on a corpus design — or its descope is recorded. (~3h human:
model downloads, license confirmations, UCIe request.)

---

### M7 — LLM layer goes live (with ground truth APD gave us for free)

Unblocked by: `ANTHROPIC_API_KEY` + `PKGTK_LLM_LIVE=1` + M2's xlsx layer.

1. **Mapping inference (4.2):** the eval needs no hand-built truth — M2's APD
   spreadsheet exports have a *known* mapping. Build `clean.xlsx` from real exports,
   `adversarial.xlsx` by mutation (merged headers, footnotes, unit traps). LLM
   proposes `mapping.yaml`; accepted only if the reconstructed graph ≡ the known
   graph — a deterministic referee on top of the paranoia battery.
2. **Net-name semantics (4.3):** real corpus net names; inferred roles/domains gated
   against M3's techfile/ecset domain data.
3. **Rule-sheet extraction (4.4):** two-pass extraction + review table on public
   design-rule documents + synthetic adversarial sheets; techfile-mined decks referee
   the overlap. **Registers `pkgtk extract`** (leaves `_ABSENT`).
4. Cassettes recorded for every flow; CI replay-only. **LLM cassettes are excluded
   from Ring-1 re-recording** — they re-record manually when prompts change, never on
   a schedule (provider-side drift would guarantee chronic red).

**Exit gate:** carried forward from the original Phase-4 numbers, not vibes —
**100% precision on auto-accepted** mappings/rules (misses only as flagged-unparsed),
correct `mapping.yaml` on **≥3 differently-shaped sheets** including the adversarial
one; extraction produces a deck that loads + coverage-classifies; `pkgtk extract`
live; all flows replay offline. (~2h human: review-table adjudication.)

---

### M8 — Integration: the gated CI machine, v0.2.0

1. **Two-ring CI with a tiered re-record policy** (rev-1's "re-record everything
   nightly" cannot complete once multi-hour solves exist):
   - **Ring 0 (unchanged, anywhere):** `make ci` — offline, license-free, replay-only.
   - **Ring 1 (this workstation, scheduled):** `make gated` —
     **Tier F** (fast, seat-free: extracta, techfile, stream_out, ipc2581_out,
     aif out — seconds-to-minutes) nightly;
     **Tier M** (APD DRC, defect-injector regeneration, small plane-pair solves)
     weekly, rotating;
     **Tier S** (real-design SYZ/DCIR/PowerSI) **on-trigger only** — doctor detects a
     tool version change, the design registry bumps a rev, or runner code changes —
     plus a monthly full pass. Wall-clock budget with a hard cutoff (kill and report
     at 06:30). Per-tier staleness ages in the provenance report so old Tier-S
     cassettes are loud. Records go to the shadow dir and **diff only**; acceptance
     is human (`CASSETTE_ACCEPT=1`, per M1.5).
   - **Runbook:** nightly job copies designs to scratch before opening (lock files);
     pre-flight checks locks + license availability and **degrades to seat-free
     tiers instead of aborting** when a designer left APD open holding the license;
     retry-once for infra-class failures; quarantine list with max-age (quarantined
     >7 days fails Ring-0 coverage honesty); report distinguishes **infra-red from
     drift-red** so morning triage is a 30-second read; power plan (no sleep, wake
     timer, deferred update reboots) and task env (`gated.env` sourced by the task,
     not inherited session vars) documented.
2. **Benchmarks rollup** gains sections: APD-differential ingestion/ECO, differential
   DRC agreement matrix, PDN solver-agreement, DCIR, COM reference deltas — replayed
   from cassettes so `make bench` stays offline; staleness guard extended. Rollup
   splits: public sections use synthetic + Cadence-sample structures only; an
   **overlay-only rollup** carries anything computed against NDA'd decks or real
   designs (and stays private pending the EULA-publication legal answer).
3. **Coverage provenance:** the coverage report and README table gain the `gated_by`
   column (vocabulary per §0). Done = no `analytic-only` rows; `golden-fixture`-only
   rows are documented choices.
4. **Wheel packaging** (recorded Phase-6 follow-up, closed here): schemas/ as package
   data (importlib.resources), verified by `pip install pkgtk-*.whl && make demo`
   from a clean venv before tagging.
5. **Schema pressure review:** collected wants from M2–M7 (dedicated `provenance`
   field, possible `bond_finger`/`via` node kinds, per-layer locations) → STOP, human
   decides v0.2.0 schema bump once, here.
6. **README + media:** Honesty section rewritten — each closed gap moves to the
   coverage table with its gate; surviving gaps stay listed ("COM stamp not yet
   flipped", "UCIe map overlay-only/descoped"). The full **Phase-6 media checklist**
   (human): KLayout marker screenshot (from M4), APD marker screenshot, ECO diff
   report, PDN cavity-vs-SIwave overlay plot, review-table-catching-footnote-trap,
   terminal GIFs, differential-DRC matrix rendering.
7. Tag v0.2.0 **and push it** (push path verified working 2026-07-20).

**Exit gate:** one full Ring-1 cycle green (or triaged) per tier; wheel install
demo passes; v0.2.0 pushed; coverage table shows zero `analytic-only`. (~4h human:
media, acceptance passes, README review.)

---

## 3. Honesty-gap closure matrix (v0.1.0 records → this plan)

| Recorded gap | Closed by | Mechanism |
|---|---|---|
| Deck not manufacturing-valid | M3 | techfile/CSet-mined decks, provenance in `source`, overlay-hosted |
| Windowed density unimplemented | M4 | TilingProcessor shifted-origin tiling + pyedb cross-check |
| annular_ring_min unimplemented | M4 | pyedb padstack tables (extracta cross-check) |
| ball_grid unimplemented | M4 | padstack-instance coordinates vs graph grid |
| Net-aware spacing deferred | M4 | pyedb per-net regions → cross-net separation_check |
| COM not included | M6 | PyChOpMarg vendored + IEEE 802-COM reference gating; stamp until delta-gate passes |
| PDN omits conductor/skin loss | M5 | tanδ_eff extension at the k² line, Q-gated vs SIwave (+PowerSI) |
| Excel/CSV ingestion deferred | M2 | mapping.yaml + xlsx reader; APD exports = real ground truth |
| LLM live flows deferred | M7 | API key + cassettes; APD exports as mechanized referee; Phase-4 numeric gates carried |
| IBIS fixtures representative-only | M6 | live ibischk7 on real vendor models; logs (overlay), models never committed; librarian tracks intake |
| Template map illustrative | M6 | UCIe/JEDEC derived maps, overlay-only (descope = allowed recorded outcome) |
| KLayout lyrdb screenshot deferred | M4.6 | actual KLayout screenshot committed (APD markers are additional, not a substitute) |
| Piecewise/expression rules skipped | M4.5 | design-variable binding from cross-section/techfile (in M4 exit gate) |
| causality: unassessed | M6 | scikit-rf IEEEP370_FD_QM behind the existing [si] extra |
| Escape v2 max-flow cited not implemented | M5 | implemented + gated vs real APD routes |
| AIF NETLIST row layout = documented guess | M2 (SPIKE-D) | confirmed/corrected against real 24.1 `aif out`; reference/aif updated |
| Wheel packaging follow-up | M8.4 | schemas as package data; clean-venv wheel demo |
| README media/GIF checklist (human) | M8.6 | full checklist scheduled, incl. new artifacts |
| Push blocked / v0.1.0 tag local | resolved | verified synced+pushed 2026-07-20; M0a fixes the stale PHASE-NOTES note |
| Agent-authored goldens/schemas unratified | M0a human item 2 | human review + sign-off before tier-1 anchors to them |
| ibischk exit-code trap | M6.2 | already handled (stdout parsing); `-numbered` added |

---

## 4. Repo & IP architecture

- **Never in the public repo:** Cadence sample designs or derivatives of them
  (injected revB databases included — install content is redistribution-restricted),
  customer/fab designs or mined deck values (NDA), vendor .ibs files (copyright),
  UCIe/JEDEC spec-derived exact maps (eval-agreement/no-derivatives risk), Ansys
  project files from real designs, and — **pending the EULA-publication legal
  answer — solver agreement matrices/accuracy deltas computed on anything but
  synthetic structures**.
- **Public:** engines, runners, parsers, cassette schemas + design registry (ids,
  recipes, hashes — not the files), synthetic parametric structures, derived-quantity
  cassettes on synthetic + sample-design structures if the EULA answer allows,
  URL+sha256(+log location) records for vendor models.
- **Private overlay** (designed and built in M1.7): sibling repo, identical layout,
  `PKGTK_PRIVATE_FIXTURES`/`PKGTK_DECK_DIR` discovery, conftest-registered tests,
  loud `overlay: ABSENT` coverage line when unmounted, shadow-on-collision with
  doctor warning, shared golden-guard console entry point, pkgtk pinned by commit,
  private remote + backup from day one. Holds: mined decks, spec-derived maps,
  real-design cassettes + raw solver outputs (git-lfs), vendor-model logs, injected
  design binaries.
- **Legal reviews** (owner named in M0a human item 3; conservative defaults apply
  until answered): UCIe encoding, JEDEC derivation, vendor-model logs, Cadence/Ansys
  EULA benchmark-publication clauses, employment/IP posture of the workstation.

---

## 5. Risk register

| # | Risk | Exposure | Mitigation |
|---|---|---|---|
| 1 | `apd -nographic` fails under non-interactive session | Ring-1 automation | SPIKE-A day one; fallback autologon + allegro_sendcmd (posture decided + recorded at SPIKE-A) |
| 2 | .sip→EDB translator drops bondwires/die stacks | M5 fidelity | SPIKE-C audit; fallback IPC-2581 rev B (`-f 1.03`/default) + `create_bondwire` re-injection |
| 3 | ExecResModeSim gone / .siwaveresults sparse in batch | M5.1e, M1 runner | SPIKE-E; fallbacks: SYZ peak-picking, `-RunScriptAndExit` export |
| 4 | License contention (designers vs Ring-1; solver overruns into workday) | throughput | tiered policy + hard cutoff; pre-flight degrade to seat-free tier (extracta draws no seat); lmutil pre-flight |
| 5 | UCIe/JEDEC/vendor-log redistribution | legal | overlay-only defaults + named reviewer; descope allowed |
| 6 | Sigrity installed but not licensed | M5.2 bonus lane | doctor feature check in M0a; Sigrity is triangulation, never critical path |
| 7 | Cadence/Ansys EULA benchmark-publication clauses | public benchmarks | overlay-only matrices until reviewed; public rollup = synthetic structures |
| 8 | pyedb gRPC teething on .sip; sweep-API signature drift | M2/M4/M5 | config-2.0 JSON primary; `pyedb[dotnet]` fallback; SPIKE-C confirms |
| 9 | Schema pressure mid-phase | doctrine | provenance via `source` now; wants collected → single human bump at M8.5 |
| 10 | Cassette drift conflated with parser changes / tool updates orphaning keys | Ring-1 meaning | registry-keyed identity (recipe, not binary hash); re-derive both sides from raw sidecars; per-quantity tolerance table in cassette-diff-spec |
| 11 | Agents self-servicing red gates by re-recording | evidence integrity | shadow-dir recording + `CASSETTE_ACCEPT=1` guard extension (M1.5) |
| 12 | Ansys install lead time serializing everything | schedule | M0a/M0b split; request filed day one; only M5 + pyedb routes blocked |
| 13 | Single workstation = dev + recorder + runner + only evidence copy | disaster recovery | overlay private remote/second-disk mirror day one; raws on the backup path |
| 14 | Ring-1 broken-windows (chronic red ignored) | process | infra-red vs drift-red split; retry-once; quarantine max-age tied to Ring-0 honesty |
| 15 | UCIe needs corporate email (user context: gmail) | M6.4 | company address, or recorded descope |

---

## 6. Command crib sheet
(verified against local batchhelp / pyedb source, except items marked confirm-in-spike)

```text
# SKILL batch                apd.exe -s wrapper.scr -nograph design.mcm
#   wrapper.scr:             skill load("job.il")  /  skill main()  /  exit
# Headless DRC               dbdoctor.exe -drc_only design.mcm     (batch_drc.exe: evaluate in SPIKE-A)
# Extraction                 extracta.exe design.sip view.txt out.txt      (-d dumps fields)
#   license note: checks out NO seat, but a PCB product license must exist on the server
# Constraints → XML          techfile.exe -w -i speuaxnr design.sip rules.tcf   (stackup only: -i x)
# IPC-2581                   ipc2581_out.exe design.mcm -o out -n -k -l -u MICRON   (default -f 1.03 = rev B; -f 1.04 = rev C)
# GDS artwork                stream_out.exe -c layers.cnv -o pkg.sf -n TOP -u MICRONS design.mcm
# Die abstract check         diacheck.exe die.txt report.txt
# Drive a live session       allegro_sendcmd.exe "<command>"
# Offline docs               C:\Cadence\SPB_24.1\share\pcb\batchhelp\*.txt
#                            C:\Cadence\SPB_24.1\share\pcb\examples\skill\DOC\FUNCS\*.txt

# EDB from Cadence           Edb(edbpath='design.sip', version='2026.1')
# Setup (primary path)       edb.configuration.load('cfg.json'); edb.configuration.run()   # backend-neutral
# SYZ setup (API path)       edb.create_siwave_syz_setup('syz1')  # sweep API: dotnet add_frequency_sweep(list) /
#                            gRPC add_sweep — confirm exact signature in SPIKE-C
# Ports                      edb.siwave.create_pin_group_on_net(...); create_circuit_port_on_pin_group(...)
# Exec + touchstone          edb.siwave.create_exec_file(add_syz=True, export_touchstone=True, ...)
# Batch solve                siwave_ng.exe design.aedb design.exec -formatOutput -useSubdir
# DCIR                       edb.create_siwave_dc_setup('dc1'); SiwaveSolve(...).solve_siwave(path,'DCIR')
# Materials/roughness        edb.materials.add_djordjevicsarkar_dielectric(...);
#                            edb.stackup.signal_layers['L'].assign_roughness_model('huray', ...)
# Annular ring data          edb.padstacks.definitions[d].pad_by_layer / hole_diameter
# Net-tagged geometry        edb.layout.primitives_by_net → PolygonData.points/area()/unite()

# IBIS golden parser         ibischk7_64.exe -numbered model.ibs      (exit 0 even on ERRORs — parse stdout)
# COM                        pip install PyChOpMarg  (BSD-3; reference: opensource.ieee.org/802-com —
#                            confirm LICENSE file on first clone)
# IEEE-370 causality         skrf.calibration.IEEEP370_FD_QM().check_quality(network)
```
