"""Unified `pkgtk` CLI. Assembly only — dispatches to the per-wedge subcommands.

Exit-code convention: 0 = clean, 1 = violations/infeasible, 2 = usage, 3 = internal.
Subcommands present in this build: verify, diff, check, models, escape, template, pdn.
Absent (deferred, see docs/PHASE-NOTES.md): com (Phase 3 cut), extract/ingest (Phase 4
live flows + Phase 1 xlsx).
"""

from __future__ import annotations

import sys

from pkgtk import __version__
from pkgtk.cli import diff as diff_cli
from pkgtk.cli import escape as escape_cli
from pkgtk.cli import models as models_cli
from pkgtk.cli import pdn as pdn_cli
from pkgtk.cli import template as template_cli
from pkgtk.cli import verify as verify_cli

SUBCOMMANDS = {
    "verify": verify_cli.main,
    "diff": diff_cli.main,
    "models": models_cli.main,
    "escape": escape_cli.main,
    "template": template_cli.main,
    "pdn": pdn_cli.main,
}

# `check` (geometry lint) needs klayout; register it only if importable.
try:
    from pkgtk.cli import check as check_cli
    SUBCOMMANDS["check"] = check_cli.main
except Exception:  # pragma: no cover - klayout optional
    pass

_ABSENT = {
    "com": "Phase 3 COM runner cut (needs vendored port).",
    "extract": "Phase 4 rule-sheet extraction (needs live LLM + xlsx).",
    "ingest": "Phase 4 mapping inference / Phase 1 xlsx ingestion (deferred).",
}


def _usage() -> str:
    avail = ", ".join(sorted(SUBCOMMANDS))
    return (f"pkgtk {__version__} - package-design verification toolkit\n"
            f"usage: pkgtk <command> [options]\n"
            f"commands: {avail}\n"
            f"(deferred: {', '.join(sorted(_ABSENT))} - see docs/PHASE-NOTES.md)")


def app(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ("-h", "--help"):
        print(_usage())
        return 0 if argv[:1] in ([], ["-h"], ["--help"]) else 2
    if argv[0] in ("-V", "--version"):
        print(__version__)
        return 0
    cmd, rest = argv[0], argv[1:]
    if cmd in _ABSENT:
        print(f"pkgtk {cmd}: not available in this build - {_ABSENT[cmd]}")
        return 2
    if cmd not in SUBCOMMANDS:
        print(f"pkgtk: unknown command {cmd!r}\n{_usage()}")
        return 2
    return SUBCOMMANDS[cmd](rest)


if __name__ == "__main__":
    raise SystemExit(app())
