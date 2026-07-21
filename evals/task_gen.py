"""Build agent-eval task directories from the Phase-1 benchmark machinery.

Each task is a directory:

    <out>/<task_id>/
        work/       # the agent's working directory (inputs + task.md prompt)
        meta.json   # grader-side data - NEVER placed inside work/

Families:
    diagnose  - mutated graph; agent runs `pkgtk verify` and reports findings.json
    fix       - additively-mutated graph; agent repairs graph.json to verify-clean
    ecodiff   - two revisions; agent runs `pkgtk diff` and reports eco.json

Every generated task is self-validated: the seeded defect must actually be caught by
the deterministic engine at generation time, so a task can never silently test nothing.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import yaml
from benchmarks.mutations import REGISTRY

from pkgtk.checks import run_all
from pkgtk.diff import diff_graphs
from pkgtk.synth.ballmap_gen import GeneratedDesign, GenParams, generate

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "benchmarks" / "cases.yaml"

DIAGNOSE_MUTATIONS = sorted(REGISTRY)
# Additive-only mutations: the correct repair restores the original node/edge counts.
FIX_MUTATIONS = [
    "duplicate_ball_grid",
    "duplicate_die_pad",
    "floating_ball_no_net",
    "floating_die_pad",
    "multi_assignment",
    "nc_collision",
]
# Mutations whose rev-A/rev-B delta is visible to `pkgtk diff` (removal class).
ECODIFF_MUTATIONS = ["diffpair_missing_partner", "diffpair_missing_partner_v2"]

FAMILIES = ("diagnose", "fix", "ecodiff")

_PROMPT_DIAGNOSE = """\
This directory contains a package-design connectivity graph with seeded defects.

1. Run: pkgtk verify graph.json --config config.json --json
   Exit code 1 means violations were found (expected here); parse the JSON report.
2. Write findings.json in this directory: a JSON array with one object per violation,
   copying each violation's "rule_id" and, when present in its location, "net" and
   "node_id". Example element: {"rule_id": "nc.collision", "node_id": "ball_A1"}.

Do not modify graph.json or config.json.
"""

_PROMPT_FIX = """\
`pkgtk verify graph.json --config config.json --json` reports violations (exit code 1).
The defects are additions to an otherwise-clean design.

Repair graph.json with the smallest possible edit so that the same command exits 0
with zero violations. Only remove the defective additions - do not touch unrelated
nodes or edges, and do not modify config.json.
"""

_PROMPT_ECODIFF = """\
revA.json and revB.json are two revisions of a package connectivity graph.

1. Run: pkgtk diff revA.json revB.json --json
   Exit code 1 means semantic changes were found (expected here).
2. Write eco.json in this directory:
   {"changed_nets": [<every net name appearing in the diff changes>],
    "classes": [<the distinct change classes reported>]}

