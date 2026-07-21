"""Deterministic zero-LLM graders for agent-eval tasks.

Each grader takes a task directory (containing work/ and meta.json) and returns
{"passed": bool, "reasons": [str, ...]} - reasons list every failed criterion.
Graders shell out to the pkgtk CLI exactly as the agent does, so the exit-code
contract (0 clean / 1 findings / 2 usage) is graded end-to-end.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_meta(task_dir: Path) -> dict:
    return json.loads((task_dir / "meta.json").read_text("utf-8"))


def _check_inputs_unmodified(work: Path, meta: dict, reasons: list[str]) -> None:
    for name, digest in meta.get("input_sha256", {}).items():
        path = work / name
        if not path.is_file():
            reasons.append(f"input {name} was deleted")
        elif _sha256(path) != digest:
            reasons.append(f"input {name} was modified")


def _load_json_output(work: Path, name: str, reasons: list[str]):
    path = work / name
    if not path.is_file():
        reasons.append(f"{name} not written")
        return None
    try:
        return json.loads(path.read_text("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as err:
        reasons.append(f"{name} is not valid JSON: {err}")
        return None


def _pkgtk_verify(work: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["pkgtk", "verify", "graph.json", "--config", "config.json", "--json"],
        cwd=work, capture_output=True, text=True, timeout=120,
    )


def grade_diagnose(task_dir: Path) -> dict:
    meta = _load_meta(task_dir)
    work = task_dir / "work"
    reasons: list[str] = []
    _check_inputs_unmodified(work, meta, reasons)
    findings = _load_json_output(work, "findings.json", reasons)
    if findings is not None:
        if not isinstance(findings, list):
            reasons.append("findings.json is not a JSON array")
        else:
            exp = meta["expected"]
            def _hit(f):
                return (
                    isinstance(f, dict)
                    and f.get("rule_id") == exp["rule_id"]
                    and (not exp.get("net") or f.get("net") == exp["net"])
                    and (not exp.get("node_id") or f.get("node_id") == exp["node_id"])
                )
            if not any(_hit(f) for f in findings):
                reasons.append(f"expected finding not reported: {exp}")
    return {"passed": not reasons, "reasons": reasons}


def grade_fix(task_dir: Path) -> dict:
    meta = _load_meta(task_dir)
    work = task_dir / "work"
    reasons: list[str] = []
    _check_inputs_unmodified(work, meta, reasons)  # config.json only
    graph = _load_json_output(work, "graph.json", reasons)
    if graph is not None:
        n_nodes = len(graph.get("nodes", []))
        n_edges = len(graph.get("edges", []))
        if n_nodes != meta["clean_node_count"]:
            reasons.append(
                f"node count {n_nodes} != clean {meta['clean_node_count']} "
                "(repair must remove exactly the defective additions)"
            )
        if n_edges != meta["clean_edge_count"]:
            reasons.append(
                f"edge count {n_edges} != clean {meta['clean_edge_count']}"
            )
        proc = _pkgtk_verify(work)
        if proc.returncode != 0:
            reasons.append(f"pkgtk verify exit {proc.returncode} (want 0/clean)")
    return {"passed": not reasons, "reasons": reasons}


def grade_ecodiff(task_dir: Path) -> dict:
    meta = _load_meta(task_dir)
    work = task_dir / "work"
    reasons: list[str] = []
    _check_inputs_unmodified(work, meta, reasons)
    eco = _load_json_output(work, "eco.json", reasons)
    if eco is not None:
        if not isinstance(eco, dict):
            reasons.append("eco.json is not a JSON object")
        else:
            exp = meta["expected"]
            reported_nets = eco.get("changed_nets") or []
            reported_classes = eco.get("classes") or []
            if exp["net"] not in reported_nets:
                reasons.append(f"changed_nets missing expected net {exp['net']!r}")
            missing = [c for c in exp["classes"] if c not in reported_classes]
            if missing:
                reasons.append(f"classes missing {missing}")
    return {"passed": not reasons, "reasons": reasons}


GRADERS = {
    "diagnose": grade_diagnose,
    "fix": grade_fix,
    "ecodiff": grade_ecodiff,
}


def grade(task_dir: Path) -> dict:
    family = _load_meta(task_dir)["family"]
    return GRADERS[family](task_dir)
