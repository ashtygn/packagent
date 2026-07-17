"""Deck loader + coverage tests."""

import pytest

from pkgtk.lint.coverage import classify
from pkgtk.lint.deck import DeckError, load_deck
from pkgtk.schemas import schemas_dir

REPO = schemas_dir().parent
DECK = REPO / "decks" / "generic-substrate-v0.yaml"
LINT_DIR = REPO / "fixtures" / "golden" / "lint"


def test_generic_deck_loads():
    deck = load_deck(DECK)
    assert deck.meta["name"] == "generic-substrate-v0"
    assert len(deck.rules) >= 8
    ids = {r.id for r in deck.rules}
    assert "SUB.TRACE.WIDTH.MIN.SIGNAL" in ids


def test_deck_disclaimer_present():
    text = DECK.read_text(encoding="utf-8")
    assert "NOT MANUFACTURING VALID" in text


def test_broken_yaml_reports_line():
    with pytest.raises(DeckError) as ei:
        load_deck(LINT_DIR / "broken_deck_syntax.yaml")
    assert "line" in str(ei.value).lower()


def test_broken_schema_reports_rule_id():
    with pytest.raises(DeckError) as ei:
        load_deck(LINT_DIR / "broken_deck_schema.yaml")
    assert "BAD.SEVERITY" in str(ei.value)


def test_coverage_classifies_unknown_as_unimplemented():
    deck = load_deck(DECK)
    report = classify(deck)
    by_id = {r["id"]: r for r in report["rules"]}
    assert by_id["SUB.TRACE.WIDTH.MIN.SIGNAL"]["status"] == "implemented"
    assert by_id["SUB.WARP.MAX"]["status"] == "manual"
    # package_warpage_max is unknown, but SUB.WARP.MAX is executability=manual ->
    # classified manual. The adhesive note is also manual.
    assert report["counts"]["implemented"] >= 3
    assert report["counts"]["manual"] >= 2


def test_coverage_unimplemented_present():
    deck = load_deck(DECK)
    report = classify(deck)
    statuses = {r["parameter"]: r["status"] for r in report["rules"]}
    # ball_grid / copper_balance_window / degas_coverage_window are real but
    # not-yet-implemented geometry checks -> unimplemented, never silent pass.
    assert statuses["ball_grid"] == "unimplemented"
    assert statuses["copper_balance_window"] == "unimplemented"
