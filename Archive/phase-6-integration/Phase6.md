# Phase 6 — Integration + Launch Artifact (8 hrs)

## Goal
One CLI, one demo command, one honest benchmark document. `pkgtk` unifies every wedge;
`make demo` runs the whole toolkit on bundled examples from a clean clone in under five
minutes and leaves an `artifacts/` folder a stranger can browse; the top-level README
becomes the launch post's skeleton with the coverage table and catch rates front and
center. In an industry allergic to demos, the benchmark table IS the launch.

## Entry Gate
- [ ] Phases 0–5 Exit Gates all green (this phase adds no new capability — only
      assembly; if you're tempted to sneak a feature in here, that's the buffer talking).

## Exit Gate (the final gate of the 100 hours)
- [ ] Clean clone → `pip install -e .` (or pipx) → `make demo` → all artifacts
      produced, total runtime < 5 min, zero manual steps.
- [ ] `make bench` green: Phase-1 20/20, Phase-2 fixture suite, Phase-3 verdicts,
      Phase-4 extraction eval, Phase-5 physics invariants — all rolled into one
      BENCHMARKS.md.
- [ ] Top-level README rewritten: what/why in 3 paragraphs, quickstart, the coverage
      table, the benchmark table, the honesty section (what this does NOT do), and the
      NOT-MANUFACTURING-VALID banner for the generic deck.
- [ ] Screenshots/GIF checklist done (Human-only task 2).
- [ ] Tag v0.1.0.

## Human-only tasks (~3 hrs)
1. **Write the honesty section yourself** — the coverage split ("N rule parameters
   implemented, M flagged unimplemented, K manual-checklist"), the UNVALIDATED flag on
   COM, net-aware spacing deferred, conductor loss omitted in PDN v0. The credibility
   of the whole artifact lives in this section; it is voice, not code.
2. **Capture the demo media**: KLayout with clickable lyrdb markers; the ECO diff
   report; the PDN curve vs mask PNG; the review table catching the footnote trap.
   Terminal GIFs via vhs or asciinema — your call.
3. **Decide the release surface** per the Hour-Zero decision: public repo now, or
   private + a write-up you can hand to specific people. Draft the launch post
   skeleton (the benchmark table + 3 honest paragraphs); polishing it for
   distribution is deliberately outside the 100 hours.

## Research pack
- CLI assembly: typer (or click) with subcommands already built per phase —
  `verify, diff, check, models, com, extract, ingest, escape, template, pdn`. This
  phase only unifies help text, exit codes, and a `--json` flag convention.
- Packaging: pyproject entry point `pkgtk = pkgtk.cli.main:app`; pipx-installable;
  pin klayout/gdstk/skrf versions (klayout wheels are platform-specific — note
  supported platforms honestly in README).
- Demo script: a Makefile `demo` target that runs each wedge against
  `fixtures/synthetic/` + goldens and copies outputs into `artifacts/` with a
  MANIFEST.md linking each artifact to the command that produced it.
- BENCHMARKS.md aggregation: each phase's bench emits JSON; this phase adds the
  roll-up renderer. Generated-file banner at top; CI fails if it's stale
  (regenerate-and-diff check).
- vhs (charmbracelet) for scriptable terminal GIFs if you want reproducible media.

## Claude Code prompts

### Prompt 6.1 — CLI unification + packaging
```
/goal Unify all subcommands under one typer app with consistent help, exit-code convention (0 clean / 1 violations / 2 usage / 3 internal), a global --json flag, and pipx-installable packaging with pinned deps.
/context Phase 6. No behavior changes to any wedge — assembly only. Any inconsistency between subcommands' conventions: normalize toward the documented convention and list the changes in PR notes.
/inputs src/pkgtk/cli/*, pyproject.toml
/constraints Do not touch check/diff/oracle logic. Platform support statement for klayout wheels goes in README verbatim from docs/platforms.md (human-written).
/deliverables src/pkgtk/cli/main.py, updated pyproject.toml, tests/test_cli_conventions.py (every subcommand: --help works, exit codes honored on golden inputs)
/verify pipx install from local path works; conventions test green; make ci green.
```

### Prompt 6.2 — make demo
```
/goal A `make demo` target running every wedge end-to-end on bundled fixtures from a clean clone, producing artifacts/ with MANIFEST.md (artifact → producing command → 1-line description), total < 5 min, zero prompts.
/context Phase 6. Everything it runs already exists and is green.
/inputs Makefile, fixtures/, src/pkgtk/
/constraints Idempotent (rm -rf artifacts/ first); every step echoes the exact CLI command a user could copy; failure of any step fails the target loudly.
/deliverables Makefile demo target, scripts/demo.sh, artifacts/.gitignore
/verify Fresh clone in a temp dir: pip install -e . && make demo succeeds < 5 min; MANIFEST.md lists every artifact; make ci green.
```

### Prompt 6.3 — benchmark roll-up + README assembly
```
/goal Aggregate all per-phase benchmark JSON into one BENCHMARKS.md (tables: ballmap catch rates, lint fixture matrix, model-gate verdicts, extraction precision/recall, PDN invariant deltas) with a staleness CI check; assemble the top-level README from the human-written sections in docs/readme-sections/ plus the generated tables.
/context Phase 6. The honesty section and platform statement are human-written inputs — include verbatim, never paraphrase.
/inputs benchmarks/*.json, docs/readme-sections/
/constraints BENCHMARKS.md and README tables are generated; CI regenerates and diffs — nonzero diff fails. Human sections byte-preserved.
/deliverables benchmarks/rollup.py, updated README.md, CI staleness check in Makefile ci target
/verify Staleness check trips when a benchmark JSON is edited without regeneration; README contains all human sections verbatim; make ci green.
```

## Cut line
GIF tooling automation (capture by hand), pipx polish (pip install -e . is enough).
Never cut the honesty section, the staleness check, or the < 5 min clean-clone demo —
those three ARE the launch artifact.

## After hour 100
Two forks, same repo either way: (a) product — design partner + the Allegro techfile
backend inside a real licensed flow; (b) career — this repo walks into every package-
engineering interview you'll ever take. The decision was deliberately not required
during the build.
