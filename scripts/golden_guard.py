"""Reject staged changes under fixtures/golden/ unless GOLDEN_EDIT=1 (human use only).

fixtures/golden/ is human-authored ground truth; agents are read-only there.
Queries the staged diff directly (rather than trusting pre-commit's filename
list) so deletions and renames out of the directory are caught too.
"""

import os
import subprocess


def staged_golden_paths() -> list[str]:
    out = subprocess.run(
        ["git", "diff", "--cached", "--name-status", "--no-renames",
         "--", "fixtures/golden/"],
        capture_output=True,
        text=True,
        check=True,
    )
    return [line for line in out.stdout.splitlines() if line.strip()]

def main() -> int:
    if os.environ.get("GOLDEN_EDIT") == "1":
        return 0
    staged = staged_golden_paths()
    if not staged:
        return 0
    print("golden-guard: fixtures/golden/ is human-authored ground truth.")
    print("Adds, edits, deletions, and renames there are blocked for agents.")
    for line in staged:
        print(f"  blocked: {line}")
    print("If you are the human oracle, re-run with GOLDEN_EDIT=1.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
