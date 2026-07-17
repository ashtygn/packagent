"""Pydantic mirror of schemas/rule_ir.schema.json (Rule IR, v0.1.0).

Field names and structure mirror the JSON Schema exactly so a model dumped with
``exclude_none=True`` validates against the schema (the parity guarantee) and
round-trips the golden example. Expression and piecewise-predicate strings are
validated through the restricted AST in :mod:`pkgtk.schemas.expr` at construction
time — never eval'd.
"""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from pkgtk.schemas.expr import ExprError, validate_expr

_Strict = ConfigDict(extra="forbid")


class Source(BaseModel):
    model_config = _Strict
    doc: str
    revision: str | None = None
    page: int | str | None = None
    table: int | str | None = None
    row: int | str | None = None


class Scope(BaseModel):
    model_config = _Strict
    layer_class: str | None = None
    net_class: str | None = None
    region: str | None = None
    component_class: str | None = None


class ScalarValue(BaseModel):
    model_config = _Strict
    kind: Literal["scalar"]
    number: float
    units: str


class ExpressionValue(BaseModel):
    model_config = _Strict
    kind: Literal["expression"]
    expr: str
    units: str | None = None
    variable: str | None = None

    @model_validator(mode="after")
    def _check_expr(self) -> "ExpressionValue":
        var = self.variable or "A"
        try:
            validate_expr(self.expr, allowed_vars=(var,))
        except ExprError as exc:
            raise ValueError(f"invalid expression {self.expr!r}: {exc}") from exc
        return self


class Piece(BaseModel):
    model_config = _Strict
    when: str
    value: float


class PiecewiseValue(BaseModel):
    model_config = _Strict
    kind: Literal["piecewise"]
    variable: str | None = None
    units: str | None = None
    pieces: list[Piece] = Field(min_length=1)

    @model_validator(mode="after")
    def _check_predicates(self) -> "PiecewiseValue":
        var = self.variable or "A"
        for piece in self.pieces:
            try:
                validate_expr(piece.when, allowed_vars=(var,))
            except ExprError as exc:
                raise ValueError(
                    f"invalid piecewise predicate {piece.when!r}: {exc}"
                ) from exc
        return self


Value = Annotated[
    ScalarValue | ExpressionValue | PiecewiseValue,
    Field(discriminator="kind"),
]


class StructuredCondition(BaseModel):
    model_config = _Strict
    param: str
    op: Literal["lt", "le", "gt", "ge", "eq", "ne", "in", "not_in"]
    value: object


class FreeTextCondition(BaseModel):
    model_config = _Strict
    text: str


Condition = StructuredCondition | FreeTextCondition


class Lifecycle(BaseModel):
    model_config = _Strict
    effective_rev: str | None = None
    deprecated: bool | None = None
    deprecated_rev: str | None = None


class RuleIR(BaseModel):
    """One design/manufacturing rule in intermediate representation."""

    model_config = _Strict

    id: str
    source: Source
    scope: Scope | None = None
    parameter: str
    value: Value
    tier: str | None = None
    severity: Literal["hard", "preferred", "advisory"]
    conditions: list[Condition] | None = None
    executability: Literal[
        "dimensional", "density", "structural", "enumerated", "manual"
    ]
    routing: Literal["cm", "dfx", "external", "checklist"]
    lifecycle: Lifecycle | None = None

    @model_validator(mode="after")
    def _freetext_forces_manual(self) -> "RuleIR":
        # Invariant from the schema spec: a free-text condition cannot be
        # evaluated mechanically, so the rule must be executability=manual.
        has_freetext = any(
            isinstance(c, FreeTextCondition) for c in (self.conditions or [])
        )
        if has_freetext and self.executability != "manual":
            raise ValueError(
                "a free-text condition forces executability='manual', "
                f"got {self.executability!r}"
            )
        return self
