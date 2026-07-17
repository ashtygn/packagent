"""CI guard for the Phase-1 benchmark: clean design clean, 20/20 caught, exacts hold."""

from benchmarks.run import run


def test_benchmark_catch_rate_and_false_positive_gate():
    summary = run()
    assert summary["clean_violations"] == 0, "false-positive gate: clean design dirty"
    assert summary["caught"] == summary["total"], (
        f"only {summary['caught']}/{summary['total']} seeded defects caught"
    )
    assert summary["total"] == 20
    assert summary["exact_failures"] == []
