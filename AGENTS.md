# AGENTS.md — operating manual for AI agents driving pkgtk

pkgtk is a deterministic, read-only verification toolkit for IC-package/substrate
design. Every capability is a headless CLI with machine-readable output — this repo is
designed to be driven by agents. The constraints in `CLAUDE.md` apply to ALL agents
(golden fixtures are human-only, `make ci` green before claiming done, frozen schemas,
no network at test time).

## Exit-code contract (every pkgtk CLI)

`0` = clean · `1` = violations/changes found (**success-with-findings — never treat as
a crash**) · `2` = usage error · `3` = internal (reserved). Prefer `--json` flags for
parseable output.

## Setup + verify the world works

```
pip install -e ".[dev]"
make ci          # ruff + pytest — must be green before AND after your changes
```

## Core verification commands

```
pkgtk verify graph.json [--config cfg.json] --json     # ball-map checks (8 families)
pkgtk diff revA.json revB.json --json                  # semantic ECO diff
pkgtk check design.gds --deck deck.yaml --layers layers.yaml \
      --out-json v.json --out-lyrdb v.lyrdb            # geometry lint (klayout)
pkgtk pdn --png z.png                                  # PDN cavity |Z| curve
pkgtk escape --deck deck.yaml --pitch-um 800 ...       # escape-capacity verdict
pkgtk template map.json --template iface.yaml          # template compliance
python scripts/extracta_to_graph.py conn.txt out.json  # Cadence extracta → graph
python scripts/pinmap_crosscheck.py graph.json sheet.xlsx --sheet S \
      --ball-col "PIN NUMBER" --net-col NETNAME        # graph vs spreadsheet
```

Always pass `--out-lyrdb` explicitly to `pkgtk check` (otherwise it writes to CWD).

## Driving Cadence APD 24.1 headless (verified recipes)

Root: `%PKGTK_APD_ROOT%` (default `C:\Cadence\SPB_24.1`), executables in `tools\bin`.
Offline command docs: `share\pcb\batchhelp\*.txt`. SKILL function reference:
`share\pcb\examples\skill\DOC\FUNCS\<fn>.txt`.

```
# SKILL batch — the core recipe. wrapper.scr is exactly:
#   skill load("job.il")
#   skill main()
#   exit                      <- MANDATORY or the process never terminates
allegro.exe -apd -product SiP_Layout_Bundle_1 -s wrapper.scr -nograph design.mcm

extracta.exe design.sip view.txt out.txt      # extraction; draws no license seat
techfile.exe -w -i speuaxnr design.sip rules.tcf   # constraint export (XML)
ipc2581_out.exe design.mcm -o out -n -k -l -u MICRON
stream_out.exe -c layers.cnv -o pkg.sf -n TOP -u MICRONS design.mcm
dbdoctor.exe -drc_only design.mcm             # headless DRC (the working path)
```

**Hard-won rules — violate these and you will waste hours:**

1. **Copies only, always.** Batch SKILL `exit` AUTO-SAVES a dirtied design with no
   prompt. Never operate on an original; never touch a design open in a live session
   (check for `<design>.lck`), and never touch pre-existing GUI processes.
2. Launch `allegro.exe -apd`, **never `apd.exe`** (a detaching stub you can't wait on).
3. `-product` takes the **FLEXlm feature name** (e.g. `SiP_Layout_Bundle_1`), not a
   product code. Missing/wrong `-product` under `-nograph` aborts with the misleading
   message `No licenses available` even when seats are free.
4. Old databases need `dbdoctor.exe <copy>` first (`SPMHDB-181` = needs uprev).
5. Form-opening console commands (e.g. bare `aif out`) **hang forever** under
   `-nograph` with zero output. Timebox every run; kill only PIDs you started; clean
   up `.lck` files after kills.
6. `stream_out` `.cnv` format (undocumented): 4 whitespace fields per line, order
   `STREAM_LAYER DATATYPE CLASS SUBCLASS`. Wrong order = silently empty GDS. Some
   designs need `-F` (stale degas shapes error SPMHSO-1).
7. SKILL: `<` is infix-only (use `lessp`); dbid attributes are lowercase
   (`design->drcs`); `printf` nil-safe with `%L` not `%s`; capture names BEFORE
   `axlDeleteObject` (dbids go nil). After `axlDRCUpdate` in-session, markers may not
   enumerate — save + reopen, and call `axlVisibleDesign(t)` before reading markers
   (invisible layers are silently skipped). Layer strings must match the design's
   real subclasses (`SURFACE` vs `TOP` varies by design).
8. extracta: custom view files = `VIEWNAME` / optional filters (`NET_NAME != ''`) /
   field names / `END`. Field list via `extracta -d design` → `extract.log`. Output is
   `!`-delimited A/J/S records; pin views also drag in GEO rows — filter rows with
   REFDES+PIN_NUMBER.

## Driving Ansys SIwave 2026 R1 headless (verified recipes)

Set in-session first (machine-scope vars are not inherited by pre-existing shells;
missing license var = silent multi-minute hangs):

```powershell
$env:ANSYSEM_ROOT261 = 'C:\Program Files\ANSYS Inc\v261\AnsysEM'
$env:AWP_ROOT261     = 'C:\Program Files\ANSYS Inc\v261'
$env:ANSYSLMD_LICENSE_FILE = '<port>@<license-server>'   # site-specific
```

pyedb 0.80.2 / pyaedt 1.3.0 (`import pyedb`, `import ansys.aedt.core` — NOT
`import pyaedt`). EDB authoring is license-free; solves draw `elec_solve_siwave` +
`elec_solve_level1/2`.

```
# Build a structure from scratch (no license), add ports + SYZ setup, then solve:
# edb.excitation_manager.create_point_terminal(...) + create_port(t, r, is_circuit_port=True)
# edb.simulation_setups.create_siwave_setup(name=..., distribution='linear_count', ...)
# edb.siwave.create_exec_file(add_syz=True, export_touchstone=True)  # + prepend 'SetNumCpus 4'
siwave_ng.exe design.aedb design.exec -formatOutput -useSubdir [-WaitForLicense]
```

Touchstone lands NEXT TO the .aedb, not in `.siwaveresults`. Gate every solver
touchstone with `pkgtk`'s `ts_gate.gate()`. Known blocker: Cadence `.sip/.mcm → EDB`
translation needs an ALinks-class license the server may not carry — the working
bridge is IPC-2581 (`ipc2581_out.exe` → `Edb(edbpath='out.xml')`).

## Key documents

- Demo run-of-show + talk track: `docs/DEMO_SCRIPT.md` (the demo driver `demo.cmd` is
  a local stage artifact — its location is listed there).
- Bring-up recipes with real observed outputs: `docs/tool-bringup-checklist.md`.
- Roadmap: `docs/moonshot-gating-plan.md`.

## Non-negotiables for any agent in this repo

- Never modify `fixtures/golden/**` (human-only; `GOLDEN_EDIT=1` is the human's
  escape hatch, not yours). If a golden looks wrong: stop and report.
- Never commit without green `make ci`. Never push without explicit human sign-off.
- Customer/NDA design data (anything not generated by this repo's own synth code or
  shipped by a vendor as demo content) must never enter the repo, its artifacts, or
  any public output. When in doubt: scratch dirs outside the repo, and ask.
- A flagged gap is fine; a silent wrong answer is fatal. Surface what you skipped.
