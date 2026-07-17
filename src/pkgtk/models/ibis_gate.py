"""IBIS intake gate: wrap the ibischk 'golden parser' executable.

The executable is never bundled (license-restricted source); its path comes from
config/env (``PKGTK_IBISCHK``). Output is line-oriented ERROR/WARNING/NOTE; we parse it
into a structured verdict preserving the raw lines. Tests parse *captured* stdout so CI
needs no executable; a live run is available when the executable is present.

Mapping: any ERROR -> reject; WARNING(s) only -> pass-with-flags; clean -> pass.
"""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

_LINE = re.compile(r"^(ERROR|WARNING|NOTE)\b", re.IGNORECASE)
_SUMMARY = re.compile(r"(\d+)\s+errors?,\s*(\d+)\s+warnings?,\s*(\d+)\s+notes?",
                      re.IGNORECASE)


def parse_ibischk_output(text: str) -> dict:
    errors = warnings = notes = 0
    matched_summary = False
    raw = text.splitlines()
    for line in raw:
        m = _SUMMARY.search(line)
        if m:
            errors, warnings, notes = (int(m.group(1)), int(m.group(2)),
                                       int(m.group(3)))
            matched_summary = True
    if not matched_summary:
        for line in raw:
            m = _LINE.match(line.strip())
            if not m:
                continue
            kind = m.group(1).upper()
            errors += kind == "ERROR"
            warnings += kind == "WARNING"
            notes += kind == "NOTE"

    if errors > 0:
        decision = "reject"
    elif warnings > 0:
        decision = "pass-with-flags"
    else:
        decision = "pass"
    return {
        "errors": errors,
        "warnings": warnings,
        "notes": notes,
        "decision": decision,
        "raw_lines": raw,
    }


def ibischk_path() -> str | None:
    return os.environ.get("PKGTK_IBISCHK")


def run_ibischk(model_path: str | Path, exe: str | None = None) -> dict:
    """Run ibischk on a model and return the structured verdict.

    Raises FileNotFoundError if no executable is configured/available (callers in
    tests skip in that case and use captured-output fixtures instead).
    """
    exe = exe or ibischk_path()
    if not exe:
        raise FileNotFoundError(
            "ibischk executable not configured (set PKGTK_IBISCHK)")
    proc = subprocess.run([exe, str(model_path)], capture_output=True, text=True)
    verdict = parse_ibischk_output(proc.stdout + "\n" + proc.stderr)
    verdict["model"] = Path(model_path).name
    return verdict
