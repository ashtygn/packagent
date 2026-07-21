"""Deterministic zero-LLM graders for agent-eval tasks.

Each grader takes a task directory (containing work/ and meta.json) and returns
{"passed": bool, "reasons": [str, ...]} - reasons list every failed criterion.

Ground truth is RECOMPUTED at grade time from (family, mutation) via the
deterministic generator - meta.json carries no answer key, because the codex
sandbox restricts writes but not reads, so anything on disk near the task is
readable by the agent. Residual risk: the mutation name in meta.json is a hint,
and a determined agent could re-derive answers from the public generator; the
runner's suspect-command detection covers that gap (see evals/README.md).

Graders shell out to the pkgtk CLI exactly as the agent does, so the exit-code
contract (0 clean / 1 findings / 2 usage) is graded end-to-end.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from functools import lru_cache
from pathlib import Path

from benchmarks.mutations import REGISTRY

from pkgtk.checks import run_all
from pkgtk.diff import diff_graphs


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_meta(task_dir: Path) -> dict:
    return json.loads((task_dir / "meta.json").read_text("utf-8"))


@lru_cache(maxsize=1)
def _design():
    from evals.task_gen import clean_design
    return clean_design()


def _mutated(mutation: str):
    return REGISTRY[mutation](_design())


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


def _str_list(value) -> list[str] | None:
    if isinstance(value, list) and all(isinstance(x, str) for x in value):
        return value
    return None


def _pkgtk_verify(work: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["pkgtk", "verify", "graph.json", "--config", "config.json", "--json"],
        cwd=work, capture_output=True, text=True, timeout=120,
    )


def _violation_triples(mutation: str) -> set[tuple]:
    graph, config, _expected = _mutated(mutation)
    return {
        (v.rule_id,
         getattr(v.location, "net", None),
         getattr(v.location, "node_id", None))
        for v in run_all(graph, config)
    }


def grade_diagnose(task_dir: Path) -> dict:
    meta = _load_meta(task_dir)
    work = task_dir / "work"
    reasons: list[str] = []
    _check_inputs_unmodified(work, meta, reasons)
    findings = _load_json_output(work, "findings.json", reasons)
    if findings is not None:
        if not isinstance(findings, list) or not all(
                isinstance(f, dict) for f in findings):
            reasons.append("findings.json is not a JSON array of objects")
        else:
            reported = {
                (f.get("rule_id"), f.get("net"), f.get("node_id"))
                for f in findings
            }
            expected = _violation_triples(meta["mutation"])
            missing = expected - reported
            spurious = reported - expected
            if missing:
                reasons.append(f"missing findings: {sorted(missing)[:3]}")
            if spurious:
                reasons.append(
                    f"{len(spurious)} spurious findings not in the report "
                    f"(e.g. {sorted(spurious)[:2]})"
                )
    return {"passed": not reasons, "reasons": reasons}


def grade_fix(task_dir: Path) -> dict:
    meta = _load_meta(task_dir)
    work = task_dir / "work"
    reasons: list[str] = []
    _check_inputs_unmodified(work, meta, reasons)  # config.json only
    graph = _load_json_output(work, "graph.json", reasons)
    if graph is not None:
        if not isinstance(graph, dict):
            reasons.append("graph.json is not a JSON object")
        else:
            clean = _design().graph
            n_nodes = len(graph.get("nodes") or [])
            n_edges = len(graph.get("edges") or [])
            if n_nodes != len(clean.nodes):
                reasons.append(
                    f"node count {n_nodes} != clean {len(clean.nodes)} "
                    "(repair must remove exactly the defective additions)"
                )
            if n_edges != len(clean.edges):
                reasons.append(
                    f"edge count {n_edges} != clean {len(clean.edges)}"
                )
            proc = _pkgtk_verify(work)
            if proc.returncode != 0:
                reasons.append(
                    f"pkgtk verify exit {proc.returncode} (want 0/clean)")
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
            graph_b, _cfg, _exp = _mutated(meta["mutation"])
            report = diff_graphs(_design().graph, graph_b)
            exp_nets = {c["net"] for c in report["changes"] if c.get("net")}
            exp_classes = {c["class"] for c in report["changes"]}
            nets = _str_list(eco.get("changed_nets"))
            classes = _str_list(eco.get("classes"))
            if nets is None:
                reasons.append("changed_nets must be a JSON array of strings")
            elif set(nets) != exp_nets:
                reasons.append(
                    f"changed_nets {sorted(set(nets))} != expected "
                    f"{sorted(exp_nets)}"
                )
            if classes is None:
                reasons.append("classes must be a JSON array of strings")
            elif set(classes) != exp_classes:
                reasons.append(
                    f"classes {sorted(set(classes))} != expected "
                    f"{sorted(exp_classes)}"
                )
    return {"passed": not reasons, "reasons": reasons}


GRADERS = {
    "diagnose": grade_diagnose,
    "fix": grade_fix,
    "ecodiff": grade_ecodiff,
}


def grade(task_dir: Path) -> dict:
    family = _load_meta(task_dir)["family"]
    return GRADERS[family](task_dir)
