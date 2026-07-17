"""CI staleness guard: committed BENCHMARKS.md must equal a fresh regeneration.

Editing a benchmark input without regenerating trips this. Skipped where klayout is
absent, since the committed file's Phase-2 section requires it.
"""

import pytest

pytest.importorskip("klayout")

from benchmarks.rollup import OUT, render  # noqa: E402


def test_benchmarks_md_is_not_stale():
    committed = OUT.read_text(encoding="utf-8")
    fresh = render()
    assert committed == fresh, (
        "benchmarks/BENCHMARKS.md is stale - run `python -m benchmarks.rollup`"
    )
