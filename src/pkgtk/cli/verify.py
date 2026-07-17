"""`pkgtk verify` — run all ball-map checks against a Connectivity Graph.

Exit codes: 0 = no hard violations, 1 = at least one hard violation, 2 = usage.
"""

from __future__ import annotations

import json
from pathlib import Path

from pkgtk.checks import RunConfig, run_all
from pkgtk.schemas.graph import ConnectivityGraph


def verify_graph(graph_path: str | Path, config_path: str | Path | None = None) -> dict:
    """Load a graph (+ optional config), run every check, return a report dict."""
    graph = ConnectivityGraph.model_validate_json(Path(graph_path).read_text("utf-8"))
    if config_path and Path(config_path).is_file():
        config = RunConfig.model_validate_json(Path(config_path).read_text("utf-8"))
    else:
        config = RunConfig()
    violations = run_all(graph, config)
    dumped = [v.model_dump(mode="json", exclude_none=True) for v in violations]
    return {
        "design": graph.design,
        "rev": graph.rev,
        "violation_count": len(dumped),
        "violations": dumped,
    }


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(prog="pkgtk verify")
    parser.add_argument("graph", help="path to a Connectivity Graph JSON")
    parser.add_argument("--config", help="path to a run-config JSON", default=None)
    parser.add_argument("--json", action="store_true", help="emit JSON report")
    args = parser.parse_args(argv)

    report = verify_graph(args.graph, args.config)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"{report['design']} rev {report['rev']}: "
              f"{report['violation_count']} violation(s)")
        for v in report["violations"]:
            loc = v["location"]
            where = loc.get("node_id") or loc.get("net") or "?"
            print(f"  [{v['severity']}] {v['rule_id']} @ {where}")
    return 1 if report["violation_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
