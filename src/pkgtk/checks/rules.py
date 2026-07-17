"""The ball-map checks. See docs/checks-spec.md (normative).

Each check is ``(graph, config, adj) -> list[Violation]``, pure and I/O-free.
"""

from __future__ import annotations

import re

from pkgtk.checks.common import (
    CHECK_VERSION,
    Adjacency,
    RunConfig,
    alphabet_for,
    row_index,
)
from pkgtk.schemas.graph import ConnectivityGraph, Node
from pkgtk.schemas.violation import LogicalLocation, Violation


def _v(rule_id: str, *, node_id: str | None = None, net: str | None = None,
       measured=None, required=None, severity: str = "hard") -> Violation:
    return Violation(
        rule_id=rule_id,
        severity=severity,
        location=LogicalLocation(kind="logical", node_id=node_id, net=net),
        measured=(str(measured) if measured is not None else None),
        required=(str(required) if required is not None else None),
        check_version=CHECK_VERSION,
    )


def _ball_interface(ball: Node, adj: Adjacency) -> str | None:
    if ball.interface:
        return ball.interface
    for net in adj.nets_of_ball(ball.id):
        if net.interface:
            return net.interface
    return None


def _ball_role(ball: Node, adj: Adjacency) -> str | None:
    if ball.role:
        return ball.role
    nets = adj.nets_of_ball(ball.id)
    return nets[0].role if nets else None


def check_bijection(graph: ConnectivityGraph, config: RunConfig, adj: Adjacency):
    out: list[Violation] = []
    for ball in adj.nodes_of_kind("ball"):
        nets = adj.nets_of_ball(ball.id)
        distinct = sorted({n.id for n in nets})
        if len(distinct) >= 2:
            out.append(_v("bijection.multi_assignment", node_id=ball.id,
                          measured=len(distinct), required=1))
    for net in adj.nodes_of_kind("substrate_net"):
        if net.role in ("gnd", "pwr"):
            continue
        if net.name in config.multi_ball_allow:
            continue
        balls = adj.balls_of_net(net.id)
        if len(balls) >= 2:
            out.append(_v("bijection.multi_ball_signal", net=net.name,
                          measured=len(balls), required=1))
    return out


def check_grounds(graph: ConnectivityGraph, config: RunConfig, adj: Adjacency):
    out: list[Violation] = []
    balls = adj.nodes_of_kind("ball")
    for interface, req in config.grounds.items():
        in_iface = [b for b in balls if _ball_interface(b, adj) == interface]
        actual = sum(1 for b in in_iface if _ball_role(b, adj) == "gnd")
        if req.min_gnd is not None:
            required = req.min_gnd
        elif req.gnd_ratio is not None:
            required = int(len(in_iface) * req.gnd_ratio)
        else:
            continue
        if actual < required:
            out.append(_v("grounds.missing", net=interface,
                          measured=actual, required=required))
    return out


def check_diffpairs(graph: ConnectivityGraph, config: RunConfig, adj: Adjacency):
    out: list[Violation] = []
    nets = adj.nodes_of_kind("substrate_net")
    names = {n.name for n in nets if n.name}
    alphabet = alphabet_for(config.alphabet)

    def ball_grid_of_net(net_name: str):
        for net in nets:
            if net.name != net_name:
                continue
            for b in adj.balls_of_net(net.id):
                if b.grid:
                    return b.grid
        return None

    for net in nets:
        if not net.name:
            continue
        for pos_pat, neg_tmpl in config.pair_patterns:
            m = re.search(pos_pat, net.name)
            if not m:
                continue
            partner = m.expand(neg_tmpl)
            if partner not in names:
                out.append(_v("diffpair.missing_partner", net=net.name,
                              required=partner))
                continue
            if config.adjacency_required:
                g1, g2 = ball_grid_of_net(net.name), ball_grid_of_net(partner)
                if g1 and g2:
                    d = max(
                        abs(row_index(g1.row, alphabet) - row_index(g2.row, alphabet)),
                        abs(g1.col - g2.col),
                    )
                    if d != 1:
                        out.append(_v("diffpair.not_adjacent", net=net.name,
                                      measured=d, required=1))
    return out


def _members_by_group(graph: ConnectivityGraph) -> dict[str, list[Node]]:
    groups: dict[str, list[Node]] = {}
    for n in graph.nodes:
        if n.match_group:
            groups.setdefault(n.match_group, []).append(n)
    return groups


