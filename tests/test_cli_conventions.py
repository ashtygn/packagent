"""Phase-6 CLI convention tests: help works, exit codes honored on golden inputs."""

from pkgtk.cli.main import app
from pkgtk.schemas import schemas_dir

REPO = schemas_dir().parent


def test_help_exits_zero():
    assert app(["--help"]) == 0


def test_version():
    assert app(["--version"]) == 0


def test_unknown_command_is_usage_error():
    assert app(["nonexistent"]) == 2


def test_deferred_command_reports_cleanly():
    assert app(["com"]) == 2  # absent, reported, not a crash


def test_verify_clean_exits_zero():
    rc = app(["verify", str(REPO / "fixtures/golden/graphs/clean/graph.json"),
              "--config", str(REPO / "fixtures/golden/graphs/clean/config.json")])
    assert rc == 0


def test_verify_defect_exits_one():
    d = REPO / "fixtures/golden/graphs/bijection_multi_assignment"
    rc = app(["verify", str(d / "graph.json")])
    assert rc == 1


def test_diff_with_changes_exits_one():
    rc = app(["diff", str(REPO / "fixtures/golden/diff/revA.json"),
              str(REPO / "fixtures/golden/diff/revB.json")])
    assert rc == 1


def test_template_swap_exits_one():
    rc = app(["template", str(REPO / "fixtures/golden/templates/swapped.json"),
              "--template", str(REPO / "fixtures/golden/templates/template.yaml")])
    assert rc == 1


def test_pdn_runs():
    assert app(["pdn"]) == 0
