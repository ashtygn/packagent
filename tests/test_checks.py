"""Golden-graph check tests.

Every fixture under fixtures/golden/graphs/<name>/ carries a hand-authored graph,
an optional run config, and the hand-computed expected violations. The engine must
reproduce each expected list exactly (and the clean graph must fire zero) — the
false-positive gate.
"""

import json

import pytest

from pkgtk.cli.verify import verify_graph
from pkgtk.schemas import schemas_dir

GRAPHS_DIR = schemas_dir().parent / "fixtures" / "golden" / "graphs"
FIXTURES = sorted(p.name for p in GRAPHS_DIR.iterdir() if p.is_dir())


def test_fixtures_present():
    assert FIXTURES, "no golden graph fixtures found"
    assert "clean" in FIXTURES


@pytest.mark.parametrize("name", FIXTURES)
def test_fixture_reproduces_expected(name):
    d = GRAPHS_DIR / name
    config = d / "config.json"
    report = verify_graph(d / "graph.json", config if config.is_file() else None)
    expected = json.loads((d / "expected.json").read_text("utf-8"))
    assert report["violations"] == expected, (
        f"{name}: mismatch\n"
        f"expected: {json.dumps(expected, sort_keys=True)}\n"
        f"actual  : {json.dumps(report['violations'], sort_keys=True)}"
    )


def test_clean_graph_zero_violations():
    report = verify_graph(GRAPHS_DIR / "clean" / "graph.json",
                          GRAPHS_DIR / "clean" / "config.json")
    assert report["violation_count"] == 0


def test_each_defect_fires_exactly_one():
    # Every non-clean fixture is engineered to plant exactly one defect.
    for name in FIXTURES:
        if name == "clean":
            continue
        d = GRAPHS_DIR / name
        config = d / "config.json"
        report = verify_graph(d / "graph.json", config if config.is_file() else None)
        assert report["violation_count"] == 1, f"{name}: expected exactly 1 violation"
