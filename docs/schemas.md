# pkgtk Schemas (v0.1.0)

> **Generated file** — produced by `scripts/gen_schema_docs.py` from the
> frozen JSON Schemas under `schemas/`. Do not edit by hand; regenerate.

The three shared schemas are the product's land-grab: every wedge of the
toolkit consumes or emits one of them. They are frozen per version; a needed
change is a version bump, never an in-place edit.

| Schema | File | Purpose |
|--------|------|---------|
| Rule IR | `schemas/rule_ir.schema.json` | One design/manufacturing rule. |
| Connectivity Graph | `schemas/connectivity_graph.schema.json` | Tiered netlist connectivity. |
| Violation | `schemas/violation.schema.json` | One check result. |

## Rule IR

`schemas/rule_ir.schema.json` — A single design/manufacturing rule in intermediate representation. One deck is a list of these. Authored by humans or extracted (with review) from vendor rule sheets; consumed by the package-lint engine and the escape oracle.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | yes | Stable unique identifier for this rule within a deck (e.g. 'SUB.TRACE.WIDTH.MIN.M1'). |
| `source` | source | yes | Provenance anchor: where in the originating document this rule came from. |
| `source.doc` | string | yes | Document name or identifier the rule was taken from. |
| `source.revision` | string | no | Document revision/version string. |
| `source.page` | integer \| string | no | Page number or label within the document. |
| `source.table` | integer \| string | no | Table identifier within the document. |
| `source.row` | integer \| string | no | Row identifier within the referenced table. |
| `scope` | scope | no | Optional narrowing of where the rule applies (layer class, net class, region, component class). Absent fields mean 'applies everywhere'. |
| `scope.layer_class` | string | no | Layer class the rule applies to (e.g. 'signal', 'plane', 'buildup'). |
| `scope.net_class` | string | no | Net class the rule applies to (e.g. 'high_speed', 'power'). |
| `scope.region` | string | no | Named physical region the rule is confined to. |
| `scope.component_class` | string | no | Component class the rule applies to (e.g. 'bga', 'die'). |
| `parameter` | string | yes | Controlled-vocabulary name of the quantity constrained. Known values map to implemented checks; unknown values are NOT schema errors — they surface as 'coverage: unimplemented' at run time (honest-coverage doctrine). Conventional vocabulary: trace_width_min, spacing_min, degas_to_trace_clearance_min, degas_coverage_window, copper_balance_window, annular_ring_min, ball_grid, copper_to_edge_min. |
| `value` | oneOf(scalarValue, expressionValue, piecewiseValue) | yes | The constraint value: a scalar with units, a restricted-AST expression, or a piecewise table keyed by a design-variable condition. |
| `value[oneOf0].kind` | const "scalar" | yes | Discriminator: a single numeric value with units. |
| `value[oneOf0].number` | number | yes | The numeric magnitude. |
| `value[oneOf0].units` | string | yes | Physical units of the magnitude (e.g. 'um', 'mm', 'percent'). |
| `value[oneOf1].kind` | const "expression" | yes | Discriminator: a value computed from a design variable via a restricted arithmetic expression. |
| `value[oneOf1].expr` | string | yes | Restricted-AST arithmetic expression over one design variable (e.g. 'A * 0.10'). Must parse under the whitelist parser in pkgtk.schemas.expr — never eval'd. |
| `value[oneOf1].units` | string | no | Units of the computed result. |
| `value[oneOf1].variable` | string | no | Name of the design variable the expression is evaluated over (default 'A'). |
| `value[oneOf2].kind` | const "piecewise" | yes | Discriminator: a table of (condition -> value) brackets over a design variable. |
| `value[oneOf2].variable` | string | no | Name of the design variable the bracket conditions are evaluated over (default 'A'). |
| `value[oneOf2].units` | string | no | Units shared by every bracket value. |
| `value[oneOf2].pieces` | array<object> | yes | Ordered brackets. The first whose 'when' predicate is true supplies the value. |
| `value[oneOf2].pieces.when` | string | yes | Restricted-AST comparison predicate over the design variable (e.g. '10 < A <= 14'). |
| `value[oneOf2].pieces.value` | number | yes | Value that applies when the predicate holds. |
| `tier` | string | no | Capability tier the rule belongs to (conventionally 'normal' or 'advanced', but vendor-specific tier names are allowed). Absent means the rule applies to all tiers. |
| `severity` | enum "hard" \| "preferred" \| "advisory" | yes | Enforcement weight. 'hard' gates tape-out and drives nonzero CLI exit codes; 'preferred' is a strong recommendation; 'advisory' is informational. |
| `conditions` | array<condition> | no | Zero or more predicates that must hold for the rule to apply. A structured condition is machine-evaluable; a free-text condition cannot be evaluated and therefore forces executability to 'manual'. |
| `executability` | enum "dimensional" \| "density" \| "structural" \| "enumerated" \| "manual" | yes | How the rule is (or is not) mechanically checkable, routing it to a class of check implementation. 'manual' means no automatic check exists and a human must verify. |
| `routing` | enum "cm" \| "dfx" \| "external" \| "checklist" | yes | Which subsystem consumes the rule: 'cm' (constraint manager / connectivity), 'dfx' (design-for-x geometry), 'external' (the geometry lint engine), or 'checklist' (human checklist item). |
| `lifecycle` | lifecycle | no | Revision lifecycle: when the rule became effective and whether it is deprecated. |
| `lifecycle.effective_rev` | string | no | Document revision at which this rule became effective. |
| `lifecycle.deprecated` | boolean | no | Whether the rule is deprecated and should no longer gate new designs. |
| `lifecycle.deprecated_rev` | string | no | Revision at which the rule was deprecated, if applicable. |

