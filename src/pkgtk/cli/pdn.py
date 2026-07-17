"""`pkgtk pdn` — compute cavity-model |Z|(f), check invariants, emit a PNG artifact."""

from __future__ import annotations

import json

import numpy as np

from pkgtk.oracles.pdn_cavity import (
    Cavity,
    Port,
    capacitance,
    plot_impedance,
    resonance_frequencies,
    z_self,
)


def main(argv: list[str] | None = None) -> int:
    import argparse

    p = argparse.ArgumentParser(prog="pkgtk pdn")
    p.add_argument("--a", type=float, default=0.040)
    p.add_argument("--b", type=float, default=0.030)
    p.add_argument("--d", type=float, default=0.0008)
    p.add_argument("--epsr", type=float, default=4.0)
    p.add_argument("--tand", type=float, default=0.02)
    p.add_argument("--fmax", type=float, default=4e9)
    p.add_argument("--png", default=None)
    p.add_argument("--json", action="store_true")
    args = p.parse_args(argv)

    cav = Cavity(args.a, args.b, args.d, args.epsr, args.tand)
    port = Port(args.a * 0.15, args.b * 0.15)
    freqs = np.linspace(1e6, args.fmax, 2000)
    z = z_self(freqs, cav, port, 30, 30)
    out = {
        "capacitance_F": capacitance(cav),
        "resonances_hz": resonance_frequencies(cav),
        "z_at_1MHz_ohm": float(abs(z_self([1e6], cav, port)[0])),
    }
    if args.png:
        plot_impedance(freqs, z, args.png)
        out["png"] = args.png
    print(json.dumps(out, indent=2) if args.json else
          f"C={out['capacitance_F']:.3e} F, |Z|(1MHz)={out['z_at_1MHz_ohm']:.1f} ohm")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
