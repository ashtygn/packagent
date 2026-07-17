"""`pkgtk models {add,status,chase,intake}` — model librarian CLI."""

from __future__ import annotations

import json

from pkgtk.models.registry import ModelKey, Registry


def _key(args) -> ModelKey:
    return ModelKey(args.part, args.rev, args.corner, args.model_type)


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(prog="pkgtk models")
    parser.add_argument("--db", default="models.db")
    sub = parser.add_subparsers(dest="cmd", required=True)
    for name in ("add", "status", "chase", "intake"):
        sp = sub.add_parser(name)
        if name != "status":
            sp.add_argument("part")
            sp.add_argument("rev")
            sp.add_argument("corner")
            sp.add_argument("model_type")
        if name == "intake":
            sp.add_argument("model_path")
    args = parser.parse_args(argv)

    reg = Registry(args.db)
    if args.cmd == "add":
        reg.add(_key(args))
        print(f"added {_key(args)} -> requested")
    elif args.cmd == "status":
        print(json.dumps(reg.all_rows(), indent=2))
    elif args.cmd == "chase":
        print(reg.chase_email(_key(args)))
    elif args.cmd == "intake":
        verdict = reg.intake(_key(args), args.model_path)
        print(f"intake {verdict['decision']} -> state {reg.state(_key(args))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
