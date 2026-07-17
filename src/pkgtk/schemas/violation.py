"""Pydantic mirror of schemas/violation.schema.json (v0.1.0)."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

_Strict = ConfigDict(extra="forbid")


class Extent(BaseModel):
    model_config = _Strict
    w: float | None = None
    h: float | None = None


class PhysicalLocation(BaseModel):
    model_config = _Strict
    kind: Literal["physical"]
    layer: str | None = None
    x: float
    y: float
    extent: Extent | None = None


class LogicalLocation(BaseModel):
    model_config = _Strict
    kind: Literal["logical"]
    node_id: str | None = None
    net: str | None = None


Location = Annotated[
    PhysicalLocation | LogicalLocation,
    Field(discriminator="kind"),
]


class MeasurementValue(BaseModel):
    model_config = _Strict
    value: float
    units: str | None = None


# A measurement is either a structured {value, units} or a bare non-numeric string.
Measurement = MeasurementValue | str


class Citation(BaseModel):
    model_config = _Strict
    doc: str | None = None
    revision: str | None = None
    page: int | str | None = None
    table: int | str | None = None
    row: int | str | None = None
    sheet: str | None = None
    cell: str | None = None
    note: str | None = None


class Violation(BaseModel):
    """One detected rule violation with measured/required/location detail."""

    model_config = _Strict

    rule_id: str
    severity: Literal["hard", "preferred", "advisory"]
    location: Location
    measured: Measurement | None = None
    required: Measurement | None = None
    delta: float | None = None
    citation: Citation | None = None
    fix_hint: str | None = None
    check_version: str
