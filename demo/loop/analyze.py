"""SIwave touchstone -> PDN analysis verdict JSON (the agent's eyes).

Parses a solver touchstone, converts S -> Z (full matrix form, so |Znn| is the
self-impedance with other ports OPEN), finds resonance peaks, and checks a
target-impedance mask. Output is machine-readable JSON so an agent can reason
about WHAT to change in the package; this tool never decides the fix.

Mask format (repeatable): --mask F_LO_GHZ:F_HI_GHZ:ZMAX_OHM
  e.g. --mask 0.001:8.0:5.0  means "|Z| must stay <= 5 ohm from 1 MHz to 8 GHz".

Exit codes: 0 = mask passes (or no mask given), 1 = mask violated, 2 = usage.

Usage:
  python analyze.py out.s2p --port 2 --mask 0.001:8:5 --json verdict.json --png z.png
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from pkgtk.models.ts_gate import gate, parse_touchstone  # noqa: E402
from pkgtk.oracles.pdn_cavity import find_resonance_peaks  # noqa: E402


def s_to_z(s: np.ndarray, z0: float) -> np.ndarray:
    n = s.shape[-1]
    eye = np.eye(n)
    return np.array([z0 * ((eye + sf) @ np.linalg.inv(eye - sf)) for sf in s])


def parse_mask(specs: list[str]) -> list[dict]:
    out = []
    for spec in specs:
        try:
            lo, hi, zmax = (float(x) for x in spec.split(":"))
        except ValueError as e:
            raise SystemExit(
                f"bad --mask '{spec}' (want F_LO:F_HI:ZMAX in GHz/ohm): {e}"
            ) from e
        out.append({"f_lo_ghz": lo, "f_hi_ghz": hi, "z_max_ohm": zmax})
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("touchstone")
    ap.add_argument("--port", type=int, default=1, help="1-based port for |Znn|")
    ap.add_argument("--mask", action="append", default=[],
                    help="F_LO_GHZ:F_HI_GHZ:ZMAX_OHM (repeatable)")
    ap.add_argument("--json", dest="json_out", help="write verdict JSON here")
    ap.add_argument("--png", help="write |Z| plot with mask overlay")
    a = ap.parse_args()

    mask = parse_mask(a.mask)  # validate mask syntax BEFORE any heavy parsing

    ts = Path(a.touchstone)
    if not ts.is_file():
        print(f"error: touchstone not found: {ts}")
        return 2
    freqs, s, z0, nports = parse_touchstone(ts)
    if not 1 <= a.port <= nports:
        print(f"error: --port {a.port} out of range (touchstone has {nports})")
        return 2
    p = a.port - 1
    zmag = np.abs(s_to_z(s, z0)[:, p, p])

    peaks = find_resonance_peaks(freqs, zmag.astype(complex))
    peak_list = [
        {"f_ghz": round(f / 1e9, 4),
         "z_ohm": round(float(zmag[np.argmin(np.abs(freqs - f))]), 3)}
        for f in peaks
    ]

    # sweep-edge blind spot (matrix case M1): a peak parked just above f_max is
    # invisible to the peak finder — flag a rising band-edge so the agent widens
    # the sweep instead of concluding "no resonance".
    edge_rising = bool(len(zmag) >= 5 and np.all(np.diff(zmag[-5:]) > 0))

    violations = []
    for seg in mask:
        sel = (freqs >= seg["f_lo_ghz"] * 1e9) & (freqs <= seg["f_hi_ghz"] * 1e9)
        if not sel.any():
            seg.update({"pass": True, "note": "no sweep points in segment"})
            continue
        zseg, fseg = zmag[sel], freqs[sel]
        iworst = int(np.argmax(zseg))
        seg.update({
            "worst_f_ghz": round(float(fseg[iworst]) / 1e9, 4),
            "worst_z_ohm": round(float(zseg[iworst]), 3),
            "pass": bool(zseg[iworst] <= seg["z_max_ohm"]),
        })
        if not seg["pass"]:
            violations.append(seg)

    g = gate(Path(a.touchstone))
    verdict = {
        "touchstone": str(a.touchstone),
        "port": a.port,
        "n_points": int(len(freqs)),
        "f_min_ghz": round(float(freqs[0]) / 1e9, 6),
        "f_max_ghz": round(float(freqs[-1]) / 1e9, 4),
        "z_at_lowest_f_ohm": round(float(zmag[0]), 3),
        "peaks": peak_list,
        "band_edge_rising": edge_rising,
        "mask": mask,
        "mask_pass": not violations,
        "violations": violations,
        "solver_output_physics_gate": {
            "decision": g["decision"],
            "sigma_max": g["passivity"]["sigma_max"],
            "reciprocity_max_asym": g["reciprocity"]["max_asymmetry"],
        },
    }

    if a.png:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        plt.style.use("dark_background")
        fig, ax = plt.subplots(figsize=(10, 6), dpi=140)
        ax.loglog(freqs / 1e9, zmag, color="#39c5cf", lw=1.8,
                  label=f"|Z{a.port}{a.port}| (solver)")
        for seg in mask:
            color = "#2ea043" if seg.get("pass") else "#f85149"
            ax.hlines(seg["z_max_ohm"], seg["f_lo_ghz"], seg["f_hi_ghz"],
                      colors=color, lw=2.2,
                      label=f"mask {seg['z_max_ohm']}Ω "
                            f"[{seg['f_lo_ghz']}-{seg['f_hi_ghz']} GHz] "
                            f"{'PASS' if seg.get('pass') else 'FAIL'}")
        for pk in peak_list:
            ax.annotate(f"{pk['f_ghz']} GHz", xy=(pk["f_ghz"], pk["z_ohm"]),
                        xytext=(pk["f_ghz"], pk["z_ohm"] * 1.6),
                        color="#e3b341", fontsize=10, ha="center")
        ax.set_xlabel("frequency (GHz)")
        ax.set_ylabel("|Z| (Ω)")
        ax.grid(True, which="both", color="#21262d", lw=0.5)
        ax.legend(frameon=False, fontsize=9)
        ax.set_title(Path(a.touchstone).name)
        fig.tight_layout()
        fig.savefig(a.png, facecolor="#0b0e14")
        plt.close(fig)
        verdict["png"] = a.png

    text = json.dumps(verdict, indent=2)
    if a.json_out:
        Path(a.json_out).write_text(text, encoding="utf-8")
    print(text)
    return 0 if verdict["mask_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
