"""CLI + lyrdb round-trip test: run a deck on a golden GDS, re-parse the lyrdb."""

import json

import pytest

pytest.importorskip("klayout")

from pkgtk.cli.check import run_lint  # noqa: E402
from pkgtk.lint.lyrdb import read_lyrdb_counts, write_lyrdb  # noqa: E402
from pkgtk.schemas import schemas_dir  # noqa: E402

LINT_DIR = schemas_dir().parent / "fixtures" / "golden" / "lint"


def test_cli_runs_deck_and_writes_lyrdb(tmp_path):
    gds = LINT_DIR / "width_min" / "in.gds"
    deck = LINT_DIR / "test_deck.yaml"
    layers = LINT_DIR / "width_min" / "layers.yaml"
    violations, coverage, skipped = run_lint(gds, deck, layers)
    assert len(violations) == 1
    assert violations[0].rule_id == "W.SIGNAL"

    out = tmp_path / "out.lyrdb"
    counts = write_lyrdb(violations, out)
    assert counts == {"W.SIGNAL": 1}
    # Re-parse the written database and confirm categories/counts survive.
    assert read_lyrdb_counts(out) == {"W.SIGNAL": 1}


def test_clean_gds_no_violations(tmp_path):
    gds = LINT_DIR / "clean" / "in.gds"
    deck = LINT_DIR / "test_deck.yaml"
    layers = LINT_DIR / "clean" / "layers.yaml"
    violations, _, _ = run_lint(gds, deck, layers)
    assert violations == []
    out = tmp_path / "out.lyrdb"
    write_lyrdb(violations, out)
    assert read_lyrdb_counts(out) == {}


def test_lyrdb_multi_category(tmp_path):
    from pkgtk.schemas.violation import PhysicalLocation, Violation

    vs = [
        Violation(rule_id="A", severity="hard",
                  location=PhysicalLocation(kind="physical", x=1.0, y=1.0),
                  check_version="0.1.0"),
        Violation(rule_id="A", severity="hard",
                  location=PhysicalLocation(kind="physical", x=2.0, y=2.0),
                  check_version="0.1.0"),
        Violation(rule_id="B", severity="preferred",
                  location=PhysicalLocation(kind="physical", x=3.0, y=3.0),
                  check_version="0.1.0"),
    ]
    out = tmp_path / "m.lyrdb"
    counts = write_lyrdb(vs, out)
    assert counts == {"A": 2, "B": 1}
    assert read_lyrdb_counts(out) == {"A": 2, "B": 1}


def test_violations_json_shape(tmp_path):
    gds = LINT_DIR / "width_min" / "in.gds"
    deck = LINT_DIR / "test_deck.yaml"
    layers = LINT_DIR / "width_min" / "layers.yaml"
    violations, _, _ = run_lint(gds, deck, layers)
    dumped = [v.model_dump(mode="json", exclude_none=True) for v in violations]
    text = json.dumps(dumped)
    assert "W.SIGNAL" in text and "physical" in text
