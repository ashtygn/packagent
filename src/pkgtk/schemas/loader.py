"""Shared helpers for loading the frozen JSON Schemas and validating instances.

The JSON Schema files under ``schemas/`` are the source of truth; the pydantic
models in this package mirror them. These helpers locate the schema directory,
cache-load each schema, and validate a dumped model against its schema (the
parity guarantee the round-trip test asserts).
"""

import functools
import json
from pathlib import Path
from typing import Any

import jsonschema


@functools.lru_cache(maxsize=1)
def schemas_dir() -> Path:
    """Return the repo's ``schemas/`` directory.

    Resolved relative to the installed package location: src/pkgtk/schemas/ ->
    <repo>/schemas/. Works from an editable install; for a wheel install the
    schemas are packaged alongside (see MANIFEST / package-data).
    """
    here = Path(__file__).resolve()
    # src/pkgtk/schemas/loader.py -> parents[3] == repo root
    candidate = here.parents[3] / "schemas"
    if candidate.is_dir():
        return candidate
    # Fallback: schemas shipped inside the package.
    packaged = here.parent / "_schemas"
    if packaged.is_dir():
        return packaged
    raise FileNotFoundError(f"could not locate schemas/ near {here}")


@functools.cache
def load_schema(name: str) -> dict[str, Any]:
    """Load and cache a JSON Schema by base name (e.g. 'rule_ir')."""
    path = schemas_dir() / f"{name}.schema.json"
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def validate_instance(instance: Any, schema_name: str) -> None:
    """Validate a plain dict/list instance against a named JSON Schema.

    Raises ``jsonschema.ValidationError`` on failure.
    """
    validator_cls = jsonschema.validators.validator_for(load_schema(schema_name))
    validator_cls.check_schema(load_schema(schema_name))
    validator_cls(load_schema(schema_name)).validate(instance)


def load_json(path: str | Path) -> Any:
    """Load a JSON file (e.g. a golden example)."""
    with Path(path).open(encoding="utf-8") as fh:
        return json.load(fh)
