"""Phase-1 benchmark runner.

Generates the clean synthetic design (false-positive gate: must be zero violations),
injects each seeded defect from cases.yaml, asserts the check engine catches it at the
correct location, and writes benchmarks/BENCHMARKS.md with the catch-rate table.

`exact` cases additionally assert the full violation set equals the hand-authored
golden under fixtures/golden/bench/<id>.json.

Usage: python benchmarks/run.py   (exit 0 iff clean design is clean AND 20/20 caught)
"""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from benchmarks.mutations import REGISTRY
from pkgtk.checks import run_all
from pkgtk.synth.ballmap_gen import GenParams, generate

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "benchmarks" / "cases.yaml"
GOLDEN_BENCH = ROOT / "fixtures" / "golden" / "bench"
# Phase-1-only report; the canonical combined file is benchmarks/BENCHMARKS.md
# (written by benchmarks.rollup, which aggregates every phase).
OUT = ROOT / "benchmarks" / "BENCHMARKS.phase1.md"


def _matches(v, exp: dict) -> bool:
    return (
        v.rule_id == exp["rule_id"]
        and (not exp.get("node_id")
             or getattr(v.location, "node_id", None) == exp["node_id"])
        and (not exp.get("net") or getattr(v.location, "net", None) == exp["net"])
    )


def run() -> dict:
    spec = yaml.safe_load(CASES.read_text("utf-8"))
    params = GenParams(**spec["design"])
    design = generate(params)

    clean = run_all(design.graph, design.config)
    n_balls = sum(1 for n in design.graph.nodes if n.kind == "ball")

    results = []
    for case in spec["cases"]:
        mutate = REGISTRY[case["mutation"]]
        graph, config, expected = mutate(design)
        violations = run_all(graph, config)
        caught = any(_matches(v, expected) for v in violations)
        exact_ok = None
        if case.get("exact"):
            gpath = GOLDEN_BENCH / f"{case['id']}.json"
            golden = json.loads(gpath.read_text("utf-8"))
            dumped = [v.model_dump(mode="json", exclude_none=True) for v in violations]
            exact_ok = dumped == golden
        results.append({
            "id": case["id"], "family": case["family"],
            "mutation": case["mutation"], "rule_id": expected["rule_id"],
            "caught": caught, "exact": case.get("exact", False),
            "exact_ok": exact_ok, "n_violations": len(violations),
        })

    caught_n = sum(1 for r in results if r["caught"])
    exact_fail = [r["id"] for r in results if r["exact"] and r["exact_ok"] is False]
    return {
        "n_balls": n_balls,
        "clean_violations": len(clean),
        "total": len(results),
        "caught": caught_n,
        "exact_failures": exact_fail,
        "results": results,
    }


def render(summary: dict) -> str:
    lines = [
        "# BENCHMARKS — Phase 1 (ball-map verifier)",
        "",
        "> **Generated file** — produced by `python benchmarks/run.py`. Do not edit.",
        "",
        f"- Synthetic design: **{summary['n_balls']} balls**, clean-design "
        f"violations: **{summary['clean_violations']}** (false-positive gate).",
        f"- Seeded-defect catch rate: **{summary['caught']}/{summary['total']}**.",
        "",
        "| Case | Family | Seeded rule | Caught | Exact |",
        "|------|--------|-------------|:------:|:-----:|",
    ]
    for r in summary["results"]:
        exact = "n/a" if not r["exact"] else ("yes" if r["exact_ok"] else "NO")
        lines.append(f"| {r['id']} | {r['family']} | `{r['rule_id']}` | "
                     f"{'yes' if r['caught'] else 'NO'} | {exact} |")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    summary = run()
    OUT.write_text(render(summary), encoding="utf-8")
    ok = (summary["clean_violations"] == 0
          and summary["caught"] == summary["total"]
          and not summary["exact_failures"])
    print(f"clean={summary['clean_violations']} "
          f"caught={summary['caught']}/{summary['total']} "
          f"exact_failures={summary['exact_failures']}")
    print(f"wrote {OUT}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
