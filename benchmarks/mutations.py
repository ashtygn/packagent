"""Seeded defect injectors for the Phase-1 benchmark.

Each mutation takes the clean GeneratedDesign and returns
``(graph, config, expected)`` where ``expected`` is the partial violation the seeded
defect should produce: ``{"rule_id", "node_id"?, "net"?}``. The check engine must
independently surface a violation matching every non-null field of ``expected`` — the
mutation only declares where it planted the defect, it does not run the checks.

Determinism: targets are chosen by scanning the (deterministic) generated graph in a
fixed order, so every case is reproducible.
"""

from __future__ import annotations

from pkgtk.checks.common import MatchGroupReq, RunConfig
from pkgtk.schemas.graph import ConnectivityGraph, Edge, Grid, Node
from pkgtk.synth.ballmap_gen import GeneratedDesign


def _clone(design: GeneratedDesign) -> tuple[ConnectivityGraph, RunConfig]:
    return design.graph.model_copy(deep=True), design.config.model_copy(deep=True)


def _first(nodes, pred):
    return _nth(nodes, pred, 0)


def _nth(nodes, pred, k):
    hits = [n for n in sorted(nodes, key=lambda x: x.id) if pred(n)]
    if k >= len(hits):
        raise AssertionError(f"fewer than {k + 1} matching nodes for mutation target")
    return hits[k]


def _signal_ball(g, k=0):
    return _nth(g.nodes, lambda n: n.kind == "ball" and n.role == "signal", k)


def _signal_net(g, k=0):
    return _nth(g.nodes, lambda n: n.kind == "substrate_net" and n.role == "signal", k)


def _nc_ball(g):
    return _first(g.nodes, lambda n: n.kind == "ball" and n.role == "nc")


def _die_pad(g):
    return _first(g.nodes, lambda n: n.kind == "die_pad")


def _pair_p_net(g):
    return _first(g.nodes, lambda n: n.kind == "substrate_net"
                  and (n.name or "").endswith("_P"))


def _no_depop(cfg: RunConfig) -> RunConfig:
    cfg.depop.n = 0
    cfg.depop.kind = "corner"
    return cfg


# --- exact single-violation mutations (golden-verified) -----------------------

def mut_multi_assignment(design, k=0):
    g, cfg = _clone(design)
    ball = _signal_ball(g, k)
    g.edges.append(Edge(source="net_GND", target=ball.id))
    return g, cfg, {"rule_id": "bijection.multi_assignment", "node_id": ball.id}


def mut_duplicate_die_pad(design):
    g, cfg = _clone(design)
    pad = _die_pad(g)
    net = _first(g.nodes, lambda n: n.kind == "substrate_net" and n.name == pad.name)
    g.nodes.append(Node(id=pad.id + "_dup", kind="die_pad", name=pad.name))
    g.edges.append(Edge(source=pad.id + "_dup", target=net.id))
    return g, cfg, {"rule_id": "duplicate.die_pad", "net": pad.name}


def mut_duplicate_ball_grid(design, k=0):
    g, cfg = _clone(design)
    ball = _signal_ball(g, k)
    key = f"{ball.grid.row}{ball.grid.col}"
    g.nodes.append(Node(id=ball.id + "_dup", kind="ball", name="NCDUP",
                        grid=Grid(row=ball.grid.row, col=ball.grid.col), role="nc"))
    return g, cfg, {"rule_id": "duplicate.ball_grid", "net": key}


def mut_nc_collision(design):
    g, cfg = _clone(design)
    ball = _nc_ball(g)
    g.edges.append(Edge(source="net_GND", target=ball.id))
    return g, cfg, {"rule_id": "nc.collision", "node_id": ball.id}


def mut_depop_not_nc(design, k=0):
    g, cfg = _clone(design)
    ball = _nth(g.nodes, lambda n: n.kind == "ball" and n.role == "nc", k)
    ball.role = "signal"
    net_id = f"net_depopfix_{k}"
    g.nodes.append(Node(id=net_id, kind="substrate_net", name=f"DEPOPFIX{k}",
                        role="signal"))
    g.nodes.append(Node(id=f"dp_depopfix_{k}", kind="die_pad", name=f"DEPOPFIX{k}"))
    g.edges.append(Edge(source=f"dp_depopfix_{k}", target=net_id))
    g.edges.append(Edge(source=net_id, target=ball.id))
    key = f"{ball.grid.row}{ball.grid.col}"
    return g, cfg, {"rule_id": "depop.not_nc", "net": key}


# --- catch+location mutations -------------------------------------------------

def mut_multi_ball_signal(design, k=0):
    g, cfg = _clone(design)
    cfg = _no_depop(cfg)
    net = _signal_net(g, k)
    g.nodes.append(Node(id=f"extra_ball_{k}", kind="ball", name=net.name,
                        grid=Grid(row="ZZ", col=1 + k), role="signal"))
    g.edges.append(Edge(source=net.id, target=f"extra_ball_{k}"))
    return g, cfg, {"rule_id": "bijection.multi_ball_signal", "net": net.name}


def mut_grounds_missing(design):
    g, cfg = _clone(design)
    # Flip every ground ball in IF0 to signal role -> IF0 ground count drops below min.
    for n in g.nodes:
        if n.kind == "ball" and n.role == "gnd" and n.interface == "IF0":
            n.role = "signal"
    return g, cfg, {"rule_id": "grounds.missing", "net": "IF0"}


