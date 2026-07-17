"""Render an ECO diff dict to a deterministic Markdown report.

Sections, in order: summary counts, per-interface rollup, per-change detail table.
Output is byte-stable so `expected_report.md` can be asserted exactly.
"""

from __future__ import annotations


def render_markdown(diff: dict) -> str:
    lines: list[str] = []
    lines.append(f"# ECO Diff - {diff['design']}: rev {diff['rev_a']} "
                 f"-> rev {diff['rev_b']}")
    lines.append("")

    lines.append("## Summary")
    lines.append("")
    lines.append("| Change class | Count |")
    lines.append("|--------------|-------|")
    total = 0
    for cls, count in diff["summary"].items():
        lines.append(f"| {cls} | {count} |")
        total += count
    lines.append(f"| **Total** | {total} |")
    lines.append("")

    lines.append("## Per-interface rollup")
    lines.append("")
    lines.append("| Interface | Change class | Count |")
    lines.append("|-----------|--------------|-------|")
    for ifc, classes in diff["by_interface"].items():
        for cls, count in classes.items():
            lines.append(f"| {ifc} | {cls} | {count} |")
    lines.append("")

    lines.append("## Changes")
    lines.append("")
    lines.append("| Class | Key | Interface | From | To | Detail |")
    lines.append("|-------|-----|-----------|------|-----|--------|")
    for c in diff["changes"]:
        key = c.get("net") or c.get("ball") or ""
        ifc = c.get("interface") or ""
        frm = c.get("from") or ""
        to = c.get("to") or ""
        detail = f"partner {c['partner']}" if c.get("partner") else ""
        lines.append(f"| {c['class']} | {key} | {ifc} | {frm} | {to} | {detail} |")
    lines.append("")

    return "\n".join(lines)
