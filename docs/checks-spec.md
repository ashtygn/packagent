# checks-spec.md — Ball-map verifier semantics (Phase 1, normative)

This document is normative. The Phase-1 check engine implements exactly these
semantics; where a check is ambiguous the implementation must **stop and flag**, never
decide silently. Every check is a pure function `ConnectivityGraph -> list[Violation]`
with no I/O. Violations use the `violation.schema.json` shape; connectivity checks that
have no governing deck rule use the check name as `rule_id` (given per check below) and
`check_version = "0.1.0"`.

## Graph semantics assumed by every check

- **Nodes** carry `kind ∈ {die_pad, bump, substrate_net, ball, board_pin}`, an optional
  `name` (net/pad/ball label), optional `grid {row, col}`, and optional attributes
  `role ∈ {signal, gnd, pwr, nc}`, `domain`, `interface`, `diff_partner`, `match_group`.
- **Connectivity** is carried by `edges` (`source`/`target` node ids). Adjacency is
  undirected for check purposes: `neighbors(n)` = every node joined to `n` by an edge.
- A **net** is a `substrate_net` node. **Ball↔net assignment** = an edge between a `ball`
  node and a `substrate_net` node. **Die-pad↔net assignment** = an edge between a
  `die_pad` and a `substrate_net`.
- `role`/`domain`/`interface` for a net are taken from the `substrate_net` node.
- A location for a connectivity violation is `logical` with `node_id` and/or `net` set.
  Where a ball has an `xy`, checks may additionally set nothing physical (v0: logical
  only, to keep locations deterministic).

Determinism: every check sorts its output by `(rule_id, location.node_id or "",
location.net or "")` so runs are byte-stable.

## Checks

### 1. Bijection / multi-assignment — `bijection.multi_assignment`, `bijection.multi_ball_signal`
- **Ball over-assigned**: a `ball` node adjacent to ≥2 distinct `substrate_net` nodes.
  One violation per offending ball. `rule_id = bijection.multi_assignment`,
  location.node_id = ball id, measured = count of nets (string), required = "1".
- **Signal net over-fanned**: a `substrate_net` with `role ∉ {gnd, pwr}` adjacent to ≥2
  `ball` nodes, unless the net name is listed in the run config `multi_ball_allow`. One
  violation per offending net. `rule_id = bijection.multi_ball_signal`, location.net =
  net name, measured = ball count (string), required = "1".

