"""Offline tests for the agent-eval harness: task generation + graders.

No codex, no network - an 'oracle agent' solves tasks via the pkgtk APIs/CLI and the
graders must pass it; corrupted, spammed, incomplete, or cheating outputs must fail.
Keeps `make ci` hermetic while proving the harness would grade a real agent correctly.
"""

import json
import subprocess

import pytest
from evals.graders import grade
from evals.run_eval import _is_suspect_command
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


def _oracle_findings(work):
    proc = subprocess.run(
        ["pkgtk", "verify", "graph.json", "--config", "config.json", "--json"],
        cwd=work, capture_output=True, text=True, timeout=120,
    )
    assert proc.returncode == 1, "seeded task must report findings (exit 1)"
    report = json.loads(proc.stdout)
    return [
        {"rule_id": v["rule_id"], **{
            k: v["location"][k] for k in ("net", "node_id")
            if v.get("location", {}).get(k) is not None
        }}
        for v in report["violations"]
    ]


def test_task_layout_and_no_answer_key(taskset):
    (task_dir,) = taskset(("diagnose",))
    work = task_dir / "work"
    assert (work / "task.md").is_file()
    assert (work / "graph.json").is_file()
    assert (work / "config.json").is_file()
    meta = _meta(task_dir)
    assert meta["family"] == "diagnose"
    # The sandbox restricts writes, not reads: nothing near the task may hold
    # the answer key (the agent can trivially `cat ../meta.json`).
    assert "expected" not in meta
    assert "clean_node_count" not in meta
    assert not (work / "meta.json").exists()


def test_diagnose_oracle_passes_and_wrong_output_fails(taskset):
    (task_dir,) = taskset(("diagnose",))
    work = task_dir / "work"
    findings = _oracle_findings(work)
    (work / "findings.json").write_text(json.dumps(findings), encoding="utf-8")
    assert grade(task_dir) == {"passed": True, "reasons": []}

    (work / "findings.json").write_text(
        json.dumps([{"rule_id": "bogus.rule"}]), encoding="utf-8")
    result = grade(task_dir)
    assert not result["passed"]
    assert any("missing findings" in r for r in result["reasons"])


def test_diagnose_grader_rejects_spam(taskset):
    """Zero-knowledge spam (every rule x every identifier) must not pass."""
    (task_dir,) = taskset(("diagnose",))
    work = task_dir / "work"
    findings = _oracle_findings(work)
    spam = findings + [{"rule_id": "nc.collision", "node_id": f"ball_{i}"}
                       for i in range(50)]
    (work / "findings.json").write_text(json.dumps(spam), encoding="utf-8")
    result = grade(task_dir)
    assert not result["passed"]
    assert any("spurious" in r for r in result["reasons"])


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


def test_fix_grader_survives_non_object_json(taskset):
    """Valid JSON that is not an object must fail gracefully, not crash."""
    (task_dir,) = taskset(("fix",))
    (task_dir / "work" / "graph.json").write_text("[1, 2, 3]", encoding="utf-8")
    result = grade(task_dir)
    assert not result["passed"]
    assert any("not a JSON object" in r for r in result["reasons"])


def test_fix_grader_fails_unrepaired_graph(taskset):
    (task_dir,) = taskset(("fix",))
    result = grade(task_dir)
    assert not result["passed"]  # untouched mutated graph cannot grade clean


def _oracle_eco(work):
    proc = subprocess.run(
        ["pkgtk", "diff", "revA.json", "revB.json", "--json"],
        cwd=work, capture_output=True, text=True, timeout=120,
    )
    assert proc.returncode == 1, "revisions must differ (exit 1)"
    report = json.loads(proc.stdout)
    return {
        "changed_nets": sorted({c["net"] for c in report["changes"] if c.get("net")}),
        "classes": sorted({c["class"] for c in report["changes"]}),
    }


def test_ecodiff_oracle_passes_and_incomplete_fails(taskset):
    (task_dir,) = taskset(("ecodiff",))
    work = task_dir / "work"
    eco = _oracle_eco(work)
    assert len(eco["changed_nets"]) > 1, "test needs a multi-net diff"
    (work / "eco.json").write_text(json.dumps(eco), encoding="utf-8")
    assert grade(task_dir) == {"passed": True, "reasons": []}

    # Dropping any changed net must fail (the prompt demands every net).
    partial = {**eco, "changed_nets": eco["changed_nets"][:1]}
    (work / "eco.json").write_text(json.dumps(partial), encoding="utf-8")
    assert not grade(task_dir)["passed"]


def test_ecodiff_grader_rejects_free_text(taskset):
    """String values must not pass via Python substring membership."""
    (task_dir,) = taskset(("ecodiff",))
    work = task_dir / "work"
    eco = _oracle_eco(work)
    prose = {
        "changed_nets": "I refuse but mention " + " ".join(eco["changed_nets"]),
        "classes": " and ".join(eco["classes"]),
    }
    (work / "eco.json").write_text(json.dumps(prose), encoding="utf-8")
    result = grade(task_dir)
    assert not result["passed"]
    assert any("array of strings" in r for r in result["reasons"])


def test_build_tasks_refuses_non_empty_out(tmp_path):
    (tmp_path / "leftover.txt").write_text("x", encoding="utf-8")
    with pytest.raises(ValueError, match="non-empty"):
        build_tasks(tmp_path, families=("diagnose",), limit_per_family=1)


def test_suspect_command_detection():
    assert _is_suspect_command("cat ../meta.json")
    assert _is_suspect_command("python -c 'print(open(\"../meta.json\").read())'")
    assert not _is_suspect_command("pkgtk verify graph.json --json")


def test_full_suite_generates(tmp_path):
    ids = build_tasks(tmp_path / "suite")
    assert len(ids) == 20 + 6 + 2  # diagnose + fix + ecodiff
    assert len(ids) == len(set(ids))
