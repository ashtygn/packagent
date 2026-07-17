"""Escape oracle: reproduce the hand-counted golden capacity exactly; verdicts."""

import json

from pkgtk.lint.deck import load_deck
from pkgtk.oracles.escape import evaluate_from_deck, line_space_from_deck
from pkgtk.schemas import schemas_dir

ESC = schemas_dir().parent / "fixtures" / "golden" / "escape"
GOLDEN = json.loads((ESC / "expected.json").read_text("utf-8"))
DECK = ESC / "escape_deck.yaml"


def test_line_space_pulled_from_deck():
    ls = line_space_from_deck(load_deck(DECK), "signal")
    assert ls.line_um == 20.0 and ls.space_um == 20.0


def _eval(demand):
    g = GOLDEN["geometry"]
    return evaluate_from_deck(DECK, g["pitch_um"], g["land_dia_um"], g["channels"],
                              g["routing_layers"], demand)


def test_capacity_reproduces_golden():
    r = _eval(GOLDEN["cases"]["feasible"]["demand"])
    assert r.n_tracks == GOLDEN["n_tracks"]
    assert r.capacity == GOLDEN["capacity"]


def test_feasible_case():
    exp = GOLDEN["cases"]["feasible"]
    r = _eval(exp["demand"])
    assert r.utilization == exp["utilization"]
    assert r.feasible is exp["feasible"]


def test_infeasible_case_flagged():
    exp = GOLDEN["cases"]["infeasible"]
    r = _eval(exp["demand"])
    assert r.utilization == exp["utilization"]
    assert r.feasible is exp["feasible"]
