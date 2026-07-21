"""Cavity model (pkgtk.oracles.pdn_cavity) vs SIwave siwave_ng on the SAME structure.

The structure is the 100%-synthetic plane pair built from scratch in t1_create.py:
  - planes: two 10 mm x 10 mm rectangles (VDD on TOP, GND on BOT)
  - stackup between the planes (t1): D1 200um FR4 + L3 17um (FR4 fill, no copper)
    + D2 200um FR4 + L2 17um (FR4 fill) + D3 200um FR4  ->  d = 634 um
  - dielectric: FR4_probe, Dk = 4.4, tan_delta = 0.02
  - ports (t5_syz.py): P1 = circuit port at (5mm, 5mm)  [plane center],
                       P2 = circuit port at (1mm, 1mm)  [near corner]

S -> Z conversion: this is a genuine 2-port, so the scalar Z0*(1+S11)/(1-S11)
would give Z at P1 with P2 terminated in 50 ohm. We instead use the full matrix
form  Z = Z0 * (I + S) @ inv(I - S), whose diagonal is the self-impedance with
the OTHER port OPEN -- exactly what the cavity-model Z-matrix diagonal means.

Port-position physics note: P1 at the exact plane center is a null of the
(1,0)/(0,1)/(1,1) cavity modes, so |Z11| shows no peak below the (2,0) mode
(~14.3 GHz). Peak-location comparison therefore uses |Z22| (P2 at 1,1 mm).

Deterministic: no randomness anywhere; inputs are a fixed .s2p + closed-form model.

Usage: python cavity_vs_solver.py [s2p]   (default: plane_pair_touchstone.s2p)
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np

from pkgtk.models.ts_gate import gate, parse_touchstone
from pkgtk.oracles.pdn_cavity import (
    Cavity,
    Port,
    capacitance,
    find_resonance_peaks,
    resonance_frequencies,
    z_matrix,
)

# --- the SAME structure as t1_create.py, analytically -------------------------
A = 10e-3               # plane x-size (m)      -- t1 create_rectangle 0..10mm
B = 10e-3               # plane y-size (m)
D = (200 + 17 + 200 + 17 + 200) * 1e-6  # TOP->BOT dielectric span (m) = 634 um
EPS_R = 4.4             # FR4_probe Dk          -- t1 add_dielectric_material
TAND = 0.02             # FR4_probe loss tangent
PORTS = [Port(5e-3, 5e-3), Port(1e-3, 1e-3)]   # P1, P2 -- t5_syz.py


def s_to_z(s: np.ndarray, z0: float) -> np.ndarray:
    """Touchstone S [F,N,N] -> Z [F,N,N] via Z = z0 (I+S)(I-S)^-1."""
    n = s.shape[-1]
    eye = np.eye(n)
    return np.array([z0 * ((eye + sf) @ np.linalg.inv(eye - sf)) for sf in s])


def main() -> int:
    t0 = time.perf_counter()
    here = Path(__file__).parent
    s2p = Path(sys.argv[1]) if len(sys.argv) > 1 else here / "plane_pair_touchstone.s2p"

    cav = Cavity(a=A, b=B, d=D, epsilon_r=EPS_R, tan_delta=TAND)
    print(f"structure : {A*1e3:.0f}x{B*1e3:.0f} mm plane pair, d={D*1e6:.0f} um, "
          f"Dk={EPS_R}, tan_delta={TAND}")
    print(f"static C  : {capacitance(cav)*1e12:.3f} pF  "
          f"(analytic eps0*epsr*a*b/d)")
    fres = resonance_frequencies(cav, max_m=2, max_n=2)
    shown = {k: fres[k] for k in ("1_0", "0_1", "1_1", "2_0")}
    print("analytic modes:",
          "  ".join(f"f{k.replace('_', '')}={v/1e9:.3f}GHz" for k, v in shown.items()))
    print(f"touchstone: {s2p}")
    print()

    # --- solver side ----------------------------------------------------------
    freqs, s, z0, n = parse_touchstone(s2p)
    zs = s_to_z(s, z0)                       # [F,2,2] solver Z-matrix
    # --- cavity side, exact same frequency grid ------------------------------
    zc = z_matrix(freqs, cav, PORTS)         # [F,2,2] analytic Z-matrix

    # --- table: |Z11| at ~6 sample points ------------------------------------
    idx = np.unique(np.linspace(0, len(freqs) - 1, 6).round().astype(int))
    print(f"{'freq':>12} {'|Z11| cavity':>14} {'|Z11| siwave':>14} {'delta%':>8}")
    for i in idx:
        zc11, zs11 = abs(zc[i, 0, 0]), abs(zs[i, 0, 0])
        dpc = 100.0 * (zc11 - zs11) / zs11
        print(f"{freqs[i]/1e6:>9.1f} MHz {zc11:>12.3f} ohm {zs11:>12.3f} ohm "
              f"{dpc:>+7.2f}%")

    # low-frequency agreement: all points at or below 500 MHz
    lf = freqs <= 500e6
    d = 100.0 * np.abs(np.abs(zc[lf, 0, 0]) - np.abs(zs[lf, 0, 0])) \
        / np.abs(zs[lf, 0, 0])
    print(f"\nlow-freq (<=500 MHz, {int(lf.sum())} pts) |Z11| agreement: "
          f"{100.0 - d.mean():.2f}%  (mean delta {d.mean():.2f}%, "
          f"worst {d.max():.2f}%)")

    # The systematic offset is fringing capacitance: the cavity model's
    # magnetic-wall boundary (docs/pdn-spec.md documented omission) has none.
    # Palmer's fringing formula for a square parallel plate explains it:
    #   C = C_pp * [1 + d/(pi*a) * (1 + ln(2*pi*a/d))]^2
    c_pp = capacitance(cav)
    c_solver = 1.0 / (2 * np.pi * freqs[0] * abs(zs[0, 0, 0]))
    palmer = (1.0 + D / (np.pi * A) * (1.0 + np.log(2 * np.pi * A / D))) ** 2
    c_palmer = c_pp * palmer
    print(f"why: fringing. C_pp={c_pp*1e12:.3f} pF (magnetic-wall cavity)  "
          f"C_solver={c_solver*1e12:.3f} pF (from |Z11| @ {freqs[0]/1e6:.0f} MHz)  "
          f"C_palmer={c_palmer*1e12:.3f} pF")
    print(f"     Palmer fringing-corrected residual vs solver: "
          f"{100.0*abs(c_palmer - c_solver)/c_solver:.2f}%")
    # fringing-normalized: scale cavity |Z| by C_pp/C_palmer in the capacitive
    # region (Z ~ 1/C) and re-measure the low-freq delta -- clearly labeled.
    d_corr = 100.0 * np.abs(np.abs(zc[lf, 0, 0]) / palmer
                            - np.abs(zs[lf, 0, 0])) / np.abs(zs[lf, 0, 0])
    print(f"     low-freq agreement after Palmer correction: "
          f"{100.0 - d_corr.mean():.2f}%  (mean delta {d_corr.mean():.2f}%, "
          f"worst {d_corr.max():.2f}%)")

    # --- peak-location comparison (only meaningful if sweep reaches modes) ---
    if freqs[-1] > 2e9:
        print("\npeak-location comparison on |Z22| (P2 at 1,1 mm sees the modes):")
        pk_s = find_resonance_peaks(freqs, zs[:, 1, 1])
        dense = np.linspace(freqs[0], freqs[-1], 4001)
        pk_c = find_resonance_peaks(dense, z_matrix(dense, cav, PORTS)[:, 1, 1])
        print(f"  cavity peaks : {[f'{f/1e9:.3f} GHz' for f in pk_c]}")
        print(f"  siwave peaks : {[f'{f/1e9:.3f} GHz' for f in pk_s]}")
        for fs_ in pk_s:
            if len(pk_c):
                fc_ = pk_c[np.argmin(np.abs(pk_c - fs_))]
                print(f"  siwave {fs_/1e9:.3f} GHz vs cavity {fc_/1e9:.3f} GHz "
                      f"-> delta {100.0*abs(fs_-fc_)/fc_:.2f}%")
    else:
        print("\n(sweep tops out at "
              f"{freqs[-1]/1e9:.1f} GHz -- below first excitable mode; "
              "peak comparison needs the extended sweep)")

    # --- pkgtk physics gate on the solver output -----------------------------
    print("\npkgtk ts_gate on solver touchstone:")
    g = gate(s2p)
    print(f"  decision    : {g['decision']}")
    print(f"  passivity   : sigma_max={g['passivity']['sigma_max']} "
          f"band={g['passivity']['band']} "
          f"(worst @ {g['passivity']['worst_freq_hz']/1e6:.1f} MHz)")
    print(f"  reciprocity : max |S - S^T| = {g['reciprocity']['max_asymmetry']}")
    print(f"  sanity      : {g['sanity']}")
    print(f"  violations  : {len(g['violations'])}")

    print(f"\nWALL cavity_vs_solver: {time.perf_counter() - t0:.2f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
