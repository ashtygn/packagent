"""Parameterized, seeded synthetic ball-map generator.

Produces a *clean* Connectivity Graph (zero violations by construction under the
matching run config) for benchmarks and demos. The benchmark harness then injects
one seeded defect per case. Determinism: output depends only on the parameters, so
regeneration is byte-stable.

Construction rules that keep the clean design violation-free:
- Signal balls come in diff pairs on adjacent columns (``*_P`` / ``*_N``); each maps to
  its own single net (bijection ok; partner exists and is grid-adjacent).
- Ground balls all attach to one shared ``GND`` net (role gnd is exempt from fan-out).
- Corner NxN positions are depopulated -> role ``nc`` with no net.
- No ball carries a ``domain`` (so domain-crossing never fires); die pads exist only for
  signal nets and always reach their ball (no floating die pads).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from pkgtk.checks.common import RunConfig, alphabet_for
from pkgtk.schemas.graph import ConnectivityGraph, Edge, Grid, Node


@dataclass
class GenParams:
    rows: int = 45
    cols: int = 45
    n_interfaces: int = 4
    depop_corner: int = 3
    gnd_period: int = 5  # every Nth column in a row is a ground
    alphabet: str = "full"
    seed: int = 0  # reserved; construction is already deterministic


def _row_label(index0: int, alphabet: str) -> str:
    base = len(alphabet)
    n = index0 + 1
    out = ""
    while n > 0:
        n, rem = divmod(n - 1, base)
        out = alphabet[rem] + out
    return out


def _in_corner(ri: int, ci: int, rmax: int, cmax_i: int, n: int) -> bool:
    if n <= 0:
        return False
    return (ri < n or ri > rmax - n) and (ci < n or ci > cmax_i - n)


@dataclass
class GeneratedDesign:
    graph: ConnectivityGraph
    config: RunConfig
    interfaces: list[str] = field(default_factory=list)


def generate(params: GenParams | None = None) -> GeneratedDesign:
    p = params or GenParams()
    alphabet = alphabet_for(p.alphabet)
    nodes: list[Node] = []
    edges: list[Edge] = []
    rmax = p.rows - 1
    cmax_i = p.cols - 1

    interfaces = [f"IF{i}" for i in range(p.n_interfaces)]
    cols_per_iface = max(1, p.cols // p.n_interfaces)

    def iface_of(col: int) -> str:
        idx = min((col - 1) // cols_per_iface, p.n_interfaces - 1)
        return interfaces[idx]

    gnd_ball_ids: list[str] = []
    gnd_count_per_iface: dict[str, int] = {i: 0 for i in interfaces}

    for ri in range(p.rows):
        row = _row_label(ri, alphabet)
        col = 1
        while col <= p.cols:
            ci = col - 1
            ball_id = f"{row}{col}"
            iface = iface_of(col)
            if _in_corner(ri, ci, rmax, cmax_i, p.depop_corner):
                nodes.append(Node(id=ball_id, kind="ball", name="NC",
                                  grid=Grid(row=row, col=col), role="nc",
                                  interface=iface))
                col += 1
                continue
            if col % p.gnd_period == 0:
                nodes.append(Node(id=ball_id, kind="ball", name="GND",
                                  grid=Grid(row=row, col=col), role="gnd",
                                  interface=iface))
                gnd_ball_ids.append(ball_id)
                gnd_count_per_iface[iface] += 1
                col += 1
                continue
            # Try to place a diff pair on (col, col+1) if both are signal-eligible.
            nxt = col + 1
            can_pair = (
                nxt <= p.cols
                and nxt % p.gnd_period != 0
                and not _in_corner(ri, nxt - 1, rmax, cmax_i, p.depop_corner)
            )
            if can_pair:
                for suffix, cc in (("_P", col), ("_N", nxt)):
                    net_name = f"{row}{col}{suffix}"
                    bid = f"{row}{cc}"
                    net_id = f"net_{net_name}"
                    dp_id = f"dp_{net_name}"
                    nodes.append(Node(id=net_id, kind="substrate_net", name=net_name,
                                      role="signal", interface=iface))
                    nodes.append(Node(id=dp_id, kind="die_pad", name=net_name))
                    nodes.append(Node(id=bid, kind="ball", name=net_name,
                                      grid=Grid(row=row, col=cc), role="signal",
                                      interface=iface))
                    edges.append(Edge(source=dp_id, target=net_id))
                    edges.append(Edge(source=net_id, target=bid))
                col += 2
            else:
                net_name = f"{row}{col}_S"
                net_id = f"net_{net_name}"
                dp_id = f"dp_{net_name}"
                nodes.append(Node(id=net_id, kind="substrate_net", name=net_name,
                                  role="signal", interface=iface))
                nodes.append(Node(id=dp_id, kind="die_pad", name=net_name))
                nodes.append(Node(id=ball_id, kind="ball", name=net_name,
                                  grid=Grid(row=row, col=col), role="signal",
                                  interface=iface))
                edges.append(Edge(source=dp_id, target=net_id))
                edges.append(Edge(source=net_id, target=ball_id))
                col += 1

    # One shared ground net for every ground ball.
    if gnd_ball_ids:
        nodes.append(Node(id="net_GND", kind="substrate_net", name="GND", role="gnd"))
        for bid in gnd_ball_ids:
            edges.append(Edge(source="net_GND", target=bid))

    graph = ConnectivityGraph(
        design=f"synth_{p.rows}x{p.cols}", rev="A",
        source_files=["<generated>"], nodes=nodes, edges=edges,
    )
    # Ground requirement: min over interfaces of the count we actually placed, so the
    # clean design passes; benchmarks lower ground counts to trip it.
    min_gnd = min(gnd_count_per_iface.values()) if gnd_count_per_iface else 0
    config = RunConfig(
        grounds={i: {"min_gnd": min_gnd} for i in interfaces},  # type: ignore[dict-item]
        adjacency_required=False,  # partners exist by construction; positions ok
        alphabet=p.alphabet,
        depop={"kind": "corner", "n": p.depop_corner},  # type: ignore[dict-item]
    )
    return GeneratedDesign(graph=graph, config=config, interfaces=interfaces)
