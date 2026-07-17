"""Escape-capacity oracle (v1 analytic). See docs/escape-spec.md.

Line/space are pulled from the Phase-2 Rule-IR deck by layer class (never hardcoded).
v2 upgrade path (not implemented): grid-graph max-flow via networkx.maximum_flow with
balls as sources, boundary as sink, inter-node capacities from n_tracks — the published
network-flow escape-routing formulation.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from pkgtk.lint.deck import Deck, load_deck


@dataclass
class LineSpace:
    line_um: float
    space_um: float


def line_space_from_deck(deck: Deck, layer_class: str = "signal") -> LineSpace:
    """Pull trace_width_min / spacing_min (scalar) for a layer class from the deck."""
    line = space = None
    for r in deck.rules:
        scope_cls = (r.scope.layer_class if r.scope else None)
        if scope_cls not in (None, layer_class):
            continue
        if r.value.kind != "scalar":
            continue
        if r.parameter == "trace_width_min" and line is None:
            line = r.value.number
        elif r.parameter == "spacing_min" and space is None:
            space = r.value.number
    if line is None or space is None:
        raise ValueError(
            f"deck missing scalar trace_width_min/spacing_min for {layer_class!r}")
    return LineSpace(line_um=line, space_um=space)


def n_tracks(pitch_um: float, land_dia_um: float, ls: LineSpace) -> int:
    numerator = pitch_um - land_dia_um - ls.space_um
    return max(0, math.floor(numerator / (ls.line_um + ls.space_um)))


@dataclass
class RegionResult:
    n_tracks: int
    capacity: int
    demand: int
    utilization: float
    feasible: bool


def evaluate_region(pitch_um, land_dia_um, ls: LineSpace, channels: int,
                    routing_layers: int, demand: int) -> RegionResult:
    nt = n_tracks(pitch_um, land_dia_um, ls)
    capacity = channels * nt * routing_layers
    util = demand / capacity if capacity else float("inf")
    return RegionResult(n_tracks=nt, capacity=capacity, demand=demand,
                        utilization=round(util, 6), feasible=demand <= capacity)


def evaluate_from_deck(deck_path, pitch_um, land_dia_um, channels, routing_layers,
                       demand, layer_class="signal") -> RegionResult:
    deck = load_deck(deck_path)
    ls = line_space_from_deck(deck, layer_class)
    return evaluate_region(pitch_um, land_dia_um, ls, channels, routing_layers, demand)
