# Phase 3 — SI/PI Validator Stack (15 hrs)

## Goal
The pillar where everything is downloadable today, assembled into one intake gate an SI
engineer would use the same afternoon: ibischk wrapped into structured verdicts,
Touchstone files gated by IEEE-370-style quality metrics, a COM runner for Ethernet
compliance (loudly flagged as unvalidated against the MATLAB reference), and a minimal
model-librarian state machine with generated chase emails. Read-only. Zero trust
required.

## Entry Gate
- [ ] Phase 0 Violation/Result schema frozen.
- [ ] Phases 1–2 CI/benchmark pattern in place.
- [ ] You have collected the public model fixtures (Human-only task 1).

## Exit Gate
- [ ] Known-bad fixtures rejected with the correct verdict and reason
      (non-passive Touchstone, truncated IBIS, port-count mismatch).
- [ ] Known-good fixtures pass all gates.
- [ ] `pkgtk com` runs end-to-end on the bundled example channel, returns a dB figure,
      and every output carries the UNVALIDATED flag.
- [ ] Librarian DB round-trips the full state machine with generated chase email.

## Human-only tasks (~4 hrs)
1. **Collect public fixtures** (all legitimately free):
   - 3 IBIS models from vendor sites (TI/ADI publish IBIS freely). Note source URLs.
   - 2+ Touchstone files: scikit-rf ships example networks; IEEE P370 published an
     open S-parameter library with its standard — grab 2x-thru examples.
   - Derive known-bad variants **by hand with a documented recipe**: scale S-params by
     1.05 (breaks passivity), truncate an IBIS mid-table, rename .s4p→.s2p
     (port mismatch). Record expected verdicts in fixtures/golden/models/.
2. **Decide the P370 fallback policy** (see research pack) and write it into
   `docs/models-spec.md`: which metrics are computed by skrf classes vs. by our own
   5-line numpy implementations, and the verdict banding.
3. Verify by hand the passivity math on one known-bad file (max singular value of S
   per frequency > 1 where you scaled it).

## Research pack
- **ibischk (the Golden Parser)**: maintained by the IBIS Open Forum; free executables
  for Windows/Linux/macOS from the IBIS tools page (ibis.org / ibis.sae-itc.com);
  source is $2,500-licensed (we use executables only). One invocation checks the
  top-level file plus every referenced .pkg/.ims/.ami file, and loads platform-matching
  IBIS-AMI .dll/.so. Output is line-oriented ERROR/WARNING/NOTE — parse into structured
  verdicts. Context: the IBIS Quality Spec grades models IQ1–IQ3 (IQ1 = zero parser
  errors, warnings explained); Zuken's tool refuses import on parser errors — that
  refusal pattern is exactly our intake gate. Claude Code: fetch the ibischk user-guide
  PDF into reference/ibis/ and pin the exact executable version in a lockfile note.
