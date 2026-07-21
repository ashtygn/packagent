"""Offline tests for the agent-eval harness: task generation + graders.

No codex, no network - an 'oracle agent' solves tasks via the pkgtk APIs/CLI and the
graders must pass it; corrupted outputs must fail. Keeps `make ci` hermetic while
proving the harness would grade a real agent correctly.
"""

import json
import shutil
import subprocess

import pytest
from evals.graders import grade
from evals.task_gen import build_tasks, clean_design


@pytest.fixture(scope="module")
def design():
    return clean_design()


@pytest.fixture()
def taskset(tmp_path):
    def _build(families, limit=1):
        ids = build_tasks(tmp_path, families=families, limit_per_family=limit)
        return [tmp_path / t for t in ids]
    return _build


def _meta(task_dir):
    return json.loads((task_dir / "meta.json").read_text("utf-8"))


def test_task_layout_and_self_validation(taskset):
    (task_dir,) = taskset(("diagnose",))
    work = task_dir / "work"
    assert (work / "task.md").is_file()
    assert (work / "graph.json").is_file()
    assert (work / "config.json").is_file()
    meta = _meta(task_dir)
    assert meta["family"] == "diagnose"
    assert meta["expected"]["rule_id"]
    # grader-side data must not leak into the agent's cwd
    assert not (work / "meta.json").exists()


def test_diagnose_oracle_passes_and_wrong_output_fails(taskset):
    (task_dir,) = taskset(("diagnose",))
    work = task_dir / "work"
    proc = subprocess.run(
        ["pkgtk", "verify", "graph.json", "--config", "config.json", "--json"],
        cwd=work, capture_output=True, text=True, timeout=120,
    )
    assert proc.returncode == 1, "seeded task must report findings (exit 1)"
    report = json.loads(proc.stdout)
    findings = [
        {"rule_id": v["rule_id"], **{
            k: v["location"][k] for k in ("net", "node_id")
            if v.get("location", {}).get(k) is not None
        }}
        for v in report["violations"]
    ]
    (work / "findings.json").write_text(json.dumps(findings), encoding="utf-8")
    assert grade(task_dir) == {"passed": True, "reasons": []}

    (work / "findings.json").write_text(
        json.dumps([{"rule_id": "bogus.rule"}]), encoding="utf-8")
    result = grade(task_dir)
    assert not result["passed"]
    assert any("expected finding" in r for r in result["reasons"])


def test_diagnose_grader_rejects_modified_inputs(taskset):
    (task_dir,) = taskset(("diagnose",))
    work = task_dir / "work"
    (work / "findings.json").write_text("[]", encoding="utf-8")
    (work / "graph.json").write_text("{}", encoding="utf-8")
    result = grade(task_dir)
    assert not result["passed"]
    assert any("modified" in r for r in result["reasons"])


def test_fix_oracle_passes_and_cheating_fails(taskset, design):
    (task_dir,) = taskset(("fix",))
    work = task_dir / "work"
    # Oracle repair: the clean pre-mutation graph (regenerated deterministically).
    (work / "graph.json").write_text(
        design.graph.model_dump_json(exclude_none=True), encoding="utf-8")
    assert grade(task_dir) == {"passed": True, "reasons": []}

    # Cheating repair: emptying the graph must fail the count guard.
    (work / "graph.json").write_text(
        json.dumps({"design": "x", "rev": "A", "nodes": [], "edges": []}),
        encoding="utf-8")
    result = grade(task_dir)
    assert not result["passed"]
    assert any("node count" in r for r in result["reasons"])


def test_fix_grader_fails_unrepaired_graph(taskset):
    (task_dir,) = taskset(("fix",))
    result = grade(task_dir)
    assert not result["passed"]  # untouched mutated graph cannot grade clean


def test_ecodiff_oracle_passes_and_missing_net_fails(taskset):
    (task_dir,) = taskset(("ecodiff",))
    work = task_dir / "work"
    proc = subprocess.run(
        ["pkgtk", "diff", "revA.json", "revB.json", "--json"],
        cwd=work, capture_output=True, text=True, timeout=120,
    )
    assert proc.returncode == 1, "revisions must differ (exit 1)"
    report = json.loads(proc.stdout)
    eco = {
        "changed_nets": sorted({c["net"] for c in report["changes"] if c.get("net")}),
        "classes": sorted({c["class"] for c in report["changes"]}),
    }
    (work / "eco.json").write_text(json.dumps(eco), encoding="utf-8")
    assert grade(task_dir) == {"passed": True, "reasons": []}

    eco["changed_nets"] = []
    (work / "eco.json").write_text(json.dumps(eco), encoding="utf-8")
    result = grade(task_dir)
    assert not result["passed"]


def test_full_suite_generates(tmp_path):
    ids = build_tasks(tmp_path)
    assert len(ids) == 20 + 6 + 2  # diagnose + fix + ecodiff
    assert len(ids) == len(set(ids))
    shutil.rmtree(tmp_path)
