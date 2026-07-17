"""`pkgtk escape` — analytic escape-capacity verdict for a region."""

from __future__ import annotations

import json

from pkgtk.oracles.escape import evaluate_from_deck


def main(argv: list[str] | None = None) -> int:
    import argparse

    p = argparse.ArgumentParser(prog="pkgtk escape")
    p.add_argument("--deck", required=True)
    p.add_argument("--pitch-um", type=float, required=True)
    p.add_argument("--land-um", type=float, required=True)
    p.add_argument("--channels", type=int, required=True)
    p.add_argument("--layers", type=int, default=2)
    p.add_argument("--demand", type=int, required=True)
    p.add_argument("--layer-class", default="signal")
    p.add_argument("--json", action="store_true")
    args = p.parse_args(argv)

    r = evaluate_from_deck(args.deck, args.pitch_um, args.land_um, args.channels,
                           args.layers, args.demand, args.layer_class)
    out = {"n_tracks": r.n_tracks, "capacity": r.capacity, "demand": r.demand,
           "utilization": r.utilization, "feasible": r.feasible}
    print(json.dumps(out, indent=2) if args.json else
          f"n_tracks={r.n_tracks} capacity={r.capacity} "
          f"util={r.utilization:.0%} feasible={r.feasible}")
    return 0 if r.feasible else 1


if __name__ == "__main__":
    raise SystemExit(main())
