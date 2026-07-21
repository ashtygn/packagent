# PLAYBOOK — the SIwave → .sip agentic fix loop

You are an agent asked to make a package design meet a PDN impedance mask. You do
not just run commands: you read solver physics, decide a geometric fix, apply it to
the Cadence design database headless, and prove the fix with a re-solve. Every step
below has a verifying tool — never skip a verification.

## The loop

```
1  EXPORT     design.mcm --ipc2581--> design.xml          (export_design.py)
2  SOLVE      design.xml --EDB+ports--> siwave_ng --> .s2p (build_and_solve.py)
3  ANALYZE    .s2p --> verdict JSON (peaks, mask, gate)    (analyze.py)
4  REASON     you. physics below. decide ONE fix.
5  EDIT       apply the fix to the .mcm headless           (apply_edit.py)
6  VERIFY     geometric proof the DB changed as commanded  (apply_edit.py --verify, automatic)
7  RE-RUN     steps 1-3 on the edited design
8  JUDGE      before vs after                              (loop_check.py)
```

Iterate 4–8 until `loop_check.py` says `fixed: true`. Keep every iteration in its
own numbered directory (`iter_001/`, `iter_002/`…) — never overwrite evidence.

## Step 4: how to reason (the part that is YOU)

The analysis JSON gives you peaks `{f_ghz, z_ohm}` and mask violations. Typical
diagnosis for a plane-pair package PDN:

**A sharp |Z| peak inside the mask band is a plane cavity resonance.** For a
rectangular plane pair of size a × b (meters), dielectric εr, the resonant modes are

```
f_mn = c / (2·√εr) · √((m/a)² + (n/b)²)        c = 3e8 m/s
f_10 = c / (2·a·√εr)      (lowest mode, along the long dimension a)
```

The solver sits a few percent BELOW the closed-form value (fringing makes the
cavity electrically larger — expect ≈ 2–4% down; tonight's measured case: analytic
7.143 GHz vs solver 6.880 GHz, −3.7%). **Budget for that when you pick a target.**

Fix options, in order of demo strength:

| Fix | Physics | When |
|---|---|---|
| **Shrink the plane** (a↓) | f_10 ∝ 1/a → peak moves UP and out of the band. Side effect: static C = ε0·εr·a·b/d drops → low-freq \|Z\| rises ∝ 1/C. Check the mask still passes at the low end | peak just inside the band's top edge |
| **Grow the plane** (a↑) | f_10 moves DOWN — useful to move a peak below the band bottom, and raises C | peak just above the band's bottom edge |
| **Stitching vias** | shorting vias between the planes push the effective cavity modes up and damp Q. Harder to predict closed-form — use for damping, verify by solve | peak reduction rather than relocation |

