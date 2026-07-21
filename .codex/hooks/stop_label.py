#!/usr/bin/env python3
"""Codex Stop-hook: label every in-repo turn for the behavioral-tuning corpus.

Receives the Stop event JSON on stdin (session_id, turn_id, transcript_path,
last_assistant_message, cwd, ...) and appends one label line to
~/.codex/labels/packagent-turns.jsonl. Cheap by design: records git dirtiness as a
coarse "did the agent leave edits" signal; real grading happens in evals/.

Never blocks the agent: always exits 0, even on internal errors.
"""

import json
import subprocess
import sys
import time
from pathlib import Path


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except Exception:
        return 0
    cwd = event.get("cwd") or "."
    try:
        dirty = subprocess.run(
            ["git", "-C", cwd, "status", "--porcelain"],
            capture_output=True, text=True, timeout=10,
        ).stdout.strip()
    except Exception:
        dirty = None
    # Deliberately no message content here: labels may leave the machine one
    # day, and assistant text can quote NDA material. The transcript_path
    # pointer stays local under ~/.codex; content extraction happens only
    # behind the plan's NDA scrub.
    label = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "session_id": event.get("session_id"),
        "turn_id": event.get("turn_id"),
        "cwd": cwd,
        "transcript_path": event.get("transcript_path"),
        "model": event.get("model"),
        "git_dirty_files": None if dirty is None else len(dirty.splitlines()),
    }
    try:
        out = Path.home() / ".codex" / "labels"
        out.mkdir(parents=True, exist_ok=True)
        with (out / "packagent-turns.jsonl").open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(label) + "\n")
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
