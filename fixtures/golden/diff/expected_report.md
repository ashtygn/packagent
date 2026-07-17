# ECO Diff - eco_demo: rev A -> rev B

## Summary

| Change class | Count |
|--------------|-------|
| added | 1 |
| ball_repurposed | 1 |
| domain_changed | 1 |
| net_moved | 1 |
| pair_broken | 1 |
| removed | 2 |
| **Total** | 7 |

## Per-interface rollup

| Interface | Change class | Count |
|-----------|--------------|-------|
| HBM_CH2 | added | 1 |
| HBM_CH2 | ball_repurposed | 1 |
| HBM_CH2 | removed | 1 |
| UCIE_M0 | domain_changed | 1 |
| UCIE_M0 | net_moved | 1 |
| UCIE_M0 | pair_broken | 1 |
| UCIE_M0 | removed | 1 |

## Changes

| Class | Key | Interface | From | To | Detail |
|-------|-----|-----------|------|-----|--------|
| added | NEW | HBM_CH2 |  |  |  |
| ball_repurposed | B1 | HBM_CH2 | SPARE | NEW |  |
| domain_changed | VDD | UCIE_M0 | VDD_IO | VDD_CORE |  |
| net_moved | VDD | UCIE_M0 | A3 | A4 |  |
| pair_broken | TX_P | UCIE_M0 |  |  | partner TX_N |
| removed | SPARE | HBM_CH2 |  |  |  |
| removed | TX_N | UCIE_M0 |  |  |  |
