"""The deterministic paranoia battery (docs/llm-spec.md). No LLM here — pure checks.

Runs on every proposed Rule-IR extraction. Auto-accept requires confidence ≥ THRESHOLD
AND double-extraction agreement AND a full battery pass; a noted cell without a bound
condition is an automatic reject regardless of confidence.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from pkgtk.schemas.expr import ExprError, validate_expr

THRESHOLD = 0.90

# param -> (low, high, canonical_units); a value outside its range is a parse error.
PLAUSIBLE = {
    "trace_width_min": (1.0, 1000.0, "um"),
    "spacing_min": (1.0, 1000.0, "um"),
    "degas_to_trace_clearance_min": (1.0, 1000.0, "um"),
    "annular_ring_min": (1.0, 1000.0, "um"),
    "copper_to_edge_min": (10.0, 5000.0, "um"),
    "copper_balance_window": (0.1, 50.0, "mm"),
    "degas_coverage_window": (0.1, 50.0, "mm"),
}
_TO = {("um", "um"): 1.0, ("mm", "um"): 1000.0, ("nm", "um"): 0.001,
       ("mm", "mm"): 1.0, ("um", "mm"): 0.001}
_DASHES = {"", "-", "--", "---", "—", "–", "n/a", "na"}


@dataclass
class Candidate:
    rule: dict | None          # proposed RuleIR-shaped dict (None = not_offered marker)
    confidence: float = 1.0
    source_cell: str = ""
    note_refs: list[str] = field(default_factory=list)
    table_units: str | None = None
    table_minmax: str | None = None   # "min" | "max" | None
    raw_cell_text: str | None = None  # None = not a tier cell under evaluation
    not_offered: bool = False


@dataclass
class BatteryResult:
    flags: list[str] = field(default_factory=list)

    @property
    def rejected(self) -> bool:
        return any(f.startswith("REJECT:") for f in self.flags)

    @property
    def needs_review(self) -> bool:
        return any(f.startswith("REVIEW:") for f in self.flags)


def _convert(value: float, from_u: str, to_u: str) -> float | None:
    return value * _TO[(from_u, to_u)] if (from_u, to_u) in _TO else None


def check_physics_sanity(cand: Candidate) -> list[str]:
    flags: list[str] = []
    rule = cand.rule
    if rule is None:
        return flags
    param = rule.get("parameter")
    value = rule.get("value", {})
    kind = value.get("kind")

    if kind == "expression":
        try:
            validate_expr(value.get("expr", ""),
                          allowed_vars=(value.get("variable") or "A",))
        except ExprError as exc:
            flags.append(f"REJECT:expr_unparseable:{exc}")
    if kind == "piecewise":
        vals = [p.get("value") for p in value.get("pieces", [])]
        if vals and vals != sorted(vals) and vals != sorted(vals, reverse=True):
            flags.append("REVIEW:piecewise_non_monotonic")
        for p in value.get("pieces", []):
            try:
                validate_expr(p.get("when", ""),
                              allowed_vars=(value.get("variable") or "A",))
            except ExprError as exc:
                flags.append(f"REJECT:predicate_unparseable:{exc}")

    if kind == "scalar" and param in PLAUSIBLE:
        lo, hi, canon = PLAUSIBLE[param]
        conv = _convert(value.get("number", 0.0), value.get("units", canon), canon)
        if conv is None:
            flags.append(f"REVIEW:unknown_units:{value.get('units')}")
        elif not (lo <= conv <= hi):
            flags.append(f"REJECT:implausible_value:{conv}{canon}_for_{param}")

    # Inequality direction: *_min params are minimums; a Max header contradicts.
    if param and param.endswith("_min") and cand.table_minmax == "max":
        flags.append("REVIEW:inequality_direction_conflict")
    return flags


def check_header_inheritance(cand: Candidate) -> list[str]:
    rule = cand.rule
    if rule is None or cand.table_units is None:
        return []
    units = rule.get("value", {}).get("units")
    if units is not None and units != cand.table_units:
        return [f"REVIEW:header_units_not_inherited:{units}!={cand.table_units}"]
    return []


def check_footnote_binding(cand: Candidate) -> list[str]:
    if not cand.note_refs or cand.rule is None:
        return []
    rule = cand.rule
    has_condition = bool(rule.get("conditions"))
    is_manual = rule.get("executability") == "manual"
    if not (has_condition or is_manual):
        return [f"REJECT:noted_cell_unbound:{cand.note_refs}"]
    return []


def check_dash_semantics(cand: Candidate) -> list[str]:
    if cand.raw_cell_text is None:
        return []
    if cand.raw_cell_text.strip().lower() not in _DASHES:
        return []
    # A dash/blank cell must be marked not_offered, never a numeric value.
    if cand.not_offered or cand.rule is None:
        return []
    return ["REJECT:dash_as_value"]


def double_extraction(a: Candidate, b: Candidate) -> list[str]:
    if a.rule != b.rule:
        return ["REVIEW:double_extraction_disagreement"]
    return []


def run_battery(cand: Candidate, second: Candidate | None = None) -> BatteryResult:
    flags: list[str] = []
    flags += check_physics_sanity(cand)
    flags += check_header_inheritance(cand)
    flags += check_footnote_binding(cand)
    flags += check_dash_semantics(cand)
    if second is not None:
        flags += double_extraction(cand, second)
    return BatteryResult(flags=flags)


def decide(cand: Candidate, second: Candidate | None = None,
           threshold: float = THRESHOLD) -> dict:
    result = run_battery(cand, second)
    if result.rejected:
        decision = "reject"
    elif result.needs_review:
        decision = "review"
    elif cand.confidence < threshold:
        decision = "review"
    else:
        decision = "accept"
    return {"decision": decision, "flags": result.flags,
            "confidence": cand.confidence}
