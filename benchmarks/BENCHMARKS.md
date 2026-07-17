# BENCHMARKS — Phase 1 (ball-map verifier)

> **Generated file** — produced by `python benchmarks/run.py`. Do not edit.

- Synthetic design: **2025 balls**, clean-design violations: **0** (false-positive gate).
- Seeded-defect catch rate: **20/20**.

| Case | Family | Seeded rule | Caught | Exact |
|------|--------|-------------|:------:|:-----:|
| bench01 | bijection | `bijection.multi_assignment` | yes | yes |
| bench02 | duplicate | `duplicate.die_pad` | yes | yes |
| bench03 | duplicate | `duplicate.ball_grid` | yes | yes |
| bench04 | floating | `nc.collision` | yes | yes |
| bench05 | depop | `depop.not_nc` | yes | yes |
| bench06 | bijection | `bijection.multi_ball_signal` | yes | n/a |
| bench07 | grounds | `grounds.missing` | yes | n/a |
| bench08 | diffpair | `diffpair.missing_partner` | yes | n/a |
| bench09 | diffpair | `diffpair.not_adjacent` | yes | n/a |
| bench10 | matchgroup | `matchgroup.domain_split` | yes | n/a |
| bench11 | matchgroup | `matchgroup.interface_split` | yes | n/a |
| bench12 | matchgroup | `matchgroup.incomplete` | yes | n/a |
| bench13 | domain | `domain.crossing` | yes | n/a |
| bench14 | floating | `floating.die_pad` | yes | n/a |
| bench15 | floating | `floating.ball_no_net` | yes | n/a |
| bench16 | bijection | `bijection.multi_assignment` | yes | n/a |
| bench17 | bijection | `bijection.multi_ball_signal` | yes | n/a |
| bench18 | diffpair | `diffpair.missing_partner` | yes | n/a |
| bench19 | duplicate | `duplicate.ball_grid` | yes | n/a |
| bench20 | depop | `depop.not_nc` | yes | n/a |
