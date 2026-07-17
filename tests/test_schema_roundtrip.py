"""Round-trip + JSON-Schema parity for every schema model.

For each of the three schemas:
  * the golden example validates against its JSON Schema (jsonschema);
  * the example loads into the pydantic model;
  * the model dumped with exclude_none is semantically identical to the input;
  * the dumped output ALSO validates against the JSON Schema (parity guarantee).
"""

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from pkgtk.schemas import MODELS, load_schema, schemas_dir, validate_instance
from pkgtk.schemas.loader import load_json

GOLDEN_DIR = schemas_dir().parent / "fixtures" / "golden" / "schema-examples"

CASES = [
    (name, model, GOLDEN_DIR / example) for name, (model, example) in MODELS.items()
]


@pytest.mark.parametrize("name,model,example_path", CASES)
def test_golden_example_exists(name, model, example_path):
    assert example_path.is_file(), f"missing golden example: {example_path}"


@pytest.mark.parametrize("name,model,example_path", CASES)
def test_example_validates_against_json_schema(name, model, example_path):
    instance = load_json(example_path)
    validate_instance(instance, name)  # raises on failure


@pytest.mark.parametrize("name,model,example_path", CASES)
def test_roundtrip_semantically_identical(name, model, example_path):
    original = load_json(example_path)
    obj = model.model_validate(original)
    dumped = obj.model_dump(mode="json", exclude_none=True)
    assert dumped == original, (
        f"{name}: round-trip differs\n"
        f"input : {json.dumps(original, sort_keys=True)}\n"
        f"output: {json.dumps(dumped, sort_keys=True)}"
    )


@pytest.mark.parametrize("name,model,example_path", CASES)
def test_dumped_model_satisfies_schema(name, model, example_path):
    original = load_json(example_path)
    obj = model.model_validate(original)
    dumped = obj.model_dump(mode="json", exclude_none=True)
    validate_instance(dumped, name)  # parity: pydantic output is schema-valid


def test_all_schemas_are_valid_json_schema():
    # Every schema file must itself be a well-formed JSON Schema.
    import jsonschema

    for name in MODELS:
        schema = load_schema(name)
        validator_cls = jsonschema.validators.validator_for(schema)
        validator_cls.check_schema(schema)


def test_schema_files_present_on_disk():
    for name in MODELS:
        assert (schemas_dir() / f"{name}.schema.json").is_file()


def test_expression_rule_uses_restricted_ast():
    # The rule_ir golden example carries a piecewise value; constructing it must
    # have exercised the restricted-AST predicate validation without error.
    from pkgtk.schemas import RuleIR

    rule = RuleIR.model_validate(load_json(GOLDEN_DIR / "rule_ir.example.json"))
    assert rule.value.kind == "piecewise"
    assert len(rule.value.pieces) == 3


def test_freetext_condition_forces_manual():
    from pkgtk.schemas import RuleIR

    base = {
        "id": "X",
        "source": {"doc": "d"},
        "parameter": "trace_width_min",
        "value": {"kind": "scalar", "number": 1.0, "units": "um"},
        "severity": "hard",
        "executability": "dimensional",
        "routing": "external",
        "conditions": [{"text": "not applicable with conductive adhesive"}],
    }
    with pytest.raises(ValidationError):
        RuleIR.model_validate(base)
    base["executability"] = "manual"
    RuleIR.model_validate(base)  # now valid


def test_bad_expression_rejected_in_model():
    from pkgtk.schemas import RuleIR

    bad = {
        "id": "X",
        "source": {"doc": "d"},
        "parameter": "p",
        "value": {"kind": "expression", "expr": "__import__('os')"},
        "severity": "hard",
        "executability": "dimensional",
        "routing": "external",
    }
    with pytest.raises(ValidationError):
        RuleIR.model_validate(bad)


def test_graph_rejects_duplicate_node_ids():
    from pkgtk.schemas import ConnectivityGraph

    with pytest.raises(ValidationError):
        ConnectivityGraph.model_validate(
            {
                "design": "d",
                "rev": "A",
                "nodes": [
                    {"id": "n1", "kind": "ball"},
                    {"id": "n1", "kind": "ball"},
                ],
                "edges": [],
            }
        )


def test_all_golden_examples_covered():
    # Guard against silently forgetting a schema.
    found = {p.name for p in Path(GOLDEN_DIR).glob("*.example.json")}
    expected = {example for _, example in MODELS.values()}
    assert found == expected
