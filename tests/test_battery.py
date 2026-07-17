"""Paranoia-battery tests: the five checks + auto-accept policy, incl. the traps."""

from pkgtk.llm.battery import Candidate, decide, run_battery


def _rule(param="trace_width_min", number=25.0, units="um", **extra):
    r = {"id": "R", "source": {"doc": "d"}, "parameter": param,
         "value": {"kind": "scalar", "number": number, "units": units},
         "severity": "hard", "executability": "dimensional", "routing": "external"}
    r.update(extra)
    return r


def test_clean_high_confidence_auto_accepts():
    cand = Candidate(rule=_rule(), confidence=0.97)
    assert decide(cand, cand)["decision"] == "accept"


def test_low_confidence_routes_to_review():
    cand = Candidate(rule=_rule(), confidence=0.5)
    assert decide(cand, cand)["decision"] == "review"


def test_double_extraction_disagreement_reviews():
    a = Candidate(rule=_rule(number=25), confidence=0.99)
    b = Candidate(rule=_rule(number=20), confidence=0.99)
    assert decide(a, b)["decision"] == "review"


def test_physics_sanity_rejects_implausible_value():
    # 15 mm trace width -> parse error, not a rule.
    cand = Candidate(rule=_rule(number=15.0, units="mm"), confidence=0.99)
    assert decide(cand, cand)["decision"] == "reject"


def test_footnote_trap_bare_value_rejected():
    # A noted cell must yield a condition or executability=manual; bare value -> reject.
    cand = Candidate(rule=_rule(), confidence=0.99, note_refs=["Note 1"])
    assert decide(cand, cand)["decision"] == "reject"


def test_footnote_trap_bound_condition_ok():
    cand = Candidate(
        rule=_rule(conditions=[{"text": "not with conductive adhesive"}],
                   executability="manual"),
        confidence=0.99, note_refs=["Note 1"])
    res = run_battery(cand)
    assert not res.rejected


def test_units_header_trap_not_inherited_reviews():
    # Table declares mm; row extracted as um without inheriting -> review.
    cand = Candidate(rule=_rule(units="um"), confidence=0.99, table_units="mm")
    assert decide(cand, cand)["decision"] == "review"


def test_dash_semantics_reject_when_misread_as_value():
    cand = Candidate(rule=_rule(number=0.0), confidence=0.99, raw_cell_text="---")
    assert decide(cand, cand)["decision"] == "reject"


def test_dash_semantics_ok_when_marked_not_offered():
    cand = Candidate(rule=None, confidence=0.99, raw_cell_text="---", not_offered=True)
    res = run_battery(cand)
    assert not res.rejected and not res.needs_review


def test_piecewise_non_monotonic_reviews():
    rule = _rule()
    rule["value"] = {"kind": "piecewise", "variable": "A", "units": "um",
                     "pieces": [{"when": "A <= 5", "value": 20.0},
                                {"when": "5 < A <= 10", "value": 10.0},
                                {"when": "A > 10", "value": 30.0}]}
    cand = Candidate(rule=rule, confidence=0.99)
    assert decide(cand, cand)["decision"] == "review"


def test_bad_expression_rejected():
    rule = _rule()
    rule["value"] = {"kind": "expression", "expr": "__import__('os')"}
    cand = Candidate(rule=rule, confidence=0.99)
    assert decide(cand, cand)["decision"] == "reject"


def test_inequality_direction_conflict_reviews():
    cand = Candidate(rule=_rule(), confidence=0.99, table_minmax="max")
    assert decide(cand, cand)["decision"] == "review"
