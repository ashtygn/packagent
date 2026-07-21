# Tool bring-up & feature-test checklist
## APD 24.1 · Sigrity 2025.1 · Ansys Electronics 2026 R1 (SIwave + pyedb)

Status legend: ✅ = executed and verified on this workstation (dates 2026-07-20/21,
scratch dirs under `%TEMP%\pkgtk-probe\`) · ⚠ = probed, needs a different route ·
❌ = probed, dead end · ⬜ = TODO, exact commands given.

Everything marked ✅ below was actually run — outputs quoted are real. This document
is the executable version of the moonshot plan's M0 spikes (docs/moonshot-gating-plan.md).

---

## 0. Environment facts (verified)

| Fact | Value |
|---|---|
| Cadence license | `CDS_LIC_FILE=5280@<license-server>`, FlexNet v11.19.5, vendor daemon `cdslmd` UP |
| APD seats | feature **`SiP_Layout_Bundle_1`**: 8 total (3 in use at probe time). Also on server: SIP_WLCSP, Allegro_X_Designer, Allegro_PCB_Router_610, PCB_design_studio, OrbitIO_Sys_PlanC |
| Sigrity licensed | **PowerSI 8, PowerSI_II 8, PowerDC 7, CelsiusDC 7, CelsiusDC_G 7** (v2025.1, expire 02-nov-2026) |
| Sigrity NOT licensed | **XtractIM, OptimizePI** — absent from the server despite being installed. Drop them from the plan; Sigrity triangulation = PowerSI/PowerDC only |
| Ansys install | `C:\Program Files\ANSYS Inc\v261` — **completed 2026-07-20 23:45**, Electromagnetics Suite + Motor-CAD; `AnsysEM\siwave.exe`, `siwave_ng.exe`, `siwave_solver.exe`, `anstranslator.exe`, `EDB_RPC_Server.exe`, `check_feature.exe`, `EDBToGDS.exe`, `EDBDiff.exe` present |
| Ansys solve licenses | `elec_solve_siwave` 2 seats · `elec_solve_level1/2` 8 each · `level3` 2 · `anshpc_pack` 8 — **first headless SYZ solve verified working**. Missing: `al4apd`/ALinks (blocks .sip translation — see 3.4) |
| Ansys env (machine scope) | `ANSYSEM_ROOT261=C:\Program Files\ANSYS Inc\v261\AnsysEM` · `AWP_ROOT261=C:\Program Files\ANSYS Inc\v261` · `ANSYSLMD_LICENSE_FILE=1055@<license-server>` (ansyslmd.ini: same + web licensing enabled). Shells started before the install must re-set these in-session |
| Python | 3.11.9 + **pyedb 0.80.2** + **pyaedt 1.3.0** installed; `import pyedb` ✅, `import ansys.aedt.core` ✅ (`import pyaedt` is NOT the 1.x path); `settings.SUPPORTED_EDB_IMPORT_FORMATS = ['brd','mcm','sip','gds','xml','dxf','tgz','anf']` |
| Sample corpus | `share\pcb\toolbox\getting_started\panelization\{mcm,sip}_context\databases\sample.{mcm,sip}` — **saved by release 16.5 (2012)**; see rule 1 below |

---

## 1. Cadence APD 24.1 — feature by feature

### 1.0 Golden rules (each discovered the hard way — read before running anything)

1. **Uprev the sample DBs first.** Every 24.1 batch tool refuses the shipped 16.5-era
   samples (`SPMHDB-181` / "Failed to open the drawing", exit 2) until
   `dbdoctor.exe <design>` uprevs a **copy**. dbdoctor writes a `.orig` backup and
   drops `dbdoctor.log`, `dsuprev.log`, `signoise.log` in cwd.
2. **Never launch `apd.exe` for batch.** It is a 308 KB stub that spawns a detached
   `allegro.exe -apd` child and exits in 0.3 s — you can't wait on it or capture
   output. Always run **`allegro.exe -apd …`** directly.
3. **`-product` takes the FLEXlm feature name** (`SiP_Layout_Bundle_1`), **not** the
   SIP4160 product code from batchhelp. Without `-product`, `-nograph` suppresses the
   product-chooser dialog and APD aborts with the *misleading* message
   `No licenses available, exiting program.` even when seats are free.
4. **`exit` auto-saves a dirtied design.** After `axlDRCUpdate`, the trailing `exit`
   writes the design to disk without prompting — headless runs silently modify the
   DB. Work on copies, or open with `-readonly` when not intending writes.
5. **Killed sessions leave `<design>.lck`** and flush nothing (stdout is
   block-buffered). Timebox form-capable commands and clean up locks.
6. **SKILL gotchas:** `<` is infix-only (use `lessp` in prefix position); dbid
   attributes are lowercase (`design->drcs`, not `->DRCs`); `design->name` is nil on
   this DB's root dbid; your `ilinit` auto-loads into every run (use `-safe` for
   clean logs).

### 1.1 ✅ dbdoctor — uprev + headless DRC (the working DRC path)

```powershell
# in a scratch dir with a COPY of the design
C:\Cadence\SPB_24.1\tools\bin\dbdoctor.exe -drc_only sample.mcm
```
Observed: exits ~2 s, uprevs 16.5→24.x, runs the batch DRC engine
(16 threads), `Original DRC errors: 122 / Updated DRC errors: 122`, writes
`dbdoctor.log` + `batch_drc.log`. **No license drawn.** This is the M4
differential-DRC headless primary.

### 1.2 ✅ Headless SKILL (the core automation recipe)

```powershell
# wrapper.scr (3 lines):   skill load("probe.il")
#                          skill main()
#                          exit          <- mandatory or apd never terminates
C:\Cadence\SPB_24.1\tools\bin\allegro.exe -apd -product SiP_Layout_Bundle_1 `
    -s wrapper.scr -nograph sample.mcm
```
Observed: 4.1 s wall, clean self-exit, seat released, **no window**. SKILL `printf`
lands on **stdout and `apd.jrl`**. Probe read `axlDBGetDesign()`: 210 nets,
3 symbols, net names VDD/VSS/SIGNAL_189/… SKILL function reference (one .txt per
function): `share\pcb\examples\skill\DOC\FUNCS\`.

### 1.3 ✅ DRC marker readout via SKILL (feeds the M4 agreement matrix)

`axlDRCUpdate(t)` → returned 122; `axlDRCGetCount()` → 122; `design->drcs` → 122
marker dbids, each with **full structured data**, e.g. first marker:
`type "ASSEMBLY CONSTRAINTS", source "BONDWIRE_PIN_SPC", expected "75 UM",
actual "13.8 UM", name "Wire to Pin Spacing", xy (-4855.86 3539.72), violations
(dbid dbid), bBox (…)`. Everything the differential gate needs (rule id, expected,
actual, location, offenders) is programmatically readable headless.

### 1.4 ✅ extracta — extraction workhorse (accepts .sip; no seat drawn)

```powershell
C:\Cadence\SPB_24.1\tools\bin\extracta.exe sample.sip view.txt out.txt
```
- **Accepts `.mcm` AND `.sip`** (open question answered). Draws **no seat** (a PCB
  product license must exist on the server; it does).
- Format: `A!` header record (field names, `!`-delimited) → `J!` design-info record →
  `S!` data records. Empty fields are `!!`. `-s` = header only.
- Shipped views verified: `conn_bv.txt` (connectivity: nets, pins, vias, coords,
  padstacks, per-net R/L/C/Z/delay), `die_stack_view.txt` (6-member die stack:
  DIE/SPACER/INTERPOSER members, bump material, FLIP-CHIP orientation),
  `paksi_view.txt` (3 views in one file → needs 3 outfiles: LAYER cross-section with
  εr/σ/tanδ/thickness per layer, PAD_DEF, FULL_GEOMETRY with BOND_PAD flags).
- **Custom views work** with zero setup. Verified minimal view file:
  ```
  CONNECTIVITY
    NET_NAME != ''
    NET_NAME
    REFDES
    PIN_NUMBER
    PIN_X
    PIN_Y
    PAD_STACK_NAME
  END
  ```
  → `S!SIGNAL_63!D1!62!4354.93!4655.27!DIE_PAD!` — this is the pkgtk ingestion feed.
- `-d` dumps all **5057 legal field names** to `extract.log`; `-P` dumps property
  definitions (26 element types) to stdout; `-X` writes `<design>.xml`
  (`<net_list>/<net>/<pin>` logic view — ideal for graph cross-checks).

### 1.5 ✅ techfile — constraint mining (feeds M3 deck compiler)

```powershell
C:\Cadence\SPB_24.1\tools\bin\techfile.exe -w -i speuaxnr sample.sip rules.tcf
```
Observed: 172 KB XML (`cft:` namespace, FormatVersion 24.100, units µm) with exactly
the sections the deck compiler needs: `PhysicalCSet` (line ~1685), `SpacingCSet`
(~2613), `SameNetSpacingCSet` (~1873), `ElectricalCSet` (~1590), `NetClass`,
`Stackup`, plus ClassClass spacing-pair objects like
`<object Name="N:CRITICAL:N:HIGH CURRENT">`. No license drawn.

### 1.6 ✅ ipc2581_out — net-attributed manufacturing export

```powershell
C:\Cadence\SPB_24.1\tools\bin\ipc2581_out.exe sample.mcm -o out2581 -n -k -l -u MICRON
```
Observed: 444 KB `out2581.xml`, `revision="B"` (default 1.03; `-f 1.04` = rev C),
`<LogicalNet>` (net attribution), `<PadStackDef>`, `<Stackup>` all present. This is
the alternate geometry/netlist bridge into EDB (`Edb(edbpath='out2581.xml')`).

### 1.7 ✅ stream_out — GDS artwork (feeds the existing klayout lint engine)

```powershell
C:\Cadence\SPB_24.1\tools\bin\stream_out.exe -c layers.cnv -o pkg.sf -n TOP -u MICRONS sample.mcm
```
**Critical undocumented format** (wrong order silently yields an empty-but-valid
GDS): `.cnv` lines are exactly 4 whitespace-separated fields,
**`STREAM_LAYER DATATYPE CLASS SUBCLASS`**:
```
1 0 ETCH TOP_COND
2 0 ETCH BOT_COND
```
Observed: 101 KB GDS, gdstk-verified — `cell TOP, layers {(1,0): 426, (2,0): 1054}`,
1469 paths. (gdstk warns about record type FORMAT 0x36; harmless.)

### 1.8 ✅ diacheck — usage mapped; needs an XML die abstract

Bare run prints usage (`diacheck <die abstract file> [output file] [-nn]…`). Input
must be an **XML die abstract** per `share\pcb\text\tech\dieAbstract.xsd` /
`xdaAbstract.xsd` — **no sample ships anywhere in SPB_24.1**, and the `die60.txt`
files under sip_context are package DEVICE files, not die abstracts. To exercise it:
export a die abstract from a die source (Innovus/Integrity Planner) or hand-author a
minimal XML against the XSD. Non-conforming input → silent usage-print (no parse
error), so wrap it accordingly.

### 1.9 ❌ batch_drc.exe — dead end

Hangs silently (no output, no log, no license draw) in every direct invocation mode:
bare, `-help` ("Help is not available"), `<design>`, stdin-redirected. It is the DRC
engine that `dbdoctor -drc_only` drives internally (which writes `batch_drc.log`).
Use dbdoctor; don't burn more time here.

### 1.10 ⚠ AIF export — form-modal; bare `aif out` is NOT scriptable

`aif out` in a `.scr` under `-nograph` **hangs forever** (0 bytes output, 0-byte
journal — blocked on the suppressed AIF Export form; killed at 120 s, left a `.lck`).
Consequences: **extracta is the primary M2 ingestion path**, and AIF export needs one
of these (in order of preference):
- ⬜ **Record a GUI session once** (`allegro.exe -apd -record aif.scr`, do the AIF
  export by hand, inspect the recorded `.scr` for the form-field commands, then
  replay that full form-fill script under `-nograph`). This is the standard Allegro
  scripting pattern for form commands — test whether the replay works headless.
- ⬜ Hunt for a SKILL-level AIF writer (grep `share\pcb\examples\skill` and DOC/FUNCS
  for `aif`; the writer is OEM'd from Artwork and may expose no SKILL API — confirm).
- ⬜ Fallback: keep AIF as a documented GUI-export step; the automated pipeline runs
  on extracta views (which carry strictly more data anyway).

### 1.11 ⬜ Ball-map / die spreadsheet export (feeds M2.4 + M7 ground truth)

Same form-modal risk as AIF. Test in this order:
1. SKILL API (no forms): `axlSpreadsheetInit/Write/SetCell…` — write a ball-map
   report directly from `design->symbols`/pins in a headless SKILL run. Docs:
   `DOC\FUNCS\axlSpreadsheet*.txt`.
2. Recorded-form replay of `symbol to spreadsheet` / `bga text out` (as 1.10).
3. Plain SKILL report: iterate ball pads, `printf` designator/net/xy to CSV —
   always works; it just doesn't exercise the wizard.

### 1.12 ⬜ External-DRC injection (pkgtk findings inside APD, M4.4)

Headless SKILL run calling `axlDBCreateExternalDRC(…)` with one synthetic violation;
reopen in GUI to confirm a clickable marker exists. Doc: `DOC\FUNCS\axlDBCreateExternalDRC.txt`.
Note rule 4 (auto-save on exit) — this run *intends* a write, so do it on a copy.

### 1.13 ⬜ Live-session driving: `allegro_sendcmd.exe "<command>"`

Requires a running APD session (one exists: PID 40920, interactive). Send a benign
command (`zoom fit`) and verify it executes. This is the fallback channel if the
scheduled-task test (1.15) fails.

### 1.14 ⬜ SKILL defect injector v0 (feeds M2.5/M4.3)

`inject.il`: swap two net assignments on balls (or `axlDBReplaceProp` on a pin),
save-as revB, `extracta` both revs, `pkgtk diff` must catch it. First real
tool-differential benchmark case.

### 1.15 ⬜ Non-interactive session test (Ring-1 go/no-go)

Register a one-shot Windows Scheduled Task running recipe 1.2 with "run whether user
is logged on or not", from a `gated.env`-style wrapper that sets `CDS_LIC_FILE`.
Verify output + clean exit. If it fails → autologon + 1.13 posture decision.

### 1.16 ⬜ `report.exe` batch reports

`share\pcb\batchhelp\report.txt` documents a GUI-free report generator — try
netlist/pin reports as a third ingestion cross-check.

---

## 2. Sigrity 2025.1 (licensed subset: PowerSI, PowerDC, CelsiusDC)

XtractIM and OptimizePI are **not on the license server** — remove them from the
moonshot plan (M5.2 shrinks to PowerSI/PowerDC triangulation).

- ⬜ **2.1 Translator:** `Dsn2SpdCon.exe` (console, in Sigrity tools\bin) converts
  Allegro/APD DBs to Sigrity `.spd`. Run on the uprevved sample.sip; inspect .spd.
- ⬜ **2.2 PowerSI batch hello-world:** launch `PowerSI.exe` with a TCL script
  (`-tcl script.tcl` per Sigrity docs — confirm exact flag with `-help`, timeboxed):
  open translated .spd, run an SYZ-style extraction, save S-params. Verifies the
  second physics oracle end-to-end.
- ⬜ **2.3 PowerDC batch:** same pattern for a DC IR run (PowerDC seats: 7).
- ⬜ **2.4 BroadbandSPICE / snpcheck utilities** in Sigrity bin as extra
  Touchstone-side cross-checks (`ckt2snp.exe`, `snp*` tools) — inventory then test.

---

## 3. Ansys Electronics 2026 R1 — SIwave + pyedb

Install ✅ complete (2026-07-20 23:45). **Session gotcha:** shells started before the
install do NOT see the machine-scope env vars — always set in-session first:
`$env:ANSYSEM_ROOT261='C:\Program Files\ANSYS Inc\v261\AnsysEM'` +
`$env:ANSYSLMD_LICENSE_FILE='1055@<license-server>'` (a missing license var turns
failures into silent multi-minute hangs).

### 3.1 ✅ License inventory (server `1055@<license-server>`, ansyslmd v11.19.9, expiry 17-nov-2026)

Headless SIwave solving **is licensed with free capacity**:
`elec_solve_siwave` 2/2 free · `elec_solve_level1` 7/8 · `elec_solve_level2` 7/8 ·
`elec_solve_level3` 2/2 · `anshpc_pack` 6/8 (bare `anshpc` does not exist here — HPC
is pack-based) · `electronics_desktop` 9/10 · `electronics3d_gui` 8/10. Also present:
`siwave_level1` 2/0, `elec_solve_hfss` 4 seats. **Absent: `al4apd`** (see 3.4).
Query with either vendor's `lmutil lmstat` (identical results); the legacy
`ansysli_util -printavail` path is retired in Common Licensing ("action STATUS is not
supported") and exits 0 even on ERROR text. Handy: `AnsysEM\check_feature.exe
<feature>` prints ENABLED/DISABLED **with a real exit code** — a doctor building
block. Note: a stray SIwave GUI (PID 46672, started 23:48) holds one
`electronics3d_gui` seat on this machine — close it when noticed.

### 3.2 ✅ Synthetic EDB from scratch (license-free, the M5 parametric-ladder foundation)

`Edb(edbpath='plane_pair.aedb', version='2026.1')` → gRPC backend auto-selected
(`EDB_RPC_Server` starts ~5 s; checks out **nothing** — EDB authoring is
license-free). Verified working calls on 0.80.2:
`materials.add_conductor_material/add_dielectric_material`,
`stackup.add_layer(name, layer_type='signal'|'dielectric', material=…, thickness=…,
filling_material=…)` (**`filling_material`**, not the deprecated `fillMaterial`),
`modeler.create_rectangle(layer_name=…, net_name=…, lower_left_point=['0mm','0mm'],
upper_right_point=['10mm','10mm'])`, `save()`, `close()` (RPC session self-releases).

### 3.3 ✅ Reopen + query surface (what the verification tool consumes)

`stackup.layers` (thickness = float **meters**), `nets.netlist`,
`layout.primitives` with `.net_name`/`.layer_name`,
`.polygon_data.area()` (**method**, not property — returned 1e-4 m² for the 10×10 mm
plane). `edb.layout.bondwires` exists (Bondwire class) for the fidelity audit.

### 3.4 ⚠ `.sip` → EDB translation — BLOCKED (license-server work item), forensically diagnosed

`Edb(edbpath='sample.sip')` invokes `AnsysEM\anstranslator.exe`, which drives
Cadence's extracta. Three captured failure modes: (a) without
`C:\Cadence\SPB_24.1\tools\bin` on PATH → instant "Extracta version could not be
identified"; (b) pyedb default (`use_ppe=False` → `-ppe=false`) → instant exit −1
with a truncated log and no error text; (c) with PPE → writes its extracta control
files (14 views **including diestack** — die-stack data is in scope) then hangs
forever pre-license-checkout at a semaphore wait. The translator DLL carries the
legacy message "Cannot check out **al4apd** or siwave_level1 license"; `al4apd` is
absent from the server and `alinks_gui` reports "unsupported by licensed server"
(`siwave_level1` itself shows 2/0, so the root cause is the ALinks/al4apd path —
not fully pinned; the hang never even contacts the server). Controls: standalone
extracta on the same .sip works; a bogus IPC-2581 XML through the SAME anstranslator
completes the license dance in 2 s (draws `elec_solve_level1+2`).

**Action items:**
- ⬜ License admin: add a usable ALinks/Cadence-translator feature (`al4apd` /
  working `alinks_gui`) to `1055@<license-server>`; then rerun the translation +
  bondwire/annular-ring audit unchanged (scripts preserved in
  `%TEMP%\pkgtk-probe\pyedb\`).
- ⬜ Debug attempt meanwhile: `ANSOFT_EXTRACTA_DEBUG=1` run; try the `.mcm` instead
  of `.sip`; try `Edb(…, use_ppe=True)` from pyedb.
- ✅ **Workaround exists today: the IPC-2581 bridge** — APD `ipc2581_out.exe` (1.6)
  → `Edb(edbpath='out2581.xml')`, which uses the licensed `elec_solve_level1/2`
  path. Fidelity vs native translation to be compared once .sip unblocks (bondwires
  likely lost in IPC-2581 — re-inject via `create_bondwire` if needed).

### 3.5 ✅ Padstack/annular-ring data path (M4)

On synthetic padstacks: `padstacks.create(padstackname=…, holediam='300um',
paddiam='500um', …)` + `padstacks.place(...)`, then reads:
`definitions[name].hole_diameter` (meters), `.hole_plating_ratio`,
`.pad_by_layer[layer].shape` ('circle') / `.parameters` ([0.0005]) → ring =
(500−300)/2 = 100 µm recoverable per layer. **pyedb 0.80.2 bug found:**
`pad_shape='Square'` raises `AttributeError` (str passed where PadGeometryType enum
expected, `grpc/database/padstacks.py:1286`) — only Circle creation works; the READ
path (what M4 needs on translated designs) is unaffected. Consider filing upstream.

### 3.6 ✅ First headless SYZ solve — END TO END (the M5 pipeline exists)

```
ports:  t = edb.excitation_manager.create_point_terminal(x, y, 'TOP', 'VDD', name='P1_VDD')
        r = edb.excitation_manager.create_point_terminal(x, y, 'BOT', 'GND', name='P1_ref')
        edb.excitation_manager.create_port(t, r, is_circuit_port=True, name='P1')
setup:  edb.simulation_setups.create_siwave_setup(name='syz', distribution='linear_count',
                                                  start_freq='1MHz', stop_freq='1GHz', step_freq=10)
exec:   edb.siwave.create_exec_file(add_syz=True, export_touchstone=True)   # + prepend 'SetNumCpus 4' manually
solve:  siwave_ng.exe plane_pair.aedb plane_pair.exec -formatOutput -useSubdir
```
Observed: exit 0 in ~90 s; `plane_pair_touchstone.s2p` valid (10 points 1 MHz–1 GHz,
S21≈0.99996 — plausible plane pair); results in `.siwaveresults\0000\` (.syzinfo,
.Sbin/.Ybin/.Zbin, solver logs). **License draw verbatim from licdebug:** CHECKOUT
`elec_solve_siwave` + `elec_solve_level2` + `elec_solve_level1` + `HPC_PARALLEL`×4;
one non-fatal DENIED `electronics_ai_plus` (web-licensing token noise — cosmetic).
Gotchas: touchstone lands next to the .aedb, not in .siwaveresults;
`create_exec_file` does not emit SetNumCpus; `siwave_ng` usage (stderr):
`siwave_ng <ANF|EDB|siw> <exec> [-formatOutput] [-respectSlnDirDb] [-l <log>]
[-WaitForLicense]` — **`-WaitForLicense` gives Ring-1 free license queuing**.

### Remaining Ansys TODO

- 3.7 ⬜ **DCIR headless**: sources via `edb.siwave` / config-2.0 JSON →
  `create_siwave_dc_setup` → solve (`ExecDcSim`) → `export_dc_report` /
  element data (incl. Bondwires category).
- 3.8 ⬜ **Resonant-mode batch** (`ExecResModeSim` in the exec — SPIKE-E) vs SYZ
  |Z| peak-picking on the 3.6 plane pair (analytic f₁₀ for 10×10 mm/FR4 ≈ 7.1 GHz —
  extend the sweep and compare against `pkgtk pdn`'s cavity model: **the first
  cavity-vs-solver gate point**).
- 3.9 ⬜ **Materials/roughness**: `add_djordjevicsarkar_dielectric`,
  `assign_roughness_model('huray', …)`; confirm survive save/reopen.
- 3.10 ⬜ **Config 2.0 JSON path**: `edb.configuration.load(cfg)/run()` — the
  backend-neutral setup route the moonshot standardizes on.
- 3.11 ⬜ **`pyedb.siwave.Siwave` desktop-COM** (`Siwave('2026.1')`,
  `open_project`, `export_element_data`) — report fallback if batch outputs prove
  GUI-only.
- 3.12 ⬜ **Touchstone → pkgtk gate**: `ts_gate.gate('plane_pair_touchstone.s2p')`
  — solver output through its own physics gate (M6.1's first data point).
- 3.13 ⬜ **IPC-2581 import**: `Edb(edbpath='out2581.xml')` on the 1.6 export —
  the working bridge today; audit nets/layers/padstacks vs extracta truth.
- 3.14 ⬜ **EDBToGDS.exe / EDBDiff.exe** (found in AnsysEM): potential extra
  geometry bridge + EDB regression diffing — inventory their CLIs.

---

## 4. What these feed

| Checklist item | Moonshot milestone |
|---|---|
| 1.1–1.3 (dbdoctor DRC + SKILL + marker readout) | M0a SPIKE-A ✅ answered → M4 differential DRC |
| 1.4 extracta (.sip ✅, custom views ✅) | M0a SPIKE-B ✅ answered → M2 primary ingestion |
| 1.5 techfile ✅ | M3 deck compiler input format confirmed |
| 1.6 ipc2581 / 1.7 stream_out ✅ (.cnv format) | M4 geometry bridges |
| 1.10 AIF form-modal ⚠ | M0a SPIKE-D answered (negative) → M2 reroute: extracta primary, AIF via form-record or GUI |
| 2.x Sigrity | M0a SPIKE-F (license half answered: PowerSI/PowerDC yes, XtractIM no) |
| 3.2/3.3/3.5 pyedb authoring+query ✅ | M4/M5 API surface confirmed |
| 3.4 .sip→EDB ⚠ license blocker | M0b SPIKE-C (workaround: IPC-2581 bridge; license-admin ticket filed) |
| 3.6 SYZ end-to-end ✅ | M0b SPIKE-E half answered → M5 pipeline proven |
| 3.8 resonant mode / 3.12 ts_gate | first cavity-vs-solver + solver-vs-gate data points |
| 1.15 scheduled task | Ring-1 go/no-go |
