"""Template compliance: conforming map clean; seeded role swap caught at A3."""

import json

from pkgtk.oracles.template_check import check_template, load_template
from pkgtk.schemas import schemas_dir
from pkgtk.schemas.graph import ConnectivityGraph

TDIR = schemas_dir().parent / "fixtures" / "golden" / "templates"
TEMPLATE = load_template(TDIR / "template.yaml")


def _graph(name):
    return ConnectivityGraph.model_validate_json((TDIR / name).read_text("utf-8"))


def test_conforming_map_is_clean():
    res = check_template(_graph("conforming.json"), TEMPLATE)
    assert res.violations == []
    assert res.flagged_unknown == []


def test_role_swap_caught_at_right_position():
    res = check_template(_graph("swapped.json"), TEMPLATE)
    dumped = [v.model_dump(mode="json", exclude_none=True) for v in res.violations]
    expected = json.loads((TDIR / "swapped_expected.json").read_text("utf-8"))
    assert dumped == expected


def test_unknown_positions_flagged_not_errored():
    g = _graph("conforming.json")
    g.nodes.append(ConnectivityGraph.model_validate(
        {"design": "x", "rev": "A",
         "nodes": [{"id": "Z9", "kind": "ball", "grid": {"row": "Z", "col": 9},
                    "role": "signal"}], "edges": []}).nodes[0])
    res = check_template(g, TEMPLATE)
    assert res.violations == []          # extra position is not a violation
    assert res.flagged_unknown == ["Z9"]  # it is flagged
