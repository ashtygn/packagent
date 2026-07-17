# escape-spec.md — Escape-capacity oracle (Phase 5, normative)

v1 analytic capacity model. Line/space are pulled from the Phase-2 Rule-IR deck by
layer class — never hardcoded.

## Tracks between adjacent ball lands (per layer)

```
n_tracks = floor( (P − D_eff − s) / (w + s) )
```
- `P`     = ball pitch (µm)
- `D_eff` = effective land / antipad blocking diameter (µm)
- `w`, `s`= line / space (µm), pulled from the deck (`trace_width_min`,
  `spacing_min`) for the relevant layer class.

## Region capacity and verdict

```
capacity = channels_crossing_edge × n_tracks × routing_layers
utilization = demand / capacity
feasible = demand ≤ capacity
```
- `channels_crossing_edge`: number of inter-land channels the region's escape edge
  crosses (hand-counted in v0 region spec; graph-derived nearest-edge assignment is the
  documented upgrade path).
- `demand`: signal nets inside the region that must escape across that edge.

## Worked golden (fixtures/golden/escape/)

Deck line/space = 20/20 µm (escape_deck.yaml). Pitch 0.8 mm = 800 µm, via land
D_eff = 0.45 mm = 450 µm, routing_layers = 2, channels = 10:

```
n_tracks = floor((800 − 450 − 20) / (20 + 20)) = floor(330/40) = floor(8.25) = 8
capacity = 10 × 8 × 2 = 160 tracks
```
- feasible case: demand 120 → utilization 0.75 → feasible.
- infeasible case: demand 200 → utilization 1.25 → infeasible.

## Upgrade path (docstring)
v2: grid-graph max-flow (networkx `maximum_flow`), balls as sources, boundary as sink,
inter-node capacities from `n_tracks` — the published network-flow escape formulation.
Cited but not implemented in v0.
