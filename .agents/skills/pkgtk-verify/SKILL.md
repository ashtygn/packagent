---
name: pkgtk-verify
description: Verify a package ball-map connectivity graph with pkgtk - run the 8 check families, parse the JSON violation report, and act on the exit-code contract. Use for any "verify / check / find violations in graph.json" request.
---

# pkgtk-verify — ball-map verification workflow

## Command

```
pkgtk verify <graph.json> [--config <config.json>] --json
```

Exit codes: `0` clean · `1` violations found (**success-with-findings — never treat
as a crash**) · `2` usage error · `3` internal. Always use `--json`.

## JSON report shape

```json
{"design": "...", "rev": "...", "violation_count": N,
 "violations": [{"rule_id": "...", "severity": "...",
                 "location": {"net": "...", "node_id": "...", ...},
                 "message": "..."}]}
```

`location` fields are optional per rule — copy only the ones present. The eight rule
families: `bijection.*`, `duplicate.*`, `nc.*`, `depop.*`, `grounds.*`, `diffpair.*`,
`matchgroup.*` / `domain.*`, `floating.*` (semantics: docs/checks-spec.md).

## Workflow

1. Run the command; capture stdout JSON. Exit 1 ⇒ parse `violations`.
2. Report findings with exact `rule_id` + location values — never paraphrase ids.
3. When asked to write findings to a file, emit a JSON array of
   `{"rule_id": ..., "net"?: ..., "node_id"?: ...}` objects, one per violation.
4. Do not edit inputs during a verification request; repairs are a separate,
   explicitly-requested task (verify again after any repair: expect exit 0).

## Config knobs that change results

`--config` carries depopulation spec (`depop.n/kind`), `adjacency_required`,
`match_groups` requirements — a graph can be clean under one config and dirty under
another, so always verify with the config you were given, unmodified.
