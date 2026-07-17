"""ECO diff engine: semantic change classification between two graphs.

Primary identity = net name; secondary = ball grid position. See docs/checks-spec.md
§diff for the taxonomy. All output is deterministically sorted for byte-stability.
"""

from __future__ import annotations

import re

from pkgtk.checks.common import Adjacency
from pkgtk.schemas.graph import ConnectivityGraph, Node

_DEFAULT_PAIRS = [["(.*)_P$", "\\1_N"]]


def _grid_str(node: Node) -> str | None:
    return f"{node.grid.row}{node.grid.col}" if node.grid else None


class _View:
    """Net-centric view of a graph: name -> net node, name -> position, etc."""

    def __init__(self, graph: ConnectivityGraph):
        self.graph = graph
        self.adj = Adjacency(graph)
        self.nets: dict[str, Node] = {}
        self.net_pos: dict[str, str] = {}
        self.pos_net: dict[str, str] = {}
        for net in self.adj.nodes_of_kind("substrate_net"):
            if not net.name:
                continue
            self.nets[net.name] = net
            balls = [b for b in self.adj.balls_of_net(net.id) if b.grid]
            balls.sort(key=lambda b: _grid_str(b))
            if balls:
                pos = _grid_str(balls[0])
                self.net_pos[net.name] = pos
                self.pos_net[pos] = net.name

    def interface(self, net_name: str) -> str | None:
        net = self.nets.get(net_name)
        return net.interface if net else None

    def domain(self, net_name: str) -> str | None:
        net = self.nets.get(net_name)
        return net.domain if net else None


def diff_graphs(
    graph_a: ConnectivityGraph,
    graph_b: ConnectivityGraph,
    pair_patterns: list[list[str]] | None = None,
) -> dict:
    a, b = _View(graph_a), _View(graph_b)
    pairs = pair_patterns or _DEFAULT_PAIRS
    changes: list[dict] = []

    names_a, names_b = set(a.nets), set(b.nets)

    def iface(name: str, primary: _View, other: _View) -> str | None:
        return primary.interface(name) or other.interface(name)

    for name in names_b - names_a:
        changes.append({"class": "added", "net": name,
                        "interface": b.interface(name)})
    for name in names_a - names_b:
        changes.append({"class": "removed", "net": name,
                        "interface": a.interface(name)})

    for name in names_a & names_b:
        pa, pb = a.net_pos.get(name), b.net_pos.get(name)
        if pa is not None and pb is not None and pa != pb:
            changes.append({"class": "net_moved", "net": name,
                            "from": pa, "to": pb, "interface": iface(name, b, a)})
        da, db = a.domain(name), b.domain(name)
        if da != db:
            changes.append({"class": "domain_changed", "net": name,
                            "from": da, "to": db, "interface": iface(name, b, a)})

    for pos in set(a.pos_net) & set(b.pos_net):
        na, nb = a.pos_net[pos], b.pos_net[pos]
        if na != nb:
            # interface of the ball position: prefer B's net interface, else A's.
            changes.append({"class": "ball_repurposed", "ball": pos,
                            "from": na, "to": nb,
                            "interface": b.interface(nb) or a.interface(na)})

    # pair_broken: a diff pair intact in A missing a partner in B.
    for name in a.nets:
        for pos_pat, neg_tmpl in pairs:
            m = re.search(pos_pat, name)
            if not m:
                continue
            partner = m.expand(neg_tmpl)
            if partner in names_a and partner not in names_b and name in names_b:
                changes.append({"class": "pair_broken", "net": name,
                                "partner": partner, "interface": iface(name, b, a)})

    # match_group_broken: invariant holds in A, fails in B.
    broken = _match_group_broken(graph_a, graph_b)
    for group, ifc in broken:
        changes.append({"class": "match_group_broken", "net": group,
                        "interface": ifc})

    changes.sort(key=lambda c: (c["class"], c.get("net") or c.get("ball") or ""))

    summary: dict[str, int] = {}
    by_interface: dict[str, dict[str, int]] = {}
    for c in changes:
        summary[c["class"]] = summary.get(c["class"], 0) + 1
        ifc = c.get("interface") or "(none)"
        by_interface.setdefault(ifc, {})
        by_interface[ifc][c["class"]] = by_interface[ifc].get(c["class"], 0) + 1

    return {
        "design": graph_b.design,
        "rev_a": graph_a.rev,
        "rev_b": graph_b.rev,
        "changes": changes,
        "summary": dict(sorted(summary.items())),
        "by_interface": {k: dict(sorted(v.items()))
                         for k, v in sorted(by_interface.items())},
    }


def _match_group_broken(graph_a: ConnectivityGraph, graph_b: ConnectivityGraph):
    from pkgtk.checks import RunConfig
    from pkgtk.checks.rules import check_matchgroups

    adj_a, adj_b = Adjacency(graph_a), Adjacency(graph_b)
    cfg = RunConfig()
    bad_a = {v.location.net for v in check_matchgroups(graph_a, cfg, adj_a)}
    bad_b = {v.location.net for v in check_matchgroups(graph_b, cfg, adj_b)}
    newly = sorted(bad_b - bad_a)
    out = []
    for group in newly:
        ifc = None
        for n in graph_b.nodes:
            if n.match_group == group and n.interface:
                ifc = n.interface
                break
        out.append((group, ifc))
    return out