- **Touchstone quality — IEEE 370-2020**: three metrics with graded bands
  (good/acceptable/inconclusive/poor): passivity (2-norm of S ≤ 1 at each frequency —
  implement as max singular value per freq), reciprocity (integrated |Sij−Sji|),
  causality (clockwise rotation of S in the complex plane per the standard's method).
  scikit-rf ships IEEEP370 quality-check classes (an `IEEEP370` deembedding/QM module
  with frequency-domain quality metrics) and MATLAB's RF Toolbox wraps the official
  P370 source. **API-drift warning**: verify the class names against the installed
  skrf version's docs first; if the QM classes aren't present, passivity and
  reciprocity are ~5 lines of numpy each (implement directly, cite the standard) and
  causality falls back to a flagged heuristic — this fallback policy is human-decided
  in docs/models-spec.md.
- **COM (Channel Operating Margin)**: normatively specified by equations in IEEE 802.3
  Annex 93A/178A; the reference implementation is MATLAB (`com_ieee8023_93a.m`) from
  the IEEE 802.3 tools page; the 802.3dj (224G) era moved COM toward an official IEEE SA
  open-source project, and Python ports exist on GitHub. Plan: locate a maintained
  Python port (search GitHub: "COM ieee 802.3 python channel operating margin"), vendor
  it into `third_party/` with license + provenance header, wire config ingestion
  (COM uses a parameter spreadsheet), and stamp every result
  `UNVALIDATED_AGAINST_MATLAB_REFERENCE` until a cross-check is done (out of scope for
  the 100 hrs — honesty is the brand). PCIe compliance = PCI-SIG Seasim, different
  methodology — explicitly out of scope; note it in the CLI help.
- **Touchstone sanity battery** (ours, deterministic): extension port count vs. matrix
  size, monotonic non-negative frequency vector, no NaN/Inf, DC/low-freq presence flag,
  |S| explosion flag.
- Deps allowed: scikit-rf, numpy, scipy, jinja2, sqlite3 (stdlib), rich.

## Claude Code prompts

### Prompt 3.1 — ibischk wrapper
```
/goal Wrap the ibischk executable: locate/download per-OS binary (documented manual step if licensing requires), run against a model, parse ERROR/WARNING/NOTE lines into a structured Verdict JSON, map to intake decision (reject on ERROR, pass-with-flags on WARNING).
/context Phase 3. Fetch the ibischk user guide into reference/ibis/ first. Fixtures: fixtures/golden/models/ibis/{good1..3, truncated} + expected verdicts.
/inputs docs/models-spec.md, fixtures/golden/models/ibis/
/constraints Executable path via config/env, never bundled in repo. Parser must preserve raw lines alongside structured fields. Tests must run with a recorded-output mode if the executable is absent (skip-with-reason, plus a fixture of captured stdout to parse).
/deliverables src/pkgtk/models/ibis_gate.py, tests/test_ibis_gate.py, fixtures/synthetic/ibischk_stdout/*.txt (captured)
/verify Expected verdicts reproduced from captured stdout; live-run test passes when executable present; make ci green.
```

### Prompt 3.2 — Touchstone quality gate
```
/goal Touchstone intake gate: sanity battery + passivity/reciprocity (+causality per docs/models-spec.md policy) with graded verdicts, using skrf for parsing and the human-decided metric implementations.
/context Phase 3. docs/models-spec.md is normative on which metrics come from skrf classes vs our numpy implementations, and on band thresholds. Check installed skrf API before using any P370 class; implement the documented fallback if absent.
/inputs docs/models-spec.md, fixtures/golden/models/touchstone/ (good + scaled-non-passive + port-mismatch, with expected verdicts)
/constraints Passivity = max singular value per frequency point; report worst frequency. Never auto-"fix" a file. Verdict JSON conforms to the Result schema.
/deliverables src/pkgtk/models/ts_gate.py, tests/test_ts_gate.py
/verify Non-passive fixture rejected citing the worst-offending frequency; good fixtures pass; port-mismatch caught pre-parse; make ci green.
```

### Prompt 3.3 — COM runner
```
/goal Vendor a Python COM implementation with full provenance, wire config ingestion and channel s-params input, expose `pkgtk com`, and stamp all outputs UNVALIDATED_AGAINST_MATLAB_REFERENCE.
/context Phase 3. Search GitHub for maintained Python COM ports; pick by license compatibility + last activity; record the decision in reference/com/CHOICE.md with alternatives considered. Bundle one example channel (from the port's own examples or P370 library data).
/inputs docs/models-spec.md
/constraints third_party/ with LICENSE + provenance header; no modification beyond import shims; if no acceptable port exists, STOP and report — do not write COM from scratch.
/deliverables third_party/com_py/, src/pkgtk/models/com_runner.py, src/pkgtk/cli/com.py, tests/test_com_smoke.py
/verify Smoke test returns a finite dB figure on the bundled channel with the flag present in JSON and console output; make ci green.
```

### Prompt 3.4 — model librarian
```
/goal SQLite model registry implementing the state machine requested→received→validated→filed→stale, keyed by (part, rev, corner, model_type), with jinja2 chase-email generation and CLI: `pkgtk models {add,status,chase,intake}` where intake runs the 3.1/3.2 gates and advances state.
/context Phase 3. No LLM anywhere in this phase — templates only.
/inputs src/pkgtk/models/{ibis_gate.py,ts_gate.py}
/constraints stdlib sqlite3; migrations as numbered SQL files; state transitions validated (illegal transition = error).
/deliverables src/pkgtk/models/registry.py, src/pkgtk/models/templates/chase_email.j2, src/pkgtk/cli/models.py, tests/test_registry.py
/verify Full lifecycle test green including a rejected intake keeping state at received-with-flags; make ci green.
```

## Cut line (in order)
COM runner (3.3) is the first cut if a trustworthy port doesn't surface within the
budget — the validator stack stands without it. Then chase-email polish. Never cut the
Touchstone gate or the known-bad fixtures.