### Worked example

```json
{
  "id": "SUB.TRACE.WIDTH.MIN.M1",
  "source": {
    "doc": "generic-substrate-v0",
    "revision": "0.1",
    "page": 12,
    "table": "4-2",
    "row": 3
  },
  "scope": {
    "layer_class": "signal",
    "region": "core"
  },
  "parameter": "trace_width_min",
  "value": {
    "kind": "piecewise",
    "variable": "A",
    "units": "um",
    "pieces": [
      { "when": "A <= 10", "value": 15.0 },
      { "when": "10 < A <= 14", "value": 20.0 },
      { "when": "A > 14", "value": 25.0 }
    ]
  },
  "tier": "advanced",
  "severity": "hard",
  "conditions": [
    { "param": "layer_count", "op": "ge", "value": 4 }
  ],
  "executability": "dimensional",
  "routing": "external",
  "lifecycle": {
    "effective_rev": "0.1",
    "deprecated": false
  }
}
```

## Connectivity Graph

`schemas/connectivity_graph.schema.json` — Tiered netlist-stage connectivity of a package: die pads, bumps, substrate nets, balls, and board pins, plus the typed edges connecting adjacent tiers. Produced by the ingestion parsers (AIF, Excel/CSV) and consumed by the verifier checks and ECO diff.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `design` | string | yes | Design name this graph represents. |
| `rev` | string | yes | Revision identifier of the design snapshot. |
| `source_files` | array<string> | no | Provenance: the input files this graph was ingested from. |
| `units` | string | no | Length units for all node xy coordinates in this graph. |
| `nodes` | array<node> | yes | All connectivity nodes across every tier. Node ids must be unique within the graph. |
| `nodes.id` | string | yes | Graph-unique identifier for the node. |
| `nodes.kind` | enum "die_pad" \| "bump" \| "substrate_net" \| "ball" \| "board_pin" | yes | Which connectivity tier the node lives on. |
| `nodes.name` | string | no | Human-facing name (e.g. net name, pad name, ball designator). |
| `nodes.xy` | array<number> | no | Physical position [x, y] in graph units. Optional (logical nets may have none). |
| `nodes.grid` | object | no | Grid coordinate for balls: row designator plus column index. |
| `nodes.grid.row` | string | yes | Row designator (e.g. 'A', 'AB'); alphabet may skip JEDEC letters I,O,Q,S,X,Z per the ingestion mapping. |
| `nodes.grid.col` | integer | yes | 1-based column index. |
| `nodes.diff_partner` | string | no | Node id (or net name) of this node's differential partner, if any. |
| `nodes.match_group` | string | no | Length/timing match-group identifier this node belongs to. |
| `nodes.domain` | string | no | Power domain this node belongs to (e.g. 'VDD_CORE'). |
| `nodes.interface` | string | no | Named interface region (e.g. 'UCIE_M0', 'HBM_CH2'). |
| `nodes.role` | enum "signal" \| "gnd" \| "pwr" \| "nc" | no | Electrical role of the node. 'nc' = no-connect. Only gnd/pwr nets may legitimately fan out to many balls. |
| `edges` | array<edge> | yes | Typed connections between nodes on adjacent tiers. |
| `edges.source` | string | yes | Node id of the edge's source (higher tier, e.g. die_pad). |
| `edges.target` | string | yes | Node id of the edge's target (adjacent lower tier, e.g. bump). |
| `edges.kind` | string | no | Optional edge type; conventionally the tier pair it bridges (e.g. 'die_pad__bump', 'bump__substrate_net', 'substrate_net__ball', 'ball__board_pin'). |

