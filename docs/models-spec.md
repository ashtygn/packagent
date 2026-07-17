# models-spec.md — SI/PI model-intake semantics (Phase 3, normative)

Defines how model files are graded. Read-only intake gate; never auto-"fix" a file.

## Touchstone quality (IEEE-370-style)

**Parser.** v0 uses a self-contained numpy Touchstone reader (comment lines `!`, one
option line `#  <freq-unit> S <format> R <z0>`, then `freq` + N² (real,imag) pairs per
row for an N-port). This avoids a heavy scikit-rf dependency so the gate runs in core
CI; scikit-rf may be swapped in later behind the same interface. Formats supported: RI
(real/imag), MA (mag/angle-deg), DB (dB/angle-deg). Reference: Touchstone 1.1 spec;
IEEE Std 370-2020 for the quality metrics below.

**Sanity battery (deterministic, pre-metric).** Fail fast, cite the reason:
- *port_count*: the number of (real,imag) pairs per data row must equal N² where N is
  the declared/expected port count (from the file extension `.sNp` -> N). Mismatch =
  `reject`, reason `port_count_mismatch`.
- *frequency_monotonic*: frequency vector strictly increasing, non-negative.
- *finite*: no NaN/Inf in any S entry.
- *low_freq_present*: flag (not fail) if the lowest frequency > 1 MHz (DC behavior
  unobservable).

**Metrics (numpy, per IEEE-370 bands).**
- *passivity*: for each frequency, `σ_max(S(f))` = largest singular value of the S
  matrix. Passive iff `σ_max ≤ 1` at every frequency. Report the worst (max over freq)
  σ_max and the frequency at which it occurs.
- *reciprocity*: `max_{i<j,f} |S_ij(f) − S_ji(f)|`. Reciprocal networks → ~0.
- *causality*: full IEEE-370 causality (clockwise rotation / KK) is **not** implemented
  in v0; a flagged heuristic placeholder is emitted with `causality: unassessed`. This
  is the human-decided fallback (see Phase-3 research pack).

**Verdict banding (passivity σ_max):**
| σ_max              | band          | decision        |
|--------------------|---------------|-----------------|
| ≤ 1.001            | good          | pass            |
| 1.001 – 1.05       | acceptable    | pass-with-flags |
| > 1.05             | poor          | reject          |

The 1.001 tolerance absorbs numerical noise; > 1.05 (our known-bad scaling of 1.05)
is an unambiguous non-passive reject. Output conforms to the Violation/Result schema:
a passing file yields zero violations; a failing file yields one violation per failed
gate with `measured`/`required` and a citation to the metric.

## IBIS intake (ibischk wrapper)

The IBIS "golden parser" ibischk is run as an external executable (path via config/env;
never bundled — source is license-restricted). Output is line-oriented
`ERROR`/`WARNING`/`NOTE`. Mapping: any `ERROR` → `reject`; `WARNING`(s) only →
`pass-with-flags`; clean → `pass`. Raw lines are preserved alongside structured fields.
Tests parse **captured** stdout fixtures (recorded mode) so CI needs no executable; a
live-run test is skipped when the executable is absent.

## COM (Channel Operating Margin)

Out of scope for the self-contained build (see PHASE-NOTES): requires vendoring a
maintained Python port with provenance. Per the Phase-3 cut-line, COM is the first cut
if no trustworthy port surfaces within budget. Any COM output must be stamped
`UNVALIDATED_AGAINST_MATLAB_REFERENCE`.

## Model librarian

SQLite registry, state machine `requested → received → validated → filed → stale`, keyed
by `(part, rev, corner, model_type)`. Illegal transitions raise. `intake` runs the IBIS
+ Touchstone gates and advances state (a failed intake holds at `received`). jinja2
chase-email templates; no LLM anywhere in this phase.
