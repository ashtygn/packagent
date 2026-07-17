# Phase 5 — Wow Tier (10 hrs)

## Goal
Three small components that separate the toolkit from a linter collection, each one a
working miniature of a pillar's endgame: an escape-capacity feasibility oracle
(Pillar 2's solver, v0), one interface-template compliance checker (spec-defined ground
truth), and the cavity-model PDN impedance calculator with decap cascading (Pillar 4's
tier-0 — embarrassingly non-neural, genuinely fast, demoing the three-tier doctrine
with zero solver licenses and zero training runs).

## Entry Gate
- [ ] Phase 1 Connectivity Graph + checks green (escape oracle consumes the graph).
- [ ] Phase 2 deck loader green (escape oracle pulls line/space from the deck —
      the cross-pillar tie is the demo).
- [ ] Human-only fixtures below authored.

## Exit Gate
- [ ] PDN curve's modal resonance peaks match hand-computed f_mn within 1%, and the
      low-frequency asymptote matches the parallel-plate capacitance within 2%.
- [ ] Escape oracle flags the deliberately over-subscribed corner of the synthetic
      design and passes the feasible one, with utilization percentages.
- [ ] Template checker catches the seeded role-swap and passes the conforming map.

## Human-only tasks (~3 hrs)
1. **PDN hand-checks** (the physics fixture — this is the one to be proud of):
   for a chosen cavity (say a=40 mm, b=30 mm, d=0.8 mm, εr=4.0, tanδ=0.02):
   - compute f_mn = (c / (2π√εr)) · √((mπ/a)² + (nπ/b)²) for (1,0), (0,1), (1,1) by
     hand; record in `fixtures/golden/pdn/expected_resonances.json`.
   - compute C = ε₀·εr·a·b/d and the expected |Z| = 1/(2πfC) at 1 MHz.
   - one decap sanity: a single ideal 100 nF at the port must move the low-freq
     branch to the decap's series-resonance behavior — describe qualitatively +
     the SRF you expect from the chosen R/L/C.
2. **Escape fixtures**: on the Phase-1 synthetic generator, define one quadrant
   configuration you can count by hand — e.g. pitch 0.8 mm, via land 0.45 mm,
   line/space 20/20 µm, 2 routing layers → tracks-per-channel and total capacity
   computed manually; a demand you set above and below it.
3. **Template**: encode ONE interface bump-map template as YAML
   (position → role grid). Preferred: a UCIe standard-package module map from the
   spec/public papers (UCIe defines bump maps in the specification; 1.1 added
   cost-reduced maps). If spec access stalls (membership/registration friction),
   fall back to a JEDEC-style DDR byte-lane rule set or an HBM-like grid from public
   documentation, and say which you used. Seed one role-swap variant + expected
   violation.

## Research pack

**Escape-capacity oracle (v1 analytic, v2 max-flow):**
- v1: tracks between adjacent ball lands per layer:
  `n_tracks = floor((P − D_eff − s) / (w + s))` where P = pitch, D_eff = effective
  land/antipad blocking diameter, w/s = line/space **pulled from the Phase-2 deck for
  the relevant layer class**. Capacity per region edge = channels_crossing_edge ×
  n_tracks × routing_layers. Demand = signals inside the region whose escape crosses
  that edge (from the Connectivity Graph + a simple nearest-edge assignment).
  Verdict per quadrant: utilization % and feasible/infeasible.
- v2 (only if hours remain): grid-graph max-flow via networkx
  (`networkx.algorithms.flow.maximum_flow`), balls as sources, boundary as sink,
  inter-node capacities from n_tracks — this is the published network-flow escape
  formulation in miniature; cite it as the upgrade path in the module docstring.

**Cavity-model PDN (the formula — put this in docs/pdn-spec.md verbatim so nothing is
hallucinated):** rectangular plane pair a×b, dielectric thickness d, ports p,q at
(x,y) with port widths W (use small squares; sinc port-averaging optional at v0):

```
Z_pq(ω) = (jωμ₀d)/(ab) · Σ_{m=0..M} Σ_{n=0..N}
          [ χ_m χ_n · cos(k_m x_p)cos(k_n y_p) · cos(k_m x_q)cos(k_n y_q) ]
          / ( k_m² + k_n² − k² )

k_m = mπ/a,  k_n = nπ/b,
k²  = ω² μ₀ ε₀ εr · (1 − j·tanδ_eff),
χ_m = 1 if m=0 else 2   (same for χ_n)
```

