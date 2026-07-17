# Phase notes — interpretation decisions & flagged gaps

This is the honesty ledger for the autonomous overnight build. The project rule is
**flagged gap = fine, silent wrong = fatal**. Every place where the agent acted as the
delegated human oracle (authoring schemas, spec docs, or golden fixtures that the plan
reserves for the human) is recorded here so the human can review and, where needed,
override. Nothing here was decided silently.

## Standing context
- The user explicitly delegated oracle authority for this run ("no permissions needed
  from me… agent running all night… go through every readme and complete the sub-goals").
- Where a phase reserves work as "human-only" (schemas, `*-spec.md`, hand-authored golden
  fixtures), the agent authored a best-effort version from the detailed field/semantics
  specs in each `PhaseN.md`, and recorded the interpretation choices below.
- `GOLDEN_EDIT=1` was used to commit initial `fixtures/golden/**` content, since that is
  the human-oracle escape hatch and the directory started empty.
- **Push to GitHub is currently blocked**: the cached credential authenticates as
  `ashwanth-lightmatter`, which lacks write access to `ashtygn/packagent` (HTTP 403).
  All work is committed locally; a `gh auth login` as `ashtygn` (or a PAT) will let the
  accumulated commits push. Nothing is lost.

## Phase 0 — Foundation
Schemas authored (frozen v0.1.0): `rule_ir`, `connectivity_graph`, `violation`.
Decisions:
- **Rule IR `value`** modeled as a discriminated union on `kind` (`scalar` /
  `expression` / `piecewise`) rather than an untagged oneOf, for clean pydantic mapping.
- **`parameter`** is an open string (not a closed enum): unknown parameters must surface
  as `coverage: unimplemented` at run time per the honest-coverage doctrine, not be
  rejected at schema level.
- **`severity`/`executability`/`routing`** are closed enums (they map to behavior);
  **`tier`** is an open string (vendor tier names vary).
- **Free-text condition ⇒ `executability: manual`** is enforced as a pydantic
  model-validator invariant (JSON Schema if/then left out for readability; documented).
- **`connectivity_graph` node roles** standardized to `signal/gnd/pwr/nc`. Phase 5's
  template uses `sig`; the template checker will map `sig → signal`.
- **`violation.measured/required`** accept either `{value, units}` or a bare string
  (for non-numeric results like a role swap).
- Round-trip is asserted **semantically** (parsed-JSON equality of `model_dump(
  exclude_none=True)` vs input), not byte-identical, since JSON key order/whitespace are
  not meaningful. Model defaults are left as `None` (not the schema's documented
  defaults) so round-trip fidelity holds.
