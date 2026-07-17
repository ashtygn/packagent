"""Touchstone gate tests: good passes, non-passive rejected citing worst freq, port
mismatch caught pre-parse. Metrics are hand-verified (see fixture headers)."""

import math

from pkgtk.models.ts_gate import gate
from pkgtk.schemas import schemas_dir

TS_DIR = schemas_dir().parent / "fixtures" / "golden" / "models" / "touchstone"


def test_good_passes_with_expected_sigma():
    r = gate(TS_DIR / "good.s2p")
    assert r["decision"] == "pass"
    assert r["passivity"]["band"] == "good"
    assert math.isclose(r["passivity"]["sigma_max"], 0.6, abs_tol=1e-6)
    assert r["reciprocity"]["max_asymmetry"] == 0.0
    assert r["violations"] == []


def test_nonpassive_rejected_with_worst_freq():
    r = gate(TS_DIR / "nonpassive.s2p")
    assert r["decision"] == "reject"
    assert r["passivity"]["band"] == "poor"
    assert math.isclose(r["passivity"]["sigma_max"], 1.2, abs_tol=1e-6)
    assert r["passivity"]["worst_freq_hz"] == 1.0e9
    rules = {v["rule_id"] for v in r["violations"]}
    assert "touchstone.passivity" in rules


def test_port_mismatch_caught_pre_parse():
    r = gate(TS_DIR / "port_mismatch.s2p")
    assert r["decision"] == "reject"
    assert r["sanity"]["port_count_ok"] is False
    rules = {v["rule_id"] for v in r["violations"]}
    assert "touchstone.port_count" in rules


def test_verdict_is_json_serializable():
    import json

    for f in ("good.s2p", "nonpassive.s2p", "port_mismatch.s2p"):
        json.dumps(gate(TS_DIR / f))
