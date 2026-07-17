"""Phase-2 substrate benchmark CI guard (skips cleanly without klayout)."""

import pytest

pytest.importorskip("klayout")

from benchmarks.lint_run import run  # noqa: E402


def test_clean_substrate_clean_and_dirty_caught():
    summary = run()
    assert summary["clean_violations"] == 0, "clean substrate should be violation-free"
    assert summary["missed"] == [], f"dirty defects missed: {summary['missed']}"
    assert set(summary["caught_defects"]) == set(summary["expected_defects"])
    assert len(summary["expected_defects"]) == 4
