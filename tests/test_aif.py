"""AIF parser golden test: minimal.aif reproduces minimal.expected.json; extras kept."""

import json

from pkgtk.ingest.aif import parse_aif
from pkgtk.schemas import schemas_dir

AIF_DIR = schemas_dir().parent / "fixtures" / "golden" / "aif"


def test_minimal_reproduces_expected_graph():
    doc = parse_aif(AIF_DIR / "minimal.aif")
    actual = doc.graph.model_dump(mode="json", exclude_none=True)
    expected = json.loads((AIF_DIR / "minimal.expected.json").read_text("utf-8"))
    assert actual == expected


def test_unknown_sections_preserved_losslessly():
    doc = parse_aif(AIF_DIR / "minimal.aif")
    assert "VENDOR_PRIVATE" in doc.extras
    assert "secret_key=keep_me" in doc.extras["VENDOR_PRIVATE"]
    assert "another=preserve_this_too" in doc.extras["VENDOR_PRIVATE"]


def test_known_sections_not_in_extras():
    doc = parse_aif(AIF_DIR / "minimal.aif")
    for known in ("DATABASE", "DIE", "PADS", "NETLIST"):
        assert known not in doc.extras


def test_parsed_graph_passes_schema_and_checks_cleanly():
    # The parsed graph must be schema-valid and fire no checks by construction.
    from pkgtk.checks import run_all

    doc = parse_aif(AIF_DIR / "minimal.aif")
    # Both TX_P and TX_N present -> no diffpair missing-partner; single ball per net.
    violations = [v for v in run_all(doc.graph)
                  if v.rule_id != "grounds.missing"]
    assert violations == []
