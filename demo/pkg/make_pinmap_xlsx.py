"""Beat 3 — emit the 'hand-maintained spreadsheet' stand-in for PHOTON-X1.

Reads graph_photonx1.json and writes:
  * PHOTONX1_PINMAP.xlsx        — sheet PINLIST (PIN NUMBER / NETNAME / X / Y),
                                  faithful to the graph (cross-check: 0 findings)
  * PHOTONX1_PINMAP_drift.xlsx  — same sheet with 3 seeded drift errors:
      1. net-name typo on one signal ball        -> 1 net mismatch
      2. one ball row deleted                    -> 1 missing-in-sheet
      3. one X coordinate off by +2.0 mm (>tol)  -> 1 coordinate mismatch

Deterministic: rows sorted by (row letters, col); drift targets are fixed
indices into the sorted signal-ball list. No wall-clock randomness.

Usage: python make_pinmap_xlsx.py [outdir]
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from openpyxl import Workbook

OUTDIR = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent
GRAPH = OUTDIR / "graph_photonx1.json"

# Fixed drift targets (indices into the sorted signal-ball row list).
IDX_NET_TYPO = 100
IDX_ROW_DELETE = 500
IDX_COORD_DRIFT = 900
COORD_DRIFT_MM = 2.0  # crosscheck default tol is 1.0 graph unit (mm)


def load_rows() -> list[dict]:
    g = json.loads(GRAPH.read_text("utf-8"))
    by_id = {n["id"]: n for n in g["nodes"]}
    net_of: dict[str, str] = {}
    for e in g["edges"]:
        src, tgt = by_id.get(e["source"]), by_id.get(e["target"])
        if not src or not tgt:
            continue
        pair = {src["kind"]: src, tgt["kind"]: tgt}
        if {"ball", "substrate_net"} <= pair.keys():
            net = pair["substrate_net"]
            net_of[pair["ball"]["id"]] = net.get("name") or net["id"]
    rows = []
    for n in g["nodes"]:
        if n["kind"] != "ball":
            continue
        grid = n["grid"]
        des = f"{grid['row']}{grid['col']}"
        x, y = n["xy"]
        rows.append({
            "pin": des,
            "net": net_of.get(n["id"], ""),  # NC balls: blank net
            "x": x,
            "y": y,
            "role": n.get("role"),
            "_row": grid["row"],
            "_col": grid["col"],
        })
    rows.sort(key=lambda r: (len(r["_row"]), r["_row"], r["_col"]))
    return rows


def write_xlsx(rows: list[dict], path: Path) -> None:
    wb = Workbook()
    ws = wb.active
    ws.title = "PINLIST"
    ws.append(["PIN NUMBER", "NETNAME", "X", "Y"])
    for r in rows:
        ws.append([r["pin"], r["net"] or None, r["x"], r["y"]])
    wb.save(path)


def main() -> int:
    rows = load_rows()
    clean_path = OUTDIR / "PHOTONX1_PINMAP.xlsx"
    write_xlsx(rows, clean_path)
    print(f"clean pinmap : {clean_path} ({len(rows)} rows, sheet PINLIST)")

    signal = [r for r in rows if r["role"] == "signal"]
    typo, dele, drift = (signal[IDX_NET_TYPO], signal[IDX_ROW_DELETE],
                         signal[IDX_COORD_DRIFT])

    drifted = []
    for r in rows:
        if r is dele:
            continue  # error 2: row deleted from the sheet
        r2 = dict(r)
        if r is typo:  # error 1: net-name typo
            r2["net"] = r["net"] + "X"
        if r is drift:  # error 3: coordinate drift beyond tol
            r2["x"] = round(r["x"] + COORD_DRIFT_MM, 4)
        drifted.append(r2)

    drift_path = OUTDIR / "PHOTONX1_PINMAP_drift.xlsx"
    write_xlsx(drifted, drift_path)
    print(f"drift pinmap : {drift_path} ({len(drifted)} rows) — 3 seeded errors:")
    print(f"  1. net typo   @ {typo['pin']}: {typo['net']} -> {typo['net']}X")
    print(f"  2. row deleted @ {dele['pin']} (net {dele['net']})")
    print(f"  3. X drift    @ {drift['pin']}: {drift['x']} -> "
          f"{round(drift['x'] + COORD_DRIFT_MM, 4)} (+{COORD_DRIFT_MM} mm)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
