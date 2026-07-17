"""ECO diff golden test: expected_diff.json and expected_report.md reproduced."""

import json

from pkgtk.cli.diff import run_diff
from pkgtk.diff.report import render_markdown
from pkgtk.schemas import schemas_dir

DIFF_DIR = schemas_dir().parent / "fixtures" / "golden" / "diff"


def test_expected_diff_reproduced():
    actual = run_diff(DIFF_DIR / "revA.json", DIFF_DIR / "revB.json")
    expected = json.loads((DIFF_DIR / "expected_diff.json").read_text("utf-8"))
    assert actual == expected


def test_expected_report_reproduced():
    actual = render_markdown(run_diff(DIFF_DIR / "revA.json", DIFF_DIR / "revB.json"))
    expected = (DIFF_DIR / "expected_report.md").read_text(encoding="utf-8")
    assert actual == expected


def test_diff_is_deterministic():
    a = run_diff(DIFF_DIR / "revA.json", DIFF_DIR / "revB.json")
    b = run_diff(DIFF_DIR / "revA.json", DIFF_DIR / "revB.json")
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


def test_identity_diff_is_empty():
    # Diffing a graph against itself yields no changes.
    d = run_diff(DIFF_DIR / "revA.json", DIFF_DIR / "revA.json")
    assert d["changes"] == []
    assert d["summary"] == {}