def mut_diffpair_missing_partner(design, k=0):
    g, cfg = _clone(design)
    pnet = _nth(g.nodes, lambda n: n.kind == "substrate_net"
                and (n.name or "").endswith("_P"), k)
    partner = pnet.name[:-2] + "_N"
    # Remove the _N net, its die pad, its ball, and their edges.
    nnet = _first(g.nodes, lambda n: n.kind == "substrate_net" and n.name == partner)
    ball_ids = {b.id for b in _balls_of(g, nnet.id)}
    dp_ids = {d.id for d in g.nodes if d.kind == "die_pad" and d.name == partner}
    drop = {nnet.id} | ball_ids | dp_ids
    g.nodes = [n for n in g.nodes if n.id not in drop]
    g.edges = [e for e in g.edges if e.source not in drop and e.target not in drop]
    return g, cfg, {"rule_id": "diffpair.missing_partner", "net": pnet.name}


def mut_diffpair_not_adjacent(design):
    g, cfg = _clone(design)
    cfg.adjacency_required = True
    cfg = _no_depop(cfg)
    pnet = _pair_p_net(g)
    partner = pnet.name[:-2] + "_N"
    nnet = _first(g.nodes, lambda n: n.kind == "substrate_net" and n.name == partner)
    nball = _balls_of(g, nnet.id)[0]
    nball.grid = Grid(row="ZZ", col=99)  # far away, unique position
    return g, cfg, {"rule_id": "diffpair.not_adjacent", "net": pnet.name}


def mut_matchgroup_domain_split(design):
    g, cfg = _clone(design)
    nets = [n for n in g.nodes if n.kind == "substrate_net" and n.role == "signal"]
    nets = sorted(nets, key=lambda x: x.id)[:2]
    nets[0].match_group = "MGX"
    nets[0].domain = "DOM_A"
    nets[1].match_group = "MGX"
    nets[1].domain = "DOM_B"
    return g, cfg, {"rule_id": "matchgroup.domain_split", "net": "MGX"}


def mut_matchgroup_interface_split(design):
    g, cfg = _clone(design)
    a = _first(g.nodes, lambda n: n.kind == "substrate_net" and n.interface == "IF0")
    b = _first(g.nodes, lambda n: n.kind == "substrate_net" and n.interface == "IF1")
    a.match_group = "MGY"
    b.match_group = "MGY"
    return g, cfg, {"rule_id": "matchgroup.interface_split", "net": "MGY"}


def mut_matchgroup_incomplete(design):
    g, cfg = _clone(design)
    net = _signal_net(g)
    net.match_group = "MGZ"
    cfg.match_groups = {"MGZ": MatchGroupReq(count=4)}
    return g, cfg, {"rule_id": "matchgroup.incomplete", "net": "MGZ"}


def mut_domain_crossing(design):
    g, cfg = _clone(design)
    gnd_balls = sorted([n for n in g.nodes if n.kind == "ball" and n.role == "gnd"],
                       key=lambda x: x.id)[:2]
    gnd_balls[0].domain = "DOM_A"
    gnd_balls[1].domain = "DOM_B"
    return g, cfg, {"rule_id": "domain.crossing", "net": "GND"}


def mut_floating_die_pad(design):
    g, cfg = _clone(design)
    g.nodes.append(Node(id="orphan_pad", kind="die_pad", name="ORPHAN"))
    return g, cfg, {"rule_id": "floating.die_pad", "node_id": "orphan_pad"}


def mut_floating_ball_no_net(design):
    g, cfg = _clone(design)
    cfg = _no_depop(cfg)
    g.nodes.append(Node(id="orphan_ball", kind="ball", name="ORPHAN",
                        grid=Grid(row="ZZ", col=2), role="signal"))
    return g, cfg, {"rule_id": "floating.ball_no_net", "node_id": "orphan_ball"}


def _balls_of(g, net_id):
    targets = {e.target for e in g.edges if e.source == net_id}
    targets |= {e.source for e in g.edges if e.target == net_id}
    return [n for n in g.nodes if n.id in targets and n.kind == "ball"]


REGISTRY = {
    "multi_assignment": mut_multi_assignment,
    "duplicate_die_pad": mut_duplicate_die_pad,
    "duplicate_ball_grid": mut_duplicate_ball_grid,
    "nc_collision": mut_nc_collision,
    "depop_not_nc": mut_depop_not_nc,
    "multi_ball_signal": mut_multi_ball_signal,
    "grounds_missing": mut_grounds_missing,
    "diffpair_missing_partner": mut_diffpair_missing_partner,
    "diffpair_not_adjacent": mut_diffpair_not_adjacent,
    "matchgroup_domain_split": mut_matchgroup_domain_split,
    "matchgroup_interface_split": mut_matchgroup_interface_split,
    "matchgroup_incomplete": mut_matchgroup_incomplete,
    "domain_crossing": mut_domain_crossing,
    "floating_die_pad": mut_floating_die_pad,
    "floating_ball_no_net": mut_floating_ball_no_net,
    # Variants at a different location, proving the checks generalize beyond
    # the first occurrence (catch+location coverage across the grid).
    "multi_assignment_v2": lambda d: mut_multi_assignment(d, k=3),
    "multi_ball_signal_v2": lambda d: mut_multi_ball_signal(d, k=3),
    "diffpair_missing_partner_v2": lambda d: mut_diffpair_missing_partner(d, k=4),
    "duplicate_ball_grid_v2": lambda d: mut_duplicate_ball_grid(d, k=5),
    "depop_not_nc_v2": lambda d: mut_depop_not_nc(d, k=2),
}
