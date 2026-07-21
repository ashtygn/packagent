"""extracta_to_graph.py — Cadence extracta CONNECTIVITY dump -> ConnectivityGraph.

Input: the '!'-delimited output of extracta run with a view of
    CONNECTIVITY / NET_NAME != '' / NET_NAME REFDES PIN_NUMBER PIN_X PIN_Y
    PAD_STACK_NAME / END
Records: A! = field-name header, J! = job header (design path, units),
S! = data. Because PAD_STACK_NAME is also a GEO-group field, extracta emits
S records for vias/geometry with empty REFDES/PIN_NUMBER; only rows with a
REFDES *and* a PIN_NUMBER are pins and are used here.

HEURISTICS (printed loudly at runtime, see --help):
  * role from net name (case-insensitive prefix): VDD* -> pwr,
    VSS*/GND* -> gnd, else signal.
  * tier from PAD_STACK_NAME: padstacks whose name starts with 'BGA'
    -> ball; every other component pin (die padstacks like DIE_PAD /
    DIE60_UPPER / BUMPC4, and discrete 0402 passives) -> die_pad.
    Rule chosen after inspecting sample.sip: the only BGA component (IO1)
    uses padstack BGA_PAD; all dice use DIE*/BUMP* padstacks.
  * ball Grid parsed from PIN_NUMBER when it matches ^[A-Za-z]+\\d+$,
    else omitted.

Graph conventions mirror pkgtk.ingest.aif: net node id 'net_<name>',
edge kinds 'die_pad__substrate_net' and 'substrate_net__ball'.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from pkgtk.schemas.graph import ConnectivityGraph, Edge, Grid, Node

_DESIGNATOR = re.compile(r"^([A-Za-z]+)(\d+)$")

EXPECTED_FIELDS = [
    "NET_NAME",
    "REFDES",
    "PIN_NUMBER",
    "PIN_X",
    "PIN_Y",
    "PAD_STACK_NAME",
]


def role_for(net: str) -> str:
    u = net.upper()
    if u.startswith("VDD"):
        return "pwr"
    if u.startswith(("VSS", "GND")):
        return "gnd"
    return "signal"


def tier_for(pad_stack: str) -> str:
    return "ball" if pad_stack.upper().startswith("BGA") else "die_pad"


def build_graph(dump: Path, design: str, rev: str) -> ConnectivityGraph:
    units = None
    fields: list[str] | None = None
    pin_rows: list[list[str]] = []
    geo_rows = 0
    for line in dump.read_text(encoding="latin-1").splitlines():
        parts = line.split("!")
        tag = parts[0]
        if tag == "A":
            fields = [f for f in parts[1:] if f]
            if fields != EXPECTED_FIELDS:
                sys.exit(f"unexpected A-record fields {fields}; "
                         f"expected {EXPECTED_FIELDS}")
        elif tag == "J" and len(parts) > 9:
            units = parts[9]
        elif tag == "S":
            row = parts[1:7]
            if row[1] and row[2] and row[3] and row[4]:
                pin_rows.append(row)
            else:
                geo_rows += 1

    print(f"[adapter] {dump.name}: {len(pin_rows)} pin rows kept, "
          f"{geo_rows} non-pin S records skipped "
          "(via/geometry rows matched by GEO-group PAD_STACK_NAME)")
    print("[adapter] HEURISTIC role: net-name prefix VDD*->pwr, "
          "VSS*/GND*->gnd, else signal")
    print("[adapter] HEURISTIC tier: PAD_STACK_NAME startswith 'BGA' -> ball; "
          "everything else -> die_pad (incl. discrete 0402 passives)")
    print("[adapter] HEURISTIC grid: ball PIN_NUMBER matching "
          "^[A-Za-z]+\\d+$ -> Grid(row,col), else no grid")

    die_pads: dict[str, Node] = {}
    nets: dict[str, Node] = {}
    balls: dict[str, Node] = {}
    edges: dict[tuple[str, str, str], Edge] = {}
    tier_counts: dict[str, int] = {}

    for net, refdes, pin, px, py, pad_stack in pin_rows:
        net_id = f"net_{net}"
        role = role_for(net)
        if net_id not in nets:
            nets[net_id] = Node(id=net_id, kind="substrate_net",
                                name=net, role=role)
        pin_id = f"{refdes}.{pin}"
        tier = tier_for(pad_stack)
        key = f"{refdes}|{pad_stack}|{tier}"
        tier_counts[key] = tier_counts.get(key, 0) + 1
        xy = [float(px), float(py)]
        if tier == "ball":
            grid = None
            m = _DESIGNATOR.match(pin)
            if m:
                grid = Grid(row=m.group(1).upper(), col=int(m.group(2)))
            balls.setdefault(pin_id, Node(id=pin_id, kind="ball", name=net,
                                          xy=xy, grid=grid, role=role))
            ek = ("substrate_net__ball", net_id, pin_id)
            edges.setdefault(ek, Edge(source=net_id, target=pin_id, kind=ek[0]))
        else:
            die_pads.setdefault(pin_id, Node(id=pin_id, kind="die_pad",
                                             name=pin_id, xy=xy, role=role))
            ek = ("die_pad__substrate_net", pin_id, net_id)
            edges.setdefault(ek, Edge(source=pin_id, target=net_id, kind=ek[0]))

    for key in sorted(tier_counts):
        refdes, pad_stack, tier = key.split("|")
        print(f"[adapter]   {refdes:<12} padstack {pad_stack:<14} "
              f"-> {tier:<7} x{tier_counts[key]}")

    graph = ConnectivityGraph(
        design=design, rev=rev, source_files=[dump.name], units=units,
        nodes=list(die_pads.values()) + list(nets.values())
        + list(balls.values()),
        edges=list(edges.values()),
    )
    print(f"[adapter] graph: {len(die_pads)} die_pad, {len(nets)} "
          f"substrate_net, {len(balls)} ball nodes; {len(edges)} edges")
    return graph


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("dump", help="extracta CONNECTIVITY output (!-delimited)")
    ap.add_argument("out", help="output ConnectivityGraph JSON path")
    ap.add_argument("--design", default="sample", help="design name")
    ap.add_argument("--rev", default="A", help="revision label")
    args = ap.parse_args(argv)

    graph = build_graph(Path(args.dump), args.design, args.rev)
    Path(args.out).write_text(
        json.dumps(graph.model_dump(mode="json", exclude_none=True), indent=2),
        encoding="utf-8",
    )
    print(f"[adapter] wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
