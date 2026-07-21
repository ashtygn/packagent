---
name: apd-headless
description: Drive Cadence APD 24.1 headless - SKILL batch scripts, extracta, IPC-2581/GDS export, headless DRC. Verified recipes with the licensing, locking, and format pitfalls pre-solved. Use for any batch APD/Allegro automation task.
---

# apd-headless — verified Cadence APD 24.1 batch recipes

Root: `%PKGTK_APD_ROOT%` (default `C:\Cadence\SPB_24.1`), executables in `tools\bin`.
Offline command docs: `share\pcb\batchhelp\*.txt`; SKILL function reference:
`share\pcb\examples\skill\DOC\FUNCS\<fn>.txt`.

## Core recipes

```
# SKILL batch - wrapper.scr is exactly these three lines:
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

## Hard-won rules — violating these wastes hours

1. **Copies only, always.** Batch SKILL `exit` auto-saves a dirtied design with no
   prompt. Never touch an original, a design with a `<design>.lck` file, or a live
   GUI process.
2. Launch `allegro.exe -apd`, **never `apd.exe`** (a detaching stub you can't wait on).
3. `-product` takes the **FLEXlm feature name** (e.g. `SiP_Layout_Bundle_1`).
   Missing/wrong `-product` under `-nograph` aborts with the misleading message
   `No licenses available` even when seats are free.
4. Old databases need `dbdoctor.exe <copy>` first (`SPMHDB-181` = needs uprev).
5. Form-opening console commands (e.g. bare `aif out`) **hang forever** under
   `-nograph` with zero output. Timebox every run; kill only PIDs you started;
   clean up `.lck` files after kills.
6. `stream_out` `.cnv` format (undocumented): 4 whitespace fields per line, order
   `STREAM_LAYER DATATYPE CLASS SUBCLASS`. Wrong order = silently empty GDS. Some
   designs need `-F` (stale degas shapes error SPMHSO-1).
7. SKILL language traps: `<` is infix-only (use `lessp`); dbid attributes are
   lowercase (`design->drcs`); `printf` is nil-safe with `%L` not `%s`; capture
   names BEFORE `axlDeleteObject` (dbids go nil). After `axlDRCUpdate` in-session,
   markers may not enumerate - save + reopen, and call `axlVisibleDesign(t)` before
   reading markers (invisible layers are silently skipped). Layer strings must
   match the design's real subclasses (`SURFACE` vs `TOP` varies by design).
8. extracta: custom view files = `VIEWNAME` / optional filters (`NET_NAME != ''`) /
   field names / `END`. Field list via `extracta -d design` → `extract.log`. Output
   is `!`-delimited A/J/S records; pin views also drag in GEO rows - filter rows
   with REFDES+PIN_NUMBER.

## Bridges

Cadence `.sip/.mcm` → EDB translation needs an ALinks-class license the server may
not carry - the working bridge to SIwave is IPC-2581: `ipc2581_out.exe` then
`Edb(edbpath='out.xml')`. Convert extracta connectivity to a pkgtk graph with
`python scripts/extracta_to_graph.py conn.txt out.json`.
