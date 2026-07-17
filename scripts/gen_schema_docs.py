"""Generate docs/schemas.md from the frozen JSON Schemas.

Walks every schema, emits one section per schema with a field table (path,
type, required, description) pulled from the schema `description` keys, appends
the golden worked example, and lists any description-less field as a TODO at the
bottom. Documentation generator only — never edits the schemas.

Usage: python scripts/gen_schema_docs.py
"""

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCHEMA_DIR = REPO / "schemas"
EXAMPLE_DIR = REPO / "fixtures" / "golden" / "schema-examples"
OUT = REPO / "docs" / "schemas.md"

SCHEMAS = [
    ("Rule IR", "rule_ir", "rule_ir.example.json"),
    ("Connectivity Graph", "connectivity_graph", "connectivity_graph.example.json"),
    ("Violation", "violation", "violation.example.json"),
]

_missing: list[str] = []


def resolve(schema: dict, node: dict) -> dict:
    """Follow a single $ref one hop (all refs here are local #/$defs/*)."""
    ref = node.get("$ref")
    if not ref:
        return node
    parts = ref.lstrip("#/").split("/")
    target = schema
    for p in parts:
        target = target[p]
    return target


def type_str(node: dict) -> str:
    if "$ref" in node:
        return node["$ref"].split("/")[-1]
    if "const" in node:
        return f'const "{node["const"]}"'
    if "enum" in node:
        return "enum " + " | ".join(json.dumps(e) for e in node["enum"])
    if "oneOf" in node:
        return "oneOf(" + ", ".join(type_str(s) for s in node["oneOf"]) + ")"
    t = node.get("type")
    if isinstance(t, list):
        return " | ".join(t)
    if t == "array":
        items = node.get("items", {})
        return f"array<{type_str(items)}>"
    return t or "any"


def walk(schema: dict, node: dict, prefix: str, required: set, rows: list, seen: set):
    node = resolve(schema, node)
    props = node.get("properties", {})
    req = set(node.get("required", []))
    for name, sub in props.items():
        path = f"{prefix}.{name}" if prefix else name
        sub_resolved = resolve(schema, sub)
        desc = sub.get("description") or sub_resolved.get("description") or ""
        is_req = name in req
        rows.append((path, type_str(sub), "yes" if is_req else "no", desc))
        if not desc:
            _missing.append(path)
        # Recurse into nested objects / arrays-of-objects, avoiding ref cycles.
        ref_key = sub.get("$ref") or sub_resolved.get("$ref")
        if ref_key and ref_key in seen:
            continue
        if ref_key:
            seen = seen | {ref_key}
        target = sub_resolved
        if target.get("type") == "array":
            target = resolve(schema, target.get("items", {}))
        if target.get("type") == "object" and target.get("properties"):
            walk(schema, target, path, required, rows, seen)
        for combiner in ("oneOf", "anyOf"):
            for i, variant in enumerate(sub_resolved.get(combiner, [])):
                v = resolve(schema, variant)
                if v.get("properties"):
                    walk(schema, v, f"{path}[{combiner}{i}]", required, rows, seen)


def md_escape(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ")


def main() -> int:
    lines = [
        "# pkgtk Schemas (v0.1.0)",
        "",
        "> **Generated file** — produced by `scripts/gen_schema_docs.py` from the",
        "> frozen JSON Schemas under `schemas/`. Do not edit by hand; regenerate.",
        "",
        "The three shared schemas are the product's land-grab: every wedge of the",
        "toolkit consumes or emits one of them. They are frozen per version; a needed",
        "change is a version bump, never an in-place edit.",
        "",
        "| Schema | File | Purpose |",
        "|--------|------|---------|",
        "| Rule IR | `schemas/rule_ir.schema.json` | One design/manufacturing rule. |",
        "| Connectivity Graph | `schemas/connectivity_graph.schema.json` | Tiered "
        "netlist connectivity. |",
        "| Violation | `schemas/violation.schema.json` | One check result. |",
        "",
    ]
    for title, base, example in SCHEMAS:
        schema = json.loads((SCHEMA_DIR / f"{base}.schema.json").read_text("utf-8"))
        lines.append(f"## {title}")
        lines.append("")
        lines.append(f"`schemas/{base}.schema.json` — {schema.get('description','')}")
        lines.append("")
        rows: list = []
        walk(schema, schema, "", set(schema.get("required", [])), rows, set())
        lines.append("| Field | Type | Required | Description |")
        lines.append("|-------|------|----------|-------------|")
        for path, typ, req, desc in rows:
            lines.append(
                f"| `{path}` | {md_escape(typ)} | {req} | {md_escape(desc)} |"
            )
        lines.append("")
        lines.append("### Worked example")
        lines.append("")
        lines.append("```json")
        lines.append((EXAMPLE_DIR / example).read_text("utf-8").rstrip())
        lines.append("```")
        lines.append("")

    lines.append("## Expression grammar (Rule IR values)")
    lines.append("")
    lines.append(
        "Expression and piecewise-predicate strings are validated by the restricted"
    )
    lines.append(
        "AST in `src/pkgtk/schemas/expr.py`: numeric literals, one or more allowed"
    )
    lines.append(
        "design variables (default `A`), the operators `+ - * /`, unary minus, and"
    )
    lines.append(
        "chained comparisons (`< <= > >= == !=`). Everything else — calls, attribute"
    )
    lines.append(
        "access, `__import__`, comprehensions, `**`, `%`, boolean logic — is rejected."
    )
    lines.append("`eval` is never used. Examples: `A * 0.10`, `10 < A <= 14`.")
    lines.append("")

    lines.append("## Fields missing descriptions (TODO)")
    lines.append("")
    if _missing:
        for path in _missing:
            lines.append(f"- [ ] `{path}`")
    else:
        lines.append("_None — every field carries a description._")
    lines.append("")

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {OUT} ({len(rows)} rows in last schema; {len(_missing)} TODO)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