Do not modify revA.json or revB.json.
"""


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _dump(model) -> str:
    return model.model_dump_json(exclude_none=True)


def _violation_matches(violation, expected: dict) -> bool:
    loc = violation.location
    return (
        violation.rule_id == expected["rule_id"]
        and (not expected.get("node_id")
             or getattr(loc, "node_id", None) == expected["node_id"])
        and (not expected.get("net") or getattr(loc, "net", None) == expected["net"])
    )


def clean_design() -> GeneratedDesign:
    spec = yaml.safe_load(CASES.read_text("utf-8"))
    return generate(GenParams(**spec["design"]))


def _init_task(out_dir: Path, task_id: str, prompt: str) -> tuple[Path, Path]:
    task_dir = out_dir / task_id
    work = task_dir / "work"
    work.mkdir(parents=True, exist_ok=False)
    (work / "task.md").write_text(prompt, encoding="utf-8")
    return task_dir, work


def _write_meta(task_dir: Path, meta: dict) -> None:
    (task_dir / "meta.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")


def _gen_diagnose(design: GeneratedDesign, out_dir: Path, mutation: str) -> str:
    task_id = f"diagnose-{mutation}"
    graph, config, expected = REGISTRY[mutation](design)
    violations = run_all(graph, config)
    if not any(_violation_matches(v, expected) for v in violations):
        raise AssertionError(f"{task_id}: seeded defect not caught by engine")
    task_dir, work = _init_task(out_dir, task_id, _PROMPT_DIAGNOSE)
    (work / "graph.json").write_text(_dump(graph), encoding="utf-8")
    (work / "config.json").write_text(_dump(config), encoding="utf-8")
    _write_meta(task_dir, {
        "task_id": task_id,
        "family": "diagnose",
        "mutation": mutation,
        "expected": expected,
        "input_sha256": {
            "graph.json": _sha256(work / "graph.json"),
            "config.json": _sha256(work / "config.json"),
        },
    })
    return task_id


def _gen_fix(design: GeneratedDesign, out_dir: Path, mutation: str) -> str:
    task_id = f"fix-{mutation}"
    graph, config, expected = REGISTRY[mutation](design)
    violations = run_all(graph, config)
    if not any(_violation_matches(v, expected) for v in violations):
        raise AssertionError(f"{task_id}: seeded defect not caught by engine")
    task_dir, work = _init_task(out_dir, task_id, _PROMPT_FIX)
    (work / "graph.json").write_text(_dump(graph), encoding="utf-8")
    (work / "config.json").write_text(_dump(config), encoding="utf-8")
    _write_meta(task_dir, {
        "task_id": task_id,
        "family": "fix",
        "mutation": mutation,
        "expected": expected,
        # The repair must restore the pre-mutation shape exactly.
        "clean_node_count": len(design.graph.nodes),
        "clean_edge_count": len(design.graph.edges),
        "input_sha256": {"config.json": _sha256(work / "config.json")},
    })
    return task_id


def _gen_ecodiff(design: GeneratedDesign, out_dir: Path, mutation: str) -> str:
    task_id = f"ecodiff-{mutation}"
    graph_b, _config, expected = REGISTRY[mutation](design)
    report = diff_graphs(design.graph, graph_b)
    changed_nets = {c["net"] for c in report["changes"] if c.get("net")}
    classes = {c["class"] for c in report["changes"]}
    if expected["net"] not in changed_nets:
        raise AssertionError(f"{task_id}: expected net not visible to pkgtk diff")
    task_dir, work = _init_task(out_dir, task_id, _PROMPT_ECODIFF)
    (work / "revA.json").write_text(_dump(design.graph), encoding="utf-8")
    (work / "revB.json").write_text(_dump(graph_b), encoding="utf-8")
    _write_meta(task_dir, {
        "task_id": task_id,
        "family": "ecodiff",
        "mutation": mutation,
        "expected": {
            "net": expected["net"],
            "changed_nets": sorted(changed_nets),
            "classes": sorted(classes),
        },
        "input_sha256": {
            "revA.json": _sha256(work / "revA.json"),
            "revB.json": _sha256(work / "revB.json"),
        },
    })
    return task_id


_GENERATORS = {
    "diagnose": (_gen_diagnose, DIAGNOSE_MUTATIONS),
    "fix": (_gen_fix, FIX_MUTATIONS),
    "ecodiff": (_gen_ecodiff, ECODIFF_MUTATIONS),
}


def build_tasks(
    out_dir: Path,
    families: tuple[str, ...] = FAMILIES,
    limit_per_family: int | None = None,
) -> list[str]:
    """Generate task directories under out_dir; returns generated task ids."""
    unknown = set(families) - set(_GENERATORS)
    if unknown:
        raise ValueError(f"unknown families: {sorted(unknown)}")
    design = clean_design()
    out_dir.mkdir(parents=True, exist_ok=True)
    task_ids = []
    for family in families:
        gen, mutations = _GENERATORS[family]
        for mutation in mutations[:limit_per_family]:
            task_ids.append(gen(design, out_dir, mutation))
    return task_ids
