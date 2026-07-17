"""AIF (Artwork Interchange Format) parser -> Connectivity Graph.

AIF is an INI-style ASCII format for die / bondshell / BGA data. A conformant parser
skips sections it does not recognize; we go further and preserve unknown sections
losslessly in ``extras`` so nothing is silently dropped.

References fetched into reference/aif/ (cite: artwork.com/package/aif). The NETLIST row
layout used here is documented and simplified; see reference/aif/README.md.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from pkgtk.schemas.graph import ConnectivityGraph, Edge, Grid, Node

_KNOWN = {"DATABASE", "DIE", "PADS", "NETLIST"}
_DESIGNATOR = re.compile(r"^([A-Za-z]+)(\d+)$")


@dataclass
class AifDocument:
    graph: ConnectivityGraph
    extras: dict[str, list[str]] = field(default_factory=dict)


def _read_text(path: str | Path) -> str:
    raw = Path(path).read_bytes()
    for enc in ("utf-8", "latin-1"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("latin-1", errors="replace")


def _split_sections(text: str) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {}
    current: str | None = None
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith((";", "#")):
            continue
        if stripped.startswith("[") and stripped.endswith("]"):
            current = stripped[1:-1].strip().upper()
            sections.setdefault(current, [])
            continue
        if current is not None:
            sections[current].append(stripped)
    return sections


def _kv(lines: list[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in lines:
        if "=" in line:
            k, v = line.split("=", 1)
            out[k.strip()] = v.strip()
    return out


def parse_aif(path: str | Path) -> AifDocument:
    text = _read_text(path)
    sections = _split_sections(text)

    db = _kv(sections.get("DATABASE", []))
    die = _kv(sections.get("DIE", []))
    units = db.get("Units", "um")
    design = die.get("Name", Path(path).stem)
    rev = db.get("Version", "0")

    die_pads: list[Node] = []
    nets: list[Node] = []
    balls: list[Node] = []
    edges: list[Edge] = []
    seen_pads: set[str] = set()
    seen_nets: set[str] = set()

    for row in sections.get("NETLIST", []):
        parts = row.split()
        if len(parts) < 7:
            continue
        net, pad, dx, dy, ball, bx, by = parts[:7]
        net_id = f"net_{net}"
        if pad not in seen_pads:
            die_pads.append(Node(id=pad, kind="die_pad", name=pad,
                                 xy=[float(dx), float(dy)]))
            seen_pads.add(pad)
        if net_id not in seen_nets:
            nets.append(Node(id=net_id, kind="substrate_net", name=net))
            seen_nets.add(net_id)
        grid = None
        m = _DESIGNATOR.match(ball)
        if m:
            grid = Grid(row=m.group(1).upper(), col=int(m.group(2)))
        balls.append(Node(id=ball, kind="ball", name=net, grid=grid,
                          xy=[float(bx), float(by)]))
        edges.append(Edge(source=pad, target=net_id, kind="die_pad__substrate_net"))
        edges.append(Edge(source=net_id, target=ball, kind="substrate_net__ball"))

    graph = ConnectivityGraph(
        design=design, rev=rev, source_files=[Path(path).name], units=units,
        nodes=die_pads + nets + balls, edges=edges,
    )
    extras = {name: lines for name, lines in sections.items() if name not in _KNOWN}
    return AifDocument(graph=graph, extras=extras)
