"""Model librarian lifecycle test incl. a rejected intake holding at 'received'."""

import pytest

from pkgtk.models.registry import ModelKey, Registry, TransitionError
from pkgtk.schemas import schemas_dir

TS_DIR = schemas_dir().parent / "fixtures" / "golden" / "models" / "touchstone"


def _reg():
    return Registry(":memory:")


def test_full_lifecycle():
    reg = _reg()
    key = ModelKey("PARTX", "A0", "typ", "sparam")
    reg.add(key)
    assert reg.state(key) == "requested"
    reg.transition(key, "received")
    reg.transition(key, "validated", note="ok")
    reg.transition(key, "filed")
    assert reg.state(key) == "filed"
    reg.transition(key, "stale")
    assert reg.state(key) == "stale"


def test_illegal_transition_raises():
    reg = _reg()
    key = ModelKey("P", "A", "typ", "sparam")
    reg.add(key)
    with pytest.raises(TransitionError):
        reg.transition(key, "filed")  # requested -> filed is illegal


def test_intake_pass_advances_to_validated():
    reg = _reg()
    key = ModelKey("P", "A", "typ", "sparam")
    reg.add(key)
    verdict = reg.intake(key, TS_DIR / "good.s2p")
    assert verdict["decision"] == "pass"
    assert reg.state(key) == "validated"


def test_rejected_intake_holds_at_received():
    reg = _reg()
    key = ModelKey("P", "A", "typ", "sparam")
    reg.add(key)
    verdict = reg.intake(key, TS_DIR / "nonpassive.s2p")
    assert verdict["decision"] == "reject"
    assert reg.state(key) == "received"
    row = [r for r in reg.all_rows() if r["part"] == "P"][0]
    assert "reject" in row["note"]


def test_intake_ibis_captured():
    reg = _reg()
    key = ModelKey("PIB", "A", "typ", "ibis")
    reg.add(key)
    captured = "ERROR (line 1): truncated\n    1 errors, 0 warnings, 0 notes\n"
    verdict = reg.intake(key, "truncated.ibs", captured_ibis=captured)
    assert verdict["decision"] == "reject"
    assert reg.state(key) == "received"


def test_chase_email_renders():
    reg = _reg()
    key = ModelKey("PARTX", "A0", "typ", "sparam")
    reg.add(key)
    email = reg.chase_email(key)
    assert "PARTX" in email and "A0" in email and "Subject:" in email