### Worked example

```json
{
  "design": "example_pkg",
  "rev": "A",
  "source_files": ["minimal.aif", "sheetA.xlsx"],
  "units": "um",
  "nodes": [
    { "id": "dp_TX_P", "kind": "die_pad", "name": "TX_P", "xy": [0.0, 0.0], "diff_partner": "dp_TX_N", "interface": "UCIE_M0", "role": "signal" },
    { "id": "dp_TX_N", "kind": "die_pad", "name": "TX_N", "xy": [50.0, 0.0], "diff_partner": "dp_TX_P", "interface": "UCIE_M0", "role": "signal" },
    { "id": "net_TX_P", "kind": "substrate_net", "name": "TX_P", "domain": "VDD_IO", "interface": "UCIE_M0", "role": "signal" },
    { "id": "net_TX_N", "kind": "substrate_net", "name": "TX_N", "domain": "VDD_IO", "interface": "UCIE_M0", "role": "signal" },
    { "id": "ball_A1", "kind": "ball", "name": "TX_P", "grid": { "row": "A", "col": 1 }, "xy": [0.0, 0.0], "diff_partner": "ball_A2", "role": "signal" },
    { "id": "ball_A2", "kind": "ball", "name": "TX_N", "grid": { "row": "A", "col": 2 }, "xy": [800.0, 0.0], "diff_partner": "ball_A1", "role": "signal" },
    { "id": "ball_B1", "kind": "ball", "name": "GND", "grid": { "row": "B", "col": 1 }, "xy": [0.0, 800.0], "role": "gnd" }
  ],
  "edges": [
    { "source": "dp_TX_P", "target": "net_TX_P", "kind": "die_pad__substrate_net" },
    { "source": "dp_TX_N", "target": "net_TX_N", "kind": "die_pad__substrate_net" },
    { "source": "net_TX_P", "target": "ball_A1", "kind": "substrate_net__ball" },
    { "source": "net_TX_N", "target": "ball_A2", "kind": "substrate_net__ball" }
  ]
}
```

## Violation