def check_matchgroups(graph: ConnectivityGraph, config: RunConfig, adj: Adjacency):
    out: list[Violation] = []
    for group, members in _members_by_group(graph).items():
        req = config.match_groups.get(group)
        if req and req.count is not None and len(members) != req.count:
            out.append(_v("matchgroup.incomplete", net=group,
                          measured=len(members), required=req.count))
        ifaces = sorted({m.interface for m in members if m.interface})
        if len(ifaces) >= 2:
            out.append(_v("matchgroup.interface_split", net=group,
                          measured=",".join(ifaces)))
        domains = sorted({m.domain for m in members if m.domain})
        if len(domains) >= 2:
            out.append(_v("matchgroup.domain_split", net=group,
                          measured=",".join(domains)))
    return out


def check_domains(graph: ConnectivityGraph, config: RunConfig, adj: Adjacency):
    out: list[Violation] = []
    for net in adj.nodes_of_kind("substrate_net"):
        if net.name in config.bridge_nets or net.domain == "bridge":
            continue
        domains = sorted({b.domain for b in adj.balls_of_net(net.id) if b.domain})
        if len(domains) >= 2:
            out.append(_v("domain.crossing", net=net.name,
                          measured=",".join(domains)))
    return out


def check_floating(graph: ConnectivityGraph, config: RunConfig, adj: Adjacency):
    out: list[Violation] = []
    for pad in adj.nodes_of_kind("die_pad"):
        reachable = adj.reachable(pad.id)
        if not any(adj.by_id[i].kind == "ball" for i in reachable):
            out.append(_v("floating.die_pad", node_id=pad.id))
    for ball in adj.nodes_of_kind("ball"):
        if ball.role == "nc":
            if adj.nets_of_ball(ball.id):
                out.append(_v("nc.collision", node_id=ball.id))
            continue
        if not adj.nets_of_ball(ball.id):
            out.append(_v("floating.ball_no_net", node_id=ball.id))
    return out


def check_duplicates(graph: ConnectivityGraph, config: RunConfig, adj: Adjacency):
    out: list[Violation] = []
    grid_seen: dict[str, int] = {}
    for ball in adj.nodes_of_kind("ball"):
        if ball.grid:
            key = f"{ball.grid.row}{ball.grid.col}"
            grid_seen[key] = grid_seen.get(key, 0) + 1
    for key, count in grid_seen.items():
        if count >= 2:
            out.append(_v("duplicate.ball_grid", net=key, measured=count, required=1))
    name_seen: dict[str, int] = {}
    for pad in adj.nodes_of_kind("die_pad"):
        if pad.name:
            name_seen[pad.name] = name_seen.get(pad.name, 0) + 1
    for name, count in name_seen.items():
        if count >= 2:
            out.append(_v("duplicate.die_pad", net=name, measured=count, required=1))
    return out


def check_depop(graph: ConnectivityGraph, config: RunConfig, adj: Adjacency):
    out: list[Violation] = []
    depop = config.depop
    balls = [b for b in adj.nodes_of_kind("ball") if b.grid]
    if not balls:
        return out
    alphabet = alphabet_for(config.alphabet)
    at: dict[tuple[int, int], Node] = {}
    for b in balls:
        at[(row_index(b.grid.row, alphabet), b.grid.col)] = b
    rmax = max(ri for ri, _ in at)
    cmax = max(c for _, c in at)

    cmax_i = cmax - 1  # 0-based max column index

    def is_depop(ri: int, col: int) -> bool:
        ci = col - 1
        if depop.kind == "corner" and depop.n > 0:
            n = depop.n
            return (ri < n or ri > rmax - n) and (ci < n or ci > cmax_i - n)
        if depop.kind == "ring" and depop.width > 0:
            w = depop.width
            return ri < w or ri > rmax - w or ci < w or ci > cmax_i - w
        if depop.kind == "list":
            return [ri, col] in depop.positions
        return False

    for (ri, col), ball in at.items():
        if is_depop(ri, col) and ball.role != "nc":
            out.append(_v("depop.not_nc", net=f"{ball.grid.row}{ball.grid.col}",
                          measured=ball.role or "none", required="nc"))
    return out


REGISTRY = [
    check_bijection,
    check_grounds,
    check_diffpairs,
    check_matchgroups,
    check_domains,
    check_floating,
    check_duplicates,
    check_depop,
]
