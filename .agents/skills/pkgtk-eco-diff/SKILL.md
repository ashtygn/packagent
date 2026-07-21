---
name: pkgtk-eco-diff
description: Compare two revisions of a package connectivity graph with pkgtk diff - semantic ECO change classification (added/removed/moved nets, broken pairs), JSON output. Use for any "what changed between revA and revB" request.
---

# pkgtk-eco-diff — semantic ECO diff workflow

## Command

```
pkgtk diff <revA.json> <revB.json> --json
```

Exit codes: `0` identical (semantically) · `1` changes found (success-with-findings)
· `2` usage error. Order matters: A is the baseline, B the new revision.

## JSON report shape

```json
{"design": "...", "rev_a": "...", "rev_b": "...",
 "changes": [{"class": "removed", "net": "A11_N", "interface": "IF0", ...}],
 "summary": {"removed": 1, "pair_broken": 1},
 "by_interface": {"IF0": {...}}}
```

Change classes include `added`, `removed`, `moved`, `renamed`, `pair_broken`,
`match_group_broken` (taxonomy: docs/checks-spec.md §diff). Primary identity is the
net name; secondary is ball grid position — a net that keeps its name but moves
grid position is `moved`, not removed+added.

## Workflow

1. Run the command; exit 1 ⇒ parse `changes`.
2. Report per-change `class` + `net` (+ `partner`/`interface` when present) exactly.
3. When asked for a machine-readable summary, emit
   `{"changed_nets": [<net names from changes>], "classes": [<distinct classes>]}`.
4. Never modify either revision file; diff is read-only.
