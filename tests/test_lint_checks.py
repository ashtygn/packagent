"""Golden geometry-check tests. Each fixture GDS fires exactly its planted violation.

Skipped cleanly where klayout is not installed (it is a `geometry` extra, not a core
dep), so `make ci` stays green everywhere while running fully where klayout is present.
"""

import json

import pytest
import yaml

pytest.importorskip("klayout")

from pkgtk.lint.engine import load_layout, run_check  # noqa: E402
from pkgtk.schemas import schemas_dir  # noqa: E402

LINT_DIR = schemas_dir().parent / "fixtures" / "golden" / "lint"
CASES = sorted(p.name for p in LINT_DIR.iterdir()
               if p.is_dir() and (p / "in.gds").is_file())


def _run(name):
    d = LINT_DIR / name
    layers = yaml.safe_load((d / "layers.yaml").read_text("utf-8"))
    layers = {k: tuple(v) for k, v in layers.items()}
    case = yaml.safe_load((d / "case.yaml").read_text("utf-8"))
    layout = load_layout(d / "in.gds")
    params = {"rule_id": f"TEST.{name}", "value_um": case["value_um"],
              "layer_class": case.get("layer_class", "signal")}
    vs = run_check(layout, layers, case["parameter"], params)
    return [v.model_dump(mode="json", exclude_none=True) for v in vs]


def test_fixtures_present():
    assert "width_min" in CASES and "clean" in CASES


@pytest.mark.parametrize("name", CASES)
def test_fixture_reproduces_expected(name):
    expected = json.loads((LINT_DIR / name / "expected.json").read_text("utf-8"))
    assert _run(name) == expected


def test_clean_fires_zero():
    assert _run("clean") == []


def test_each_defect_fires_exactly_one():
    for name in CASES:
        if name == "clean":
            continue
        assert len(_run(name)) == 1, f"{name} did not fire exactly one violation"
