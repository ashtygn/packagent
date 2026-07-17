"""`pkgtk template` — interface-template compliance check of a ball map."""

from __future__ import annotations

import json
from pathlib import Path

from pkgtk.oracles.template_check import check_template, load_template
from pkgtk.schemas.graph import ConnectivityGraph


def main(argv: list[str] | None = None) -> int:
    import argparse

    p = argparse.ArgumentParser(prog="pkgtk template")
    p.add_argument("graph")
    p.add_argument("--template", required=True)
    p.add_argument("--json", action="store_true")
    args = p.parse_args(argv)

    graph = ConnectivityGraph.model_validate_json(Path(args.graph).read_text("utf-8"))
    res = check_template(graph, load_template(args.template))
    dumped = [v.model_dump(mode="json", exclude_none=True) for v in res.violations]
    out = {"violations": dumped, "flagged_unknown": res.flagged_unknown}
    if args.json:
        print(json.dumps(out, indent=2, sort_keys=True))
    else:
        print(f"{len(dumped)} mismatch(es); {len(res.flagged_unknown)} unknown flagged")
        for v in dumped:
            print(f"  {v['location']['net']}: {v['measured']} != {v['required']}")
    return 1 if dumped else 0


if __name__ == "__main__":
    raise SystemExit(main())