### 2. Missing grounds — `grounds.missing`
- Config supplies, per `interface`, a minimum ground count (`min_gnd`) OR a ratio
  (`gnd_ratio`, applied to the interface's ball count, floor). For each interface present
  in the graph, count balls whose net role is `gnd`. If `actual < required`, emit one
  violation. location.net = interface name (logical, `net` field carries the interface),
  measured = actual (string), required = required (string).

### 3. Diff pairs — `diffpair.missing_partner`, `diffpair.not_adjacent`
- Config supplies `pair_patterns`: list of `[positive_regex, negative_template]`.
  Default: `["(.*)_P$", "\\1_N"]`. Opt-in extra: `["(.*)P$", "\\1N"]`.
- For every net whose name matches a positive regex, compute the expected partner name.
  If no net with that partner name exists → `diffpair.missing_partner`, location.net =
  positive net, required = partner name (string).
- If config `adjacency_required` is true, and both partners exist and each maps to a ball
  with a `grid`, the two balls must be **grid-adjacent** (Chebyshev distance 1 in
  (row_index, col); row_index from the configured alphabet). Otherwise
  `diffpair.not_adjacent`, location.net = positive net, measured = Chebyshev distance
  (string), required = "1".

### 4. Match groups — `matchgroup.incomplete`, `matchgroup.domain_split`, `matchgroup.interface_split`
- Group nodes by `match_group` (nets/balls carrying the attribute). Config
  `match_groups` may declare the expected member count per group; if declared and the
  actual member count differs → `matchgroup.incomplete` (measured/required = counts).
- All members must share one `interface`; if ≥2 distinct interfaces →
  `matchgroup.interface_split` (measured = sorted interfaces joined by ",").
- No member may be reassigned across `domain`s: if members span ≥2 distinct non-null
  domains → `matchgroup.domain_split` (measured = sorted domains joined by ",").
- One violation per group per failing condition. location.net = match_group name.

### 5. Domain crossing — `domain.crossing`
- For each `substrate_net`, gather the distinct non-null `domain` values of the balls it
  is adjacent to (ball nodes may carry `domain`). If a net touches balls of ≥2 domains
  and the net is not flagged `bridge` (net name in config `bridge_nets`, or node has a
  truthy attribute we encode via `domain == "bridge"`), emit `domain.crossing`.
  location.net = net name, measured = sorted domains joined by ",".

### 6. Floating / orphan — `floating.die_pad`, `floating.ball_no_net`, `nc.collision`
- `floating.die_pad`: a `die_pad` node with no path (via edges, any length) to any
  `ball` node. location.node_id = die pad id.
- `floating.ball_no_net`: a `ball` node (role ≠ `nc`) with no adjacent `substrate_net`.
  location.node_id = ball id.
- `nc.collision`: a `ball` with role `nc` that is nonetheless adjacent to a
  `substrate_net`, OR whose net role is not nc. location.node_id = ball id.

### 7. Duplicates — `duplicate.ball_grid`, `duplicate.die_pad`
- `duplicate.ball_grid`: two `ball` nodes sharing the same `(grid.row, grid.col)`. One
  violation per duplicated grid id; location.net carries the grid id string "row+col".
- `duplicate.die_pad`: two `die_pad` nodes sharing the same `name`. One per duplicated
  name; location.net = name.

### 8. Depop conformance — `depop.not_nc`
- Config supplies a depop pattern: `{kind: corner, n: N}` (each corner N×N block),
  `{kind: ring, width: W}` (outer W rings), or `{kind: list, positions: [[row,col],…]}`.
  For each grid position the pattern marks as depopulated, the ball at that position (if
  present) must have role `nc`. A populated (non-nc) ball at a depop position →
  `depop.not_nc`, location.net = grid id, measured = actual role, required = "nc".
  A missing ball at a depop position is fine (depopulated = absent is allowed).

## Grid conventions

- Row designators are letters; the alphabet is configurable. The **JEDEC preset** skips
  `I, O, Q, S, X, Z`. Multi-letter rows continue `... Y, AA, AB, ...` in the configured
  alphabet. `row_index(row)` maps a designator to a 0-based integer using the alphabet;
  used for adjacency math. Column indices are 1-based integers.
- Default alphabet (non-JEDEC) is the full A–Z then AA…; the mapping file selects which.

## ECO diff semantics (`pkgtk diff A B`)

Primary identity = **net name**; secondary = **ball grid position**. Classification of
each change (emitted in deterministic sorted order):

- `added` — net present in B, absent in A.
- `removed` — net present in A, absent in B.
- `net_moved` — same net name, its assigned ball grid position changed.
- `ball_repurposed` — same ball grid position, the net assigned to it changed.
- `pair_broken` — a diff pair intact in A is missing a partner in B.
- `match_group_broken` — a match group's membership/interface/domain invariant holds in
  A but fails in B.
- `domain_changed` — a net's `domain` differs between A and B.

**Impact rollup**: counts of each change class, plus a per-`interface` breakdown (change
counts grouped by the interface of the affected net). Report sections, in order:
summary counts, per-interface rollup, per-change detail table. Output is byte-stable
(all keys sorted).

## Config object (`verify` run config)

A single optional YAML/dict consumed by the engine:
```yaml
multi_ball_allow: []          # net names allowed to fan out despite signal role
grounds: {UCIE_M0: {min_gnd: 2}}   # per-interface ground requirement
pair_patterns: [["(.*)_P$", "\\1_N"]]
adjacency_required: false
alphabet: jedec               # or "full"
match_groups: {}              # {group: {count: N}}
bridge_nets: []
depop: {kind: corner, n: 0}   # n:0 = no depop
```
Absent config = every check runs with its documented defaults; checks needing config
(grounds, depop) simply produce nothing when their config is empty.
