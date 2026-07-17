"""Interface-template compliance checker. See Phase 5.

A template = grid of expected roles (sig/gnd/pwr/nc). Align the proposed ball map (from
the Connectivity Graph) to the template's declared anchor, compare roles, emit a
Violation per mismatch. Unknown proposal positions are flagged, not errors.

v0 alignment: template positions are absolute grid ids matching graph grid ids (the
declared anchor maps identity). Anchor-offset alignment is a v0 simplification
(see docs/PHASE-NOTES.md).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

from pkgtk.schemas.graph import ConnectivityGraph
from pkgtk.schemas.violation import LogicalLocation, Violation

CHECK_VERSION = "0.1.0"
_ROLE_ALIAS = {"sig": "signal", "signal": "signal", "gnd": "gnd", "pwr": "pwr",
               "nc": "nc"}


@dataclass
class TemplateResult:
    violations: list[Violation]
    flagged_unknown: list[str] = field(default_factory=list)


def load_template(path: str | Path) -> dict:
    return yaml.safe_load(Path(path).read_text("utf-8"))


def _ball_roles(graph: ConnectivityGraph) -> dict[str, str]:
    out = {}
    for n in graph.nodes:
        if n.kind == "ball" and n.grid:
            out[f"{n.grid.row}{n.grid.col}"] = n.role or "nc"
    return out


def check_template(graph: ConnectivityGraph, template: dict) -> TemplateResult:
    expected_roles = {k: _ROLE_ALIAS.get(v, v) for k, v in template["roles"].items()}
    actual = _ball_roles(graph)
    violations = []
    for pos, exp_role in sorted(expected_roles.items()):
        act_role = actual.get(pos)
        if act_role is None:
            # Missing populated position where the template expects a role.
            violations.append(_v(pos, "missing", exp_role))
        elif act_role != exp_role:
            violations.append(_v(pos, act_role, exp_role))
    flagged = sorted(set(actual) - set(expected_roles))
    return TemplateResult(violations=violations, flagged_unknown=flagged)


def _v(pos: str, measured: str, required: str) -> Violation:
    return Violation(
        rule_id="template.role_mismatch", severity="hard",
        location=LogicalLocation(kind="logical", net=pos),
        measured=measured, required=required, check_version=CHECK_VERSION,
    )
