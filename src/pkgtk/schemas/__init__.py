"""Pydantic mirrors of the frozen JSON Schemas, plus the safe expression validator.

The JSON Schema files under ``schemas/`` are the source of truth; these models
mirror them and round-trip the golden examples byte-for-byte (semantically).
"""

from pkgtk.schemas.expr import ExprError, evaluate, validate_expr
from pkgtk.schemas.graph import ConnectivityGraph, Edge, Grid, Node
from pkgtk.schemas.loader import (
    load_json,
    load_schema,
    schemas_dir,
    validate_instance,
)
from pkgtk.schemas.rule_ir import RuleIR
from pkgtk.schemas.violation import Violation

# Maps schema base name -> (pydantic model, golden example filename).
MODELS = {
    "rule_ir": (RuleIR, "rule_ir.example.json"),
    "connectivity_graph": (ConnectivityGraph, "connectivity_graph.example.json"),
    "violation": (Violation, "violation.example.json"),
}

__all__ = [
    "ExprError",
    "evaluate",
    "validate_expr",
    "RuleIR",
    "ConnectivityGraph",
    "Node",
    "Edge",
    "Grid",
    "Violation",
    "MODELS",
    "load_json",
    "load_schema",
    "schemas_dir",
    "validate_instance",
]