Worked example (tonight's live case): mask `3:8:20` (≤20 Ω, 3–8 GHz) fails at
6.880 GHz / 533 Ω on a 10×10 mm εr=4.4 plane pair. To clear the band with margin,
target f_10 ≥ 9.3 GHz analytic (≈ 9.0 GHz after −3.5% fringing → above 8 GHz with
~1 GHz margin): a ≤ c/(2·9.3e9·√4.4) = 7.69 mm → **choose a = 7.5 mm** →
analytic f_10 = 9.54 GHz, expected solver ≈ 9.2 GHz. Also re-check f_01 (b
unchanged → 7.15→~6.9 GHz stays? No: f_01 depends on b — if you shrink only a,
f_01 stays at its old value and is STILL in band!). **On a square plane you must
shrink BOTH dimensions** or the degenerate f_01 mode remains. Shrink a AND b.

Always state your prediction BEFORE re-solving (write it in `iter_NNN/prediction.md`):
expected new peak frequency ± tolerance. The re-solve either confirms your physics
or tells you your model is wrong — both are information.

## Hard rules (mistake-independence)

1. **Copies only.** The loop operates on `work/design.mcm`, never an original.
   Headless APD `exit` auto-saves — that is the commit mechanism for edits.
2. **Never trust an edit you didn't verify.** `apply_edit.py` re-opens the DB and
   geometrically verifies the change (and fails loudly if the shape/via isn't
   exactly as commanded). If verification fails, the iteration is dead — start a
   fresh copy; do not stack edits on an unverified state.
3. **Never trust a solve that fails the physics gate.** analyze.py embeds the
   ts_gate verdict; loop_check.py refuses a `fixed` verdict on a failing gate.
4. **One fix per iteration.** Multiple simultaneous edits make the physics
   unattributable.
5. **Timebox everything.** Solver/translator hangs are killed by the tools; a
   timeout is a loud result, not a retry-forever.
5b. **One pyedb job at a time.** Concurrent pyedb processes share one
   EDB_RPC_Server on a machine, and one process's close() can kill the other's
   session (observed live: gRPC UNAVAILABLE mid-setup). Serialize all
   build_and_solve.py runs; the tool also retries a transient open failure once.
6. If a tool exits 2 (usage/environment), fix the invocation; if it exits 1 with a
   verdict, that is DATA (success-with-findings), not an error.

## Port strategy (choose deliberately, per measurement intent)

- **Package-level** (default): auto-picked terminals at via positions that sit ON
  the target net's copper of `--port-layer` (void-aware). This is what the mask
  usually means. Terminals on disjoint islands solve to GΩ garbage; pruned
  non-functional pads fail with solver exit 1004 — the tool guards both.
- **Plane-level** (`--port-layer SUPPLY --neg-layer GROUND --port-xy-mm 0,0`):
  measures the plane pair itself — use to verify a plane fix's capacitance
  against your prediction independently of the rest of the network.
- Reuse the reported port xy across iterations (`--port-xy-mm`) so before/after
  comparisons are apples-to-apples.

## Known model limitations (discovered live, triple-tested — read before trusting)

**IPC-2581→EDB via galvanic connectivity.** Vias imported over this bridge do not
galvanically connect layers in the SIwave solve, even with pads on all layers,
100% plating, restored COPPER barrel material (`build_and_solve` fixes the empty
material automatically), and added short-range stitching stubs — all verified
persisted in the solved .aedb. Symptom: low-frequency |Z| is bit-identical across
model variants and matches a purely capacitive series chain. Consequence: a fix
that depends on via stitching will show up at the plane level but not fully at the
package port. Do not burn iterations re-fixing the design — the design is right;
the model is the limit. Verify at plane level, file the discrepancy, and (future)
cross-check with Sigrity PowerSI or HFSS 3D Layout.

**Ring-coverage floor (discovered in the round-2 campaign).** A reference plane
must extend UNDER its net's via ring or package-level coupling collapses (the
13 mm iteration crashed C from 61→2.1 pF because the plane edge stopped short of
the 6.75–7.25 mm VDD ring). Before proposing a resize, map the feed-ring radii
(padstack-instance xy of the net) and treat ring coverage as a hard constraint on
the lever range. Corollary: when a legal-range resize leaves the curve
numerically unchanged, the measured resonances belong to the feed structure, not
the planes — switch lever class (damping/stitching/decap) or report the
requirement conflict.

**Bit-identical results are a red flag.** If a re-solve returns the identical
number to 3 decimals after a change, your change did not reach the solve OR the
mechanism you changed is inert. Verify persistence by re-opening the solved .aedb
before drawing physics conclusions.

## Environment (set in-session before build_and_solve.py)

```powershell
$env:ANSYSEM_ROOT261 = 'C:\Program Files\ANSYS Inc\v261\AnsysEM'
$env:AWP_ROOT261     = 'C:\Program Files\ANSYS Inc\v261'
$env:ANSYSLMD_LICENSE_FILE = '<port>@<license-server>'   # site-specific
```
