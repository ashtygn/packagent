"""`pkgtk diff A B` — semantic ECO diff between two Connectivity Graphs."""

from __future__ import annotations

import json
from pathlib import Path

from pkgtk.diff.engine import diff_graphs
from pkgtk.diff.report import render_markdown
from pkgtk.schemas.graph import ConnectivityGraph


def run_diff(path_a: str | Path, path_b: str | Path) -> dict:
    a = ConnectivityGraph.model_validate_json(Path(path_a).read_text("utf-8"))
    b = ConnectivityGraph.model_validate_json(Path(path_b).read_text("utf-8"))
    return diff_graphs(a, b)


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(prog="pkgtk diff")
    parser.add_argument("graph_a", help="path to revision-A Connectivity Graph JSON")
    parser.add_argument("graph_b", help="path to revision-B Connectivity Graph JSON")
    parser.add_argument("--json", action="store_true", help="emit JSON diff")
    args = parser.parse_args(argv)

    diff = run_diff(args.graph_a, args.graph_b)
    if args.json:
        print(json.dumps(diff, indent=2, sort_keys=True))
    else:
        print(render_markdown(diff))
    total = sum(diff["summary"].values())
    return 1 if total else 0


if __name__ == "__main__":
    raise SystemExit(main())
