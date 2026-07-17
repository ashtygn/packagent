"""KLayout ReportDatabase (.lyrdb) emitter — the click-to-zoom UI.

One category per rule id, one item per violation, each carrying the violation polygon
(in µm / DBUM) so markers are clickable in KLayout. No hand-built XML; the
ReportDatabase API writes the file natively.
"""

from __future__ import annotations

from pathlib import Path

import klayout.db as kdb
import klayout.rdb as krdb

from pkgtk.schemas.violation import Violation


def write_lyrdb(violations: list[Violation], path: str | Path,
                cell_name: str = "TOP") -> dict[str, int]:
    """Write violations to a .lyrdb; return per-category item counts."""
    rdb = krdb.ReportDatabase("pkgtk")
    cell = rdb.create_cell(cell_name)
    cats: dict[str, krdb.RdbCategory] = {}
    counts: dict[str, int] = {}

    for v in sorted(violations, key=lambda x: x.rule_id):
        if v.rule_id not in cats:
            cats[v.rule_id] = rdb.create_category(v.rule_id)
            counts[v.rule_id] = 0
        item = rdb.create_item(cell.rdb_id(), cats[v.rule_id].rdb_id())
        loc = v.location
        if getattr(loc, "kind", None) == "physical":
            x, y = loc.x, loc.y
            ext = loc.extent
            w = ext.w if ext and ext.w else 1.0
            h = ext.h if ext and ext.h else 1.0
            box = kdb.DBox(x - w / 2, y - h / 2, x + w / 2, y + h / 2)
            item.add_value(krdb.RdbItemValue(kdb.DPolygon(box)))
        item.add_value(krdb.RdbItemValue(f"severity={v.severity}"))
        if v.measured is not None:
            m = v.measured
            mv = m.value if hasattr(m, "value") else m
            item.add_value(krdb.RdbItemValue(f"measured={mv}"))
        counts[v.rule_id] += 1

    rdb.save(str(path))
    return counts


def read_lyrdb_counts(path: str | Path) -> dict[str, int]:
    """Re-parse a .lyrdb and return per-category item counts (for tests)."""
    rdb = krdb.ReportDatabase("")
    rdb.load(str(path))
    counts: dict[str, int] = {}
    for cat in rdb.each_category():
        counts[cat.name()] = sum(1 for _ in rdb.each_item_per_category(cat.rdb_id()))
    return counts