- Loss: v0 uses tanδ_eff = tanδ (dielectric only); note conductor/skin loss as a
  documented omission (affects peak Q, not peak location — which is what the fixture
  checks).
- Convergence: M=N high enough that adding 10 modes changes |Z| < 0.5% up to f_max;
  make M,N adaptive with that stop rule.
- **Validation invariants (the exit-gate math)**: peaks at f_mn; |Z| → 1/(ωC) as
  ω→0 with C = ε₀εr·a·b/d.
- Decaps: 1-port shunt series-RLC at (x,y): Z_cap = R + jωL + 1/(jωC); combine with
  the plane's Z-matrix via standard multiport shunt-termination reduction (build the
  N-port Z among {observation port + decap ports}, terminate decap ports in Z_cap,
  reduce to the observation port). scipy handles the small dense linear algebra.
- Target mask: piecewise-linear Z_target(f) from YAML; report worst margin + frequency.
- Plot: matplotlib log-log |Z| with mask overlay → PNG artifact.

**Template compliance:** a template = grid of expected roles (sig/gnd/pwr/nc, plus
named lanes). Checker = align proposed map to template anchor, compare roles, emit
Violation JSON per mismatch. Pure data + comparison — the value is the encoded
template itself.

Deps allowed: numpy, scipy, networkx, matplotlib, pyyaml.

## Claude Code prompts

### Prompt 5.1 — cavity-model PDN engine
```
/goal Implement the cavity-model Z(f) engine exactly per docs/pdn-spec.md (formula, adaptive mode truncation, decap shunt reduction, target-mask compare, matplotlib artifact) with the two physics invariants as tests.
/context Phase 5. docs/pdn-spec.md contains the formula verbatim and the hand-computed expected resonances/capacitance in fixtures/golden/pdn/. Those numbers are ground truth.
/inputs docs/pdn-spec.md, fixtures/golden/pdn/expected_resonances.json
/constraints numpy/scipy only; vectorize over frequency; no formula "improvements" — implement what the spec says and list omissions (conductor loss) in the docstring.
/deliverables src/pkgtk/oracles/pdn_cavity.py, src/pkgtk/cli/pdn.py, tests/test_pdn_physics.py
/verify Resonances within 1% of golden; low-freq |Z| within 2% of 1/(ωC); decap sanity test matches the documented qualitative expectation; runtime < 1 s for M=N=30 over 1000 freq points; make ci green.
```

### Prompt 5.2 — escape-capacity oracle
```
/goal v1 analytic escape-capacity oracle per docs/escape-spec.md: per-quadrant capacity from (pitch, land, line/space-from-deck, layers), demand from the Connectivity Graph, utilization verdicts; v2 networkx max-flow only if v1 lands early.
/context Phase 5. Hand-counted capacity numbers for one configuration are in fixtures/golden/escape/ — the implementation must reproduce them exactly before anything else.
/inputs docs/escape-spec.md, fixtures/golden/escape/, src/pkgtk/schemas/graph.py, src/pkgtk/lint/deck.py
/constraints Line/space comes from the Rule-IR deck by layer class — no hardcoded numbers. Cite the network-flow escape-routing literature as upgrade path in the docstring.
/deliverables src/pkgtk/oracles/escape.py, src/pkgtk/cli/escape.py, tests/test_escape.py
/verify Golden capacity reproduced; over-subscribed fixture flagged, feasible fixture passes with utilization %; make ci green.
```

### Prompt 5.3 — template compliance
```
/goal Interface-template compliance checker: load the human-encoded template YAML, align to a proposed ball map from the Connectivity Graph, emit Violation JSON per role mismatch.
/context Phase 5. One template + one conforming map + one role-swapped map with expected violation exist in fixtures/golden/templates/.
/inputs fixtures/golden/templates/, schemas/
/constraints Alignment = declared anchor position in the template file (no auto-search in v0). Unknown positions in the proposal = flagged, not errors.
/deliverables src/pkgtk/oracles/template_check.py, src/pkgtk/cli/template.py, tests/test_template.py
/verify Seeded swap caught at the right position; conforming map clean; make ci green.
```

## Cut line (in order)
v2 max-flow, sinc port-averaging, multi-template support. Never cut the PDN physics
invariant tests — they are the demo.
