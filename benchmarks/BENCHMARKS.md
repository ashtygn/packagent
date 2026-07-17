# BENCHMARKS (all phases)

> **Generated** by `python -m benchmarks.rollup`. Do not edit.

## Phase 1 - ball-map verifier
- Synthetic design: **2025 balls**; clean-design violations: **0** (false-positive gate).
- Seeded-defect catch rate: **20/20**.

## Phase 2 - package-lint geometry
- Clean substrate violations: **0**; dirty defects caught: **4/4** (copper_to_edge_min, degas_to_trace_clearance_min, spacing_min, trace_width_min).

## Phase 3 - model gates (Touchstone)
| Fixture | Decision |
|---------|----------|
| good.s2p | pass |
| nonpassive.s2p | reject |
| port_mismatch.s2p | reject |

## Phase 5 - PDN physics invariant
- Low-frequency |Z| at 1 MHz: **2995.3 ohm** vs golden **2996.0 ohm** (rel err 0.0202%, tol 2%).
