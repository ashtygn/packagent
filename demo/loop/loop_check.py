"""Compare BEFORE vs AFTER analysis verdicts -> improvement verdict (the referee).

Consumes two analyze.py JSON files and judges whether the design change actually
fixed the mask violation, with the numbers to prove it. This is the loop's honest
closer: an edit that "ran" but didn't improve the physics is a FAILURE here.

Exit codes: 0 = AFTER passes mask and improved, 1 = not fixed / regressed, 2 = usage.

Usage: python loop_check.py before.json after.json [--json out.json] [--png overlay.png]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))


def load(p: str) -> dict:
    return json.loads(Path(p).read_text(encoding="utf-8"))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("before_json")
    ap.add_argument("after_json")
    ap.add_argument("--json", dest="json_out")
    ap.add_argument("--png", help="overlay plot of both |Z| curves + mask")
    a = ap.parse_args()

    b, aft = load(a.before_json), load(a.after_json)

    peak_moves = []
    for pb in b.get("peaks", []):
        if not aft.get("peaks"):
            peak_moves.append({"before_ghz": pb["f_ghz"], "after_ghz": None,
                               "note": "peak gone from sweep"})
            continue
        fa = min(aft["peaks"], key=lambda pk: abs(pk["f_ghz"] - pb["f_ghz"]))
        peak_moves.append({
            "before_ghz": pb["f_ghz"], "after_ghz": fa["f_ghz"],
            "shift_pct": round(100.0 * (fa["f_ghz"] - pb["f_ghz"]) / pb["f_ghz"], 2),
            "before_z_ohm": pb["z_ohm"], "after_z_ohm": fa["z_ohm"],
        })

    verdict = {
        "before": {"touchstone": b["touchstone"], "mask_pass": b["mask_pass"],
                   "violations": b["violations"]},
        "after": {"touchstone": aft["touchstone"], "mask_pass": aft["mask_pass"],
                  "violations": aft["violations"]},
        "peak_moves": peak_moves,
        "fixed": (not b["mask_pass"]) and aft["mask_pass"],
        "regressed": b["mask_pass"] and not aft["mask_pass"],
        "solver_gates": {
            "before": b["solver_output_physics_gate"]["decision"],
            "after": aft["solver_output_physics_gate"]["decision"],
        },
    }
    if verdict["solver_gates"]["after"] != "pass":
        verdict["fixed"] = False
        verdict["note"] = "AFTER solve failed the physics gate - untrustworthy result"

    if a.png:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        from pkgtk.models.ts_gate import parse_touchstone

        def zmag(ts: str, port: int) -> tuple[np.ndarray, np.ndarray]:
            freqs, s, z0, _ = parse_touchstone(Path(ts))
            n = s.shape[-1]
            eye = np.eye(n)
            z = np.array([z0 * ((eye + sf) @ np.linalg.inv(eye - sf)) for sf in s])
            return freqs, np.abs(z[:, port - 1, port - 1])

        fb, zb = zmag(b["touchstone"], b["port"])
        fa_, za = zmag(aft["touchstone"], aft["port"])
        plt.style.use("dark_background")
        fig, ax = plt.subplots(figsize=(10, 6), dpi=140)
        ax.loglog(fb / 1e9, zb, color="#f85149", lw=1.8, alpha=0.9, label="BEFORE")
        ax.loglog(fa_ / 1e9, za, color="#2ea043", lw=1.8, label="AFTER")
        for seg in b.get("mask", []):
            ax.hlines(seg["z_max_ohm"], seg["f_lo_ghz"], seg["f_hi_ghz"],
                      colors="#e3b341", lw=2.2,
                      label=f"mask {seg['z_max_ohm']}Ω "
                            f"[{seg['f_lo_ghz']}-{seg['f_hi_ghz']} GHz]")
        ax.set_xlabel("frequency (GHz)")
        ax.set_ylabel("|Z| (Ω)")
        ax.grid(True, which="both", color="#21262d", lw=0.5)
        ax.legend(frameon=False, fontsize=9)
        ax.set_title("PDN fix: before vs after")
        fig.tight_layout()
        fig.savefig(a.png, facecolor="#0b0e14")
        plt.close(fig)
        verdict["png"] = a.png

    text = json.dumps(verdict, indent=2)
    if a.json_out:
        Path(a.json_out).write_text(text, encoding="utf-8")
    print(text)
    return 0 if verdict["fixed"] and not verdict["regressed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
