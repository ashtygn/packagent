"""pinmap_crosscheck.py — ConnectivityGraph vs. pin-map spreadsheet cross-check.

Compares the ball tier of a pkgtk ConnectivityGraph against a hand-maintained
pin-map spreadsheet (xlsx sheet or a pre-flattened csv) and reports:

  * balls present in the sheet but missing from the DB graph
  * balls present in the DB graph but missing from the sheet
  * net-name mismatches (with 'case-only' / alias-resolved characterization)
  * optional coordinate mismatches (same units as the graph, default tol 1)

Ball designators are taken from each ball node's grid (row+col) when present,
else from the node id after the last '.', else the node id itself. Nets come
from substrate_net<->ball edges. Coordinates come from ball node xy.

Sheet input: .xlsx (needs --sheet; cached formula values are used, so
formula-driven exports from Google Sheets work) or .csv. Coordinates are read
either from one 'x, y' string column (--coord-col) or two numeric columns
(--x-col/--y-col). --write-cache-csv flattens the parsed sheet to a
ball,net,x,y csv for fast (<1s) reloads.

Exit codes follow pkgtk convention: 0 clean, 1 findings, 2 usage error.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from math import hypot
from pathlib import Path

import pandas as pd
from rich.console import Console
from rich.table import Table

from pkgtk.schemas.graph import ConnectivityGraph, Node

DETAIL_LIMIT = 20


def ball_designator(node: Node) -> str:
    if node.grid is not None:
        return f"{node.grid.row}{node.grid.col}".upper()
    return node.id.rsplit(".", 1)[-1].upper()


def load_db(graph_path: Path) -> tuple[ConnectivityGraph, dict[str, dict]]:
    graph = ConnectivityGraph.model_validate_json(graph_path.read_text("utf-8"))
    by_id = {n.id: n for n in graph.nodes}
    net_of: dict[str, str] = {}
    for e in graph.edges:
        src, tgt = by_id.get(e.source), by_id.get(e.target)
        if src is None or tgt is None:
            continue
        pair = {src.kind: src, tgt.kind: tgt}
        if {"ball", "substrate_net"} <= pair.keys():
            net = pair["substrate_net"]
            net_of[pair["ball"].id] = net.name or net.id.removeprefix("net_")
    balls: dict[str, dict] = {}
    for n in graph.nodes:
        if n.kind != "ball":
            continue
        des = ball_designator(n)
        if des in balls:
            raise SystemExit(f"duplicate ball designator in graph: {des}")
        balls[des] = {"net": net_of.get(n.id), "xy": n.xy, "node_id": n.id}
    return graph, balls


def parse_coord_pair(raw: object) -> tuple[float, float] | None:
    if raw is None or (isinstance(raw, float) and pd.isna(raw)):
        return None
    parts = str(raw).replace("(", "").replace(")", "").split(",")
    if len(parts) != 2:
        return None
    try:
        return float(parts[0]), float(parts[1])
    except ValueError:
        return None


def load_sheet(args: argparse.Namespace) -> tuple[dict[str, dict], list, list]:
    path = Path(args.sheet_file)
    if path.suffix.lower() == ".csv":
        df = pd.read_csv(path)
    else:
        df = pd.read_excel(path, sheet_name=args.sheet, header=0)
    want = [args.ball_col, args.net_col]
    if args.coord_col:
        want.append(args.coord_col)
    if args.x_col:
        want += [args.x_col, args.y_col]
    missing = [c for c in want if c not in df.columns]
    if missing:
        raise SystemExit(f"column(s) {missing} not in sheet; have {list(df.columns)}")

    rows: dict[str, dict] = {}
    duplicates: list[str] = []
    coord_errors: list[str] = []
    for _, row in df.iterrows():
        ball = row[args.ball_col]
        if pd.isna(ball) or str(ball).strip() == "":
            continue
        ball = str(ball).strip().upper()
        net = row[args.net_col]
        net = None if pd.isna(net) else str(net).strip()
        xy: tuple[float, float] | None = None
        if args.coord_col:
            xy = parse_coord_pair(row[args.coord_col])
            if xy is None:
                coord_errors.append(ball)
        elif args.x_col:
            try:
                xy = (float(row[args.x_col]), float(row[args.y_col]))
            except (TypeError, ValueError):
                coord_errors.append(ball)
        if ball in rows:
            duplicates.append(ball)
            continue
        rows[ball] = {"net": net, "xy": xy}
    return rows, duplicates, coord_errors


def load_aliases(path: Path | None) -> dict[str, str]:
    if path is None:
        return {}
    aliases: dict[str, str] = {}
    with path.open(newline="", encoding="utf-8") as fh:
        for rec in csv.reader(fh):
            if len(rec) < 2 or rec[0].strip().lower() == "alias":
                continue
            aliases[rec[0].strip()] = rec[1].strip()
    return aliases


def crosscheck(
    db: dict[str, dict],
    sheet: dict[str, dict],
    aliases: dict[str, str],
    tol: float,
    check_coords: bool,
) -> dict:
    def canon(name: str | None) -> str | None:
        return None if name is None else aliases.get(name, name)

    missing_in_db = sorted(set(sheet) - set(db))
    missing_in_sheet = sorted(set(db) - set(sheet))
    net_mismatches: list[dict] = []
    coord_mismatches: list[dict] = []
    alias_resolved: list[dict] = []
    for ball in sorted(set(db) & set(sheet)):
        db_net, sheet_net = db[ball]["net"], sheet[ball]["net"]
        if canon(db_net) != canon(sheet_net):
            note = ""
            if (db_net or "").casefold() == (sheet_net or "").casefold():
                note = "case-only"
            net_mismatches.append(
                {"ball": ball, "db_net": db_net, "sheet_net": sheet_net,
                 "note": note}
            )
        elif db_net != sheet_net:
            alias_resolved.append(
                {"ball": ball, "db_net": db_net, "sheet_net": sheet_net}
            )
        if check_coords and db[ball]["xy"] and sheet[ball]["xy"]:
            (dx, dy), (sx, sy) = db[ball]["xy"], sheet[ball]["xy"]
            dist = hypot(dx - sx, dy - sy)
            if dist > tol:
                coord_mismatches.append(
                    {"ball": ball, "db_xy": [dx, dy], "sheet_xy": [sx, sy],
                     "dist": round(dist, 3)}
                )
    return {
        "db_balls": len(db),
        "sheet_rows": len(sheet),
        "missing_in_db": missing_in_db,
        "missing_in_sheet": missing_in_sheet,
        "net_mismatches": net_mismatches,
        "coord_mismatches": coord_mismatches,
        "alias_resolved": alias_resolved,
    }


def render(report: dict, console: Console) -> None:
    summary = Table(title=f"pin-map cross-check — {report['design']} "
                          f"rev {report['rev']}")
    summary.add_column("category")
    summary.add_column("count", justify="right")
    summary.add_column("status")
    ok = "[green]OK[/green]"
    bad = "[red]MISMATCH[/red]"
    keys = ["missing_in_db", "missing_in_sheet", "net_mismatches",
            "coord_mismatches", "duplicates_in_sheet", "coord_parse_errors"]
    summary.add_row("balls in DB graph", str(report["db_balls"]), "")
    summary.add_row("rows in sheet", str(report["sheet_rows"]), "")
    for key in keys:
        n = len(report[key])
        summary.add_row(key.replace("_", " "), str(n), ok if n == 0 else bad)
    if report["alias_resolved"]:
        summary.add_row("alias-resolved matches",
                        str(len(report["alias_resolved"])), "")
    console.print(summary)

    def detail(title: str, items: list, fmt) -> None:
        if not items:
            return
        console.print(f"[bold]{title}[/bold] ({len(items)})")
        for item in items[:DETAIL_LIMIT]:
            console.print(f"  {fmt(item)}")
        if len(items) > DETAIL_LIMIT:
            console.print(f"  ... and {len(items) - DETAIL_LIMIT} more "
                          "(full list in --json report)")

    detail("Missing in DB", report["missing_in_db"], str)
    detail("Missing in sheet", report["missing_in_sheet"], str)
    detail(
        "Net mismatches", report["net_mismatches"],
        lambda m: f"{m['ball']}: DB={m['db_net']!r} sheet={m['sheet_net']!r}"
                  + (f"  [{m['note']}]" if m["note"] else ""),
    )
    detail(
        "Coordinate mismatches", report["coord_mismatches"],
        lambda m: f"{m['ball']}: DB={m['db_xy']} sheet={m['sheet_xy']} "
                  f"dist={m['dist']}",
    )
    detail("Duplicate sheet rows", report["duplicates_in_sheet"], str)
    detail("Unparseable coordinates", report["coord_parse_errors"], str)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("graph", help="ConnectivityGraph JSON path")
    ap.add_argument("sheet_file", help="pin-map spreadsheet (.xlsx or .csv)")
    ap.add_argument("--sheet", help="xlsx sheet name (required for .xlsx)")
    ap.add_argument("--ball-col", required=True, help="ball designator column")
    ap.add_argument("--net-col", required=True, help="net name column")
    ap.add_argument("--coord-col", help="single 'x, y' coordinate column")
    ap.add_argument("--x-col", help="numeric X column (with --y-col)")
    ap.add_argument("--y-col", help="numeric Y column (with --x-col)")
    ap.add_argument("--tol", type=float, default=1.0,
                    help="coordinate tolerance, graph units (default 1)")
    ap.add_argument("--alias-csv", type=Path,
                    help="csv of alias,canonical net-name pairs")
    ap.add_argument("--json", dest="json_out", type=Path,
                    help="write full JSON report here")
    ap.add_argument("--write-cache-csv", type=Path,
                    help="flatten parsed sheet to ball,net,x,y csv")
    args = ap.parse_args(argv)
    if args.coord_col and args.x_col:
        ap.error("--coord-col and --x-col/--y-col are mutually exclusive")
    if bool(args.x_col) != bool(args.y_col):
        ap.error("--x-col and --y-col must be given together")
    if Path(args.sheet_file).suffix.lower() != ".csv" and not args.sheet:
        ap.error("--sheet is required for xlsx input")

    t0 = time.perf_counter()
    graph, db = load_db(Path(args.graph))
    sheet, duplicates, coord_errors = load_sheet(args)
    check_coords = bool(args.coord_col or args.x_col)
    report = crosscheck(db, sheet, load_aliases(args.alias_csv),
                        args.tol, check_coords)
    report.update(
        design=graph.design, rev=graph.rev,
        duplicates_in_sheet=sorted(set(duplicates)),
        coord_parse_errors=coord_errors,
        coords_checked=check_coords, tol=args.tol,
        elapsed_s=round(time.perf_counter() - t0, 2),
    )
    findings = sum(
        len(report[k]) for k in
        ("missing_in_db", "missing_in_sheet", "net_mismatches",
         "coord_mismatches", "duplicates_in_sheet", "coord_parse_errors")
    )
    report["finding_count"] = findings

    if args.write_cache_csv:
        with args.write_cache_csv.open("w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["ball", "net", "x", "y"])
            for ball in sorted(sheet):
                xy = sheet[ball]["xy"] or ("", "")
                w.writerow([ball, sheet[ball]["net"], xy[0], xy[1]])

    console = Console()
    render(report, console)
    if args.json_out:
        args.json_out.write_text(json.dumps(report, indent=2), encoding="utf-8")
        console.print(f"JSON report -> {args.json_out}")
    verdict = ("[green]CLEAN — DB and sheet agree[/green]" if findings == 0
               else f"[red]{findings} finding(s)[/red]")
    console.print(f"{verdict}  ({report['elapsed_s']}s)")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