`schemas/violation.schema.json` — One check result: a single detected violation of a rule, with enough measured/required/location detail to reproduce and click-to-zoom. Emitted by every verifier and lint check; the universal output currency of the toolkit.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `rule_id` | string | yes | Identifier of the rule (or check) that was violated. For connectivity checks with no deck rule, the check name (e.g. 'bijection.multi_assignment'). |
| `severity` | enum "hard" \| "preferred" \| "advisory" | yes | Severity inherited from the rule. 'hard' violations drive nonzero CLI exit codes. |
| `location` | oneOf(physicalLocation, logicalLocation) | yes | Where the violation is, physically (layer + coordinates) or logically (node/net). |
| `location[oneOf0].kind` | const "physical" | yes | Discriminator: a geometric location. |
| `location[oneOf0].layer` | string | no | Layer name the violation is on. |
| `location[oneOf0].x` | number | yes | X coordinate (in the emitting tool's output units, conventionally um). |
| `location[oneOf0].y` | number | yes | Y coordinate. |
| `location[oneOf0].extent` | object | no | Optional bounding box of the violating geometry, anchored at (x, y). |
| `location[oneOf0].extent.w` | number | no | Width of the bounding box. |
| `location[oneOf0].extent.h` | number | no | Height of the bounding box. |
| `location[oneOf1].kind` | const "logical" | yes | Discriminator: a connectivity location. |
| `location[oneOf1].node_id` | string | no | Connectivity-graph node id involved. |
| `location[oneOf1].net` | string | no | Net name involved. |
| `measured` | measurement | no | The value actually observed (e.g. measured trace width). Omitted for non-metric violations such as a role swap. |
| `measured[oneOf0].value` | number | yes | Numeric magnitude. |
| `measured[oneOf0].units` | string | no | Units of the magnitude. |
| `required` | measurement | no | The value the rule requires (the threshold). Omitted for non-metric violations. |
| `delta` | number | no | Signed shortfall/excess (measured - required) in the measurement units, when both are numeric. |
| `citation` | citation | no | Anchor back to the rule's source document, so a reviewer can find the governing text. |
| `citation.doc` | string | no | Source document name. |
| `citation.revision` | string | no | Source document revision. |
| `citation.page` | integer \| string | no | Page anchor. |
| `citation.table` | integer \| string | no | Table anchor. |
| `citation.row` | integer \| string | no | Row anchor. |
| `citation.sheet` | string | no | Spreadsheet sheet name, for rule-sheet-derived rules. |
| `citation.cell` | string | no | Spreadsheet cell reference (e.g. 'C14'). |
| `citation.note` | string | no | Free-text note or footnote reference. |
| `fix_hint` | string | no | Optional free-text remediation suggestion. Advisory only; never auto-applied. |
| `check_version` | string | yes | Semantic version of the check implementation that produced this violation, for reproducibility. |

### Worked example

```json
{
  "rule_id": "SUB.TRACE.WIDTH.MIN.M1",
  "severity": "hard",
  "location": {
    "kind": "physical",
    "layer": "M1",
    "x": 1234.5,
    "y": 678.9,
    "extent": { "w": 12.0, "h": 3.0 }
  },
  "measured": { "value": 12.0, "units": "um" },
  "required": { "value": 20.0, "units": "um" },
  "delta": -8.0,
  "citation": {
    "doc": "generic-substrate-v0",
    "revision": "0.1",
    "table": "4-2",
    "row": 3
  },
  "fix_hint": "Widen the trace to at least 20 um in the core region for >=4 layer builds.",
  "check_version": "0.1.0"
}
```

## Expression grammar (Rule IR values)

Expression and piecewise-predicate strings are validated by the restricted
AST in `src/pkgtk/schemas/expr.py`: numeric literals, one or more allowed
design variables (default `A`), the operators `+ - * /`, unary minus, and
chained comparisons (`< <= > >= == !=`). Everything else — calls, attribute
access, `__import__`, comprehensions, `**`, `%`, boolean logic — is rejected.
`eval` is never used. Examples: `A * 0.10`, `10 < A <= 14`.

## Fields missing descriptions (TODO)

_None — every field carries a description._
