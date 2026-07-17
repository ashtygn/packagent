"""Reject staged changes under fixtures/golden/ unless GOLDEN_EDIT=1 (human use only).

fixtures/golden/ is human-authored ground truth; agents are read-only there.
pre-commit passes the offending staged paths as argv.
"""

import os
import sys


def main() -> int:
    if os.environ.get("GOLDEN_EDIT") == "1":
        return 0
    staged = sys.argv[1:]
    if not staged:
        return 0
    print("golden-guard: fixtures/golden/ is human-authored ground truth.")
    print("Edits are blocked for agents.")
    for path in staged:
        print(f"  blocked: {path}")
    print("If you are the human oracle, re-run with GOLDEN_EDIT=1.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
