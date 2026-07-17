"""Pydantic mirrors of the frozen JSON Schemas, plus the safe expression validator.

rule_ir / graph / violation models land here once the human-authored
schemas/*.schema.json exist (they are frozen inputs — never generated).
"""

from pkgtk.schemas.expr import ExprError, evaluate, validate_expr

__all__ = ["ExprError", "evaluate", "validate_expr"]
