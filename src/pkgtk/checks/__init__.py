"""Ball-map check engine: registry + deterministic run_all.

See docs/checks-spec.md. ``run_all`` executes every registered check and returns a
byte-stable (sorted) list of Violations.
"""

from __future__ import annotations

from pkgtk.checks.common import Adjacency, RunConfig
from pkgtk.checks.rules import REGISTRY
from pkgtk.schemas.graph import ConnectivityGraph
from pkgtk.schemas.violation import Violation


def _sort_key(v: Violation) -> tuple[str, str, str]:
    node_id = getattr(v.location, "node_id", None) or ""
    net = getattr(v.location, "net", None) or ""
    return (v.rule_id, node_id, net)


def run_all(
    graph: ConnectivityGraph, config: RunConfig | None = None
) -> list[Violation]:
    config = config or RunConfig()
    adj = Adjacency(graph)
    out: list[Violation] = []
    for check in REGISTRY:
        out.extend(check(graph, config, adj))
    return sorted(out, key=_sort_key)


__all__ = ["run_all", "RunConfig", "Adjacency", "REGISTRY"]
