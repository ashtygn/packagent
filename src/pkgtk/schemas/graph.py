"""Pydantic mirror of schemas/connectivity_graph.schema.json (v0.1.0)."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

_Strict = ConfigDict(extra="forbid")


class Grid(BaseModel):
    model_config = _Strict
    row: str
    col: int = Field(ge=1)


class Node(BaseModel):
    model_config = _Strict
    id: str
    kind: Literal["die_pad", "bump", "substrate_net", "ball", "board_pin"]
    name: str | None = None
    xy: list[float] | None = Field(default=None, min_length=2, max_length=2)
    grid: Grid | None = None
    diff_partner: str | None = None
    match_group: str | None = None
    domain: str | None = None
    interface: str | None = None
    role: Literal["signal", "gnd", "pwr", "nc"] | None = None


class Edge(BaseModel):
    model_config = _Strict
    source: str
    target: str
    kind: str | None = None


class ConnectivityGraph(BaseModel):
    """Tiered connectivity of a package: nodes across tiers + typed edges."""

    model_config = _Strict

    design: str
    rev: str
    source_files: list[str] | None = None
    units: str | None = None
    nodes: list[Node] = Field(default_factory=list)
    edges: list[Edge] = Field(default_factory=list)

    @model_validator(mode="after")
    def _unique_node_ids(self) -> "ConnectivityGraph":
        ids = [n.id for n in self.nodes]
        if len(ids) != len(set(ids)):
            dupes = sorted({i for i in ids if ids.count(i) > 1})
            raise ValueError(f"duplicate node ids: {dupes}")
        return self

    @model_validator(mode="after")
    def _edges_reference_known_nodes(self) -> "ConnectivityGraph":
        ids = {n.id for n in self.nodes}
        for e in self.edges:
            missing = [end for end in (e.source, e.target) if end not in ids]
            if missing:
                raise ValueError(f"edge references unknown node(s): {missing}")
        return self
