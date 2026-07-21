"""PHOTON-X1 — fully synthetic 2025-ball demo package, built by pkgtk's own
seeded generator (pkgtk.synth.ballmap_gen). Zero external design data.

Deterministic: output depends only on GenParams (seeded, no wall clock), plus a
fixed 0.8 mm grid pitch for ball XY coordinates. Regeneration is byte-stable.
"""

from __future__ import annotations

from pkgtk.checks.common import alphabet_for, row_index
from pkgtk.synth.ballmap_gen import GeneratedDesign, GenParams, generate

# Canonical benchmark geometry (benchmarks/cases.yaml): 45 x 45 = 2025 balls.
PARAMS = GenParams(rows=45, cols=45, n_interfaces=4, depop_corner=3,
                   gnd_period=5, alphabet="full", seed=2025)
PITCH_MM = 0.8
DESIGN_NAME = "PHOTON-X1"


def build() -> GeneratedDesign:
    """Generate PHOTON-X1 rev A: canonical synthetic design + XY coordinates."""
    design = generate(PARAMS)
    g = design.graph
    g.design = DESIGN_NAME
    g.rev = "A"
    g.units = "mm"
    alphabet = alphabet_for(PARAMS.alphabet)
    for n in g.nodes:
        if n.kind == "ball" and n.grid is not None:
            x = round((n.grid.col - 1) * PITCH_MM, 4)
            y = round(row_index(n.grid.row, alphabet) * PITCH_MM, 4)
            n.xy = [x, y]
    return design


def story(design: GeneratedDesign) -> list[str]:
    """Human-readable generation summary lines (the beat-1 narration)."""
    g = design.graph
    balls = [n for n in g.nodes if n.kind == "ball"]
    by_role: dict[str, int] = {}
    for b in balls:
        by_role[b.role or "?"] = by_role.get(b.role or "?", 0) + 1
    nets = [n for n in g.nodes if n.kind == "substrate_net"]
    pads = [n for n in g.nodes if n.kind == "die_pad"]
    pairs = sum(1 for n in nets if (n.name or "").endswith("_P"))
    domains = sorted({n.domain for n in g.nodes if n.domain})
    return [
        f"design      : {g.design} rev {g.rev} ({PARAMS.rows}x{PARAMS.cols} grid, "
        f"seed {PARAMS.seed})",
        f"balls       : {len(balls)} total  "
        f"(signal {by_role.get('signal', 0)}, gnd {by_role.get('gnd', 0)}, "
        f"nc {by_role.get('nc', 0)})",
        f"nets        : {len(nets)} substrate nets "
        f"({pairs} diff pairs + singles + shared GND)",
        f"die pads    : {len(pads)}",
        f"interfaces  : {len(design.interfaces)} ({', '.join(design.interfaces)})",
        f"domains     : {len(domains)} "
        f"({'clean by construction — none assigned' if not domains else domains})",
        f"edges       : {len(g.edges)}",
        f"pitch       : {PITCH_MM} mm (XY derived from grid, deterministic)",
    ]
