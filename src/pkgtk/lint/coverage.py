"""Coverage reporter: which deck rules map to implemented geometry checks.

The honest-coverage doctrine, mechanized: every rule is classified as
``implemented`` (an engine check exists), ``manual`` (executability=manual, a human
must verify), or ``unimplemented`` (a real geometry rule with no check yet). Unknown
parameters are loud ``unimplemented`` entries, never silent passes.
"""

from __future__ import annotations

from pkgtk.lint.deck import Deck

# Parameters the geometry engine actually implements (imported would be ideal, but
# kept here to avoid importing klayout at coverage time). Keep in sync with
# pkgtk.lint.engine.IMPLEMENTED.
IMPLEMENTED_PARAMETERS = {
    "trace_width_min",
    "spacing_min",
    "degas_to_trace_clearance_min",
    "copper_to_edge_min",
}


def classify(deck: Deck) -> dict:
    rows = []
    for rule in deck.rules:
        if rule.executability == "manual":
            status = "manual"
        elif rule.parameter in IMPLEMENTED_PARAMETERS:
            status = "implemented"
        else:
            status = "unimplemented"
        rows.append({
            "id": rule.id,
            "parameter": rule.parameter,
            "executability": rule.executability,
            "status": status,
        })
    counts = {"implemented": 0, "unimplemented": 0, "manual": 0}
    for r in rows:
        counts[r["status"]] += 1
    return {
        "deck": deck.meta.get("name", deck.path.stem),
        "total": len(rows),
        "counts": counts,
        "rules": rows,
    }


def render_table(report: dict) -> str:
    from rich.console import Console
    from rich.table import Table

    table = Table(title=f"Coverage - {report['deck']}")
    table.add_column("Rule id")
    table.add_column("Parameter")
    table.add_column("Executability")
    table.add_column("Status")
    for r in report["rules"]:
        table.add_row(r["id"], r["parameter"], r["executability"], r["status"])
    console = Console(record=True, width=100)
    console.print(table)
    c = report["counts"]
    console.print(f"implemented={c['implemented']} "
                  f"unimplemented={c['unimplemented']} manual={c['manual']}")
    return console.export_text()
