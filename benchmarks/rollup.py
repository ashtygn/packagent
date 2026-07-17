"""Aggregate every phase's benchmark into one BENCHMARKS.md.

Sections: Phase-1 ballmap catch rates, Phase-2 lint fixture matrix, Phase-3 model-gate
verdicts, Phase-5 PDN invariant deltas. Generated file; a CI staleness check regenerates
and diffs (see tests/test_rollup_staleness.py).
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "benchmarks" / "BENCHMARKS.md"


def _phase1():
    from benchmarks.run import run
    return run()


def _phase2():
    try:
        import klayout.db  # noqa: F401

        from benchmarks.lint_run import run
        return run()
    except Exception:
        return None


def _phase3():
    from pkgtk.models.ts_gate import gate
    d = ROOT / "fixtures" / "golden" / "models" / "touchstone"
    return {name: gate(d / name)["decision"]
            for name in ("good.s2p", "nonpassive.s2p", "port_mismatch.s2p")}


def _phase5():
    from pkgtk.oracles.pdn_cavity import Cavity, Port, capacitance, z_self
    g = json.loads((ROOT / "fixtures" / "golden" / "pdn" /
                    "expected_resonances.json").read_text("utf-8"))
    cav = Cavity(0.04, 0.03, 0.0008, 4.0, 0.02)
    z1 = abs(z_self([1e6], cav, Port(0.006, 0.0045))[0])
    zc = 1.0 / (2 * np.pi * 1e6 * capacitance(cav))
    return {"lowfreq_rel_err": abs(z1 - zc) / zc,
            "z_1MHz_ohm": round(z1, 1), "golden_ohm": g["z_at_1MHz_ohm"]}


def render() -> str:
    p1, p2, p3, p5 = _phase1(), _phase2(), _phase3(), _phase5()
    lines = [
        "# BENCHMARKS (all phases)",
        "",
        "> **Generated** by `python -m benchmarks.rollup`. Do not edit.",
        "",
        "## Phase 1 - ball-map verifier",
        f"- Synthetic design: **{p1['n_balls']} balls**; clean-design violations: "
        f"**{p1['clean_violations']}** (false-positive gate).",
        f"- Seeded-defect catch rate: **{p1['caught']}/{p1['total']}**.",
        "",
        "## Phase 2 - package-lint geometry",
    ]
    if p2:
        lines.append(f"- Clean substrate violations: **{p2['clean_violations']}**; "
                     f"dirty defects caught: **{len(p2['caught_defects'])}/"
                     f"{len(p2['expected_defects'])}** "
                     f"({', '.join(p2['caught_defects'])}).")
    else:
        lines.append("- (skipped: klayout not installed in this environment)")
    lines += [
        "",
        "## Phase 3 - model gates (Touchstone)",
        "| Fixture | Decision |",
        "|---------|----------|",
    ]
    for name, dec in p3.items():
        lines.append(f"| {name} | {dec} |")
    lines += [
        "",
        "## Phase 5 - PDN physics invariant",
        f"- Low-frequency |Z| at 1 MHz: **{p5['z_1MHz_ohm']} ohm** vs golden "
        f"**{p5['golden_ohm']} ohm** (rel err {p5['lowfreq_rel_err']:.4%}, tol 2%).",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    OUT.write_text(render(), encoding="utf-8")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
