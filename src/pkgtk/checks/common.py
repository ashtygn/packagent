"""Shared helpers for the ball-map checks: run config, adjacency, grid alphabets.

See docs/checks-spec.md (normative). All checks are pure functions
``(graph, config, adj) -> list[Violation]`` with no I/O.
"""

from __future__ import annotations

from collections import defaultdict

from pydantic import BaseModel, ConfigDict, Field

from pkgtk.schemas.graph import ConnectivityGraph, Node

CHECK_VERSION = "0.1.0"

# JEDEC row-letter alphabet skips I, O, Q, S, X, Z (see checks-spec §grid conventions).
_FULL_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
_JEDEC_ALPHABET = "ABCDEFGHJKLMNPRTUVWY"  # I,O,Q,S,X,Z removed


class DepopSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kind: str = "corner"  # corner | ring | list
    n: int = 0
    width: int = 0
    positions: list[list[int]] = Field(default_factory=list)


class GroundReq(BaseModel):
    model_config = ConfigDict(extra="forbid")
    min_gnd: int | None = None
    gnd_ratio: float | None = None


class MatchGroupReq(BaseModel):
    model_config = ConfigDict(extra="forbid")
    count: int | None = None


class RunConfig(BaseModel):
    """Optional run configuration consumed by the check engine."""

    model_config = ConfigDict(extra="forbid")

    multi_ball_allow: list[str] = Field(default_factory=list)
    grounds: dict[str, GroundReq] = Field(default_factory=dict)
    pair_patterns: list[list[str]] = Field(
        default_factory=lambda: [["(.*)_P$", "\\1_N"]]
    )
    adjacency_required: bool = False
    alphabet: str = "full"  # "full" | "jedec"
    match_groups: dict[str, MatchGroupReq] = Field(default_factory=dict)
    bridge_nets: list[str] = Field(default_factory=list)
    depop: DepopSpec = Field(default_factory=DepopSpec)


def alphabet_for(name: str) -> str:
    return _JEDEC_ALPHABET if name == "jedec" else _FULL_ALPHABET


def row_index(row: str, alphabet: str) -> int:
    """Map a (possibly multi-letter) row designator to a 0-based index.

    Bijective-base-N over the given alphabet: A->0, ..., last->N-1, then AA->N, ...
    """
    base = len(alphabet)
    idx = 0
    for ch in row:
        pos = alphabet.find(ch)
        if pos < 0:
            raise ValueError(f"row letter {ch!r} not in alphabet {alphabet!r}")
        idx = idx * base + (pos + 1)
    return idx - 1


class Adjacency:
    """Precomputed neighbor maps and tier lookups for a graph."""

    def __init__(self, graph: ConnectivityGraph):
        self.graph = graph
        self.by_id: dict[str, Node] = {n.id: n for n in graph.nodes}
        self.neigh: dict[str, set[str]] = defaultdict(set)
        for e in graph.edges:
            self.neigh[e.source].add(e.target)
            self.neigh[e.target].add(e.source)

    def neighbors(self, node_id: str) -> list[Node]:
        ids = self.neigh.get(node_id, set())
        return [self.by_id[i] for i in ids if i in self.by_id]

    def nodes_of_kind(self, kind: str) -> list[Node]:
        return [n for n in self.graph.nodes if n.kind == kind]

    def nets_of_ball(self, ball_id: str) -> list[Node]:
        return [n for n in self.neighbors(ball_id) if n.kind == "substrate_net"]

    def balls_of_net(self, net_id: str) -> list[Node]:
        return [n for n in self.neighbors(net_id) if n.kind == "ball"]

    def reachable(self, start_id: str) -> set[str]:
        seen = {start_id}
        stack = [start_id]
        while stack:
            cur = stack.pop()
            for nxt in self.neigh.get(cur, set()):
                if nxt not in seen:
                    seen.add(nxt)
                    stack.append(nxt)
        return seen
