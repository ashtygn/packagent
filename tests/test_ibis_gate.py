"""IBIS gate tests via captured stdout (recorded mode; no executable needed).

A live-run test is included but skipped unless PKGTK_IBISCHK points at an executable.
"""

import json
import os

import pytest

from pkgtk.models.ibis_gate import parse_ibischk_output, run_ibischk
from pkgtk.schemas import schemas_dir

REPO = schemas_dir().parent
CAPTURED = REPO / "fixtures" / "synthetic" / "ibischk_stdout"
EXPECTED = json.loads(
    (REPO / "fixtures" / "golden" / "models" / "ibis" / "expected_verdicts.json")
    .read_text("utf-8")
)


@pytest.mark.parametrize("name", sorted(EXPECTED))
def test_captured_output_reproduces_expected_verdict(name):
    text = (CAPTURED / name).read_text("utf-8")
    v = parse_ibischk_output(text)
    exp = EXPECTED[name]
    assert v["errors"] == exp["errors"]
    assert v["warnings"] == exp["warnings"]
    assert v["notes"] == exp["notes"]
    assert v["decision"] == exp["decision"]


def test_raw_lines_preserved():
    text = (CAPTURED / "truncated.txt").read_text("utf-8")
    v = parse_ibischk_output(text)
    assert any("Unexpected end-of-file" in line for line in v["raw_lines"])


def test_count_fallback_without_summary_line():
    v = parse_ibischk_output("ERROR (line 1): x\nWARNING (line 2): y\n")
    assert v["errors"] == 1 and v["warnings"] == 1 and v["decision"] == "reject"


@pytest.mark.skipif(not os.environ.get("PKGTK_IBISCHK"),
                    reason="ibischk executable not configured")
def test_live_run_smoke(tmp_path):
    model = tmp_path / "empty.ibs"
    model.write_text("[IBIS Ver] 5.0\n[End]\n", "utf-8")
    v = run_ibischk(model)
    assert v["decision"] in ("pass", "pass-with-flags", "reject")
