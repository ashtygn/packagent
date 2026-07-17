# pdn-spec.md — Cavity-model PDN impedance (Phase 5, normative)

The engine implements this formula verbatim. No "improvements"; omissions are listed.

## Impedance formula (rectangular parallel-plate cavity)

Plane pair a×b, dielectric thickness d, ports p,q at (x,y):

```
Z_pq(ω) = (jωμ₀d)/(ab) · Σ_{m=0..M} Σ_{n=0..N}
          [ χ_m χ_n · cos(k_m x_p)cos(k_n y_p) · cos(k_m x_q)cos(k_n y_q) ]
          / ( k_m² + k_n² − k² )

k_m = mπ/a,  k_n = nπ/b,
k²  = ω² μ₀ ε₀ εr · (1 − j·tanδ_eff),
χ_m = 1 if m=0 else 2   (same for χ_n)
```

- Loss: v0 uses `tanδ_eff = tanδ` (dielectric only). **Conductor/skin loss is omitted**
  — this affects peak Q (sharpness), not peak *location*, which is what the fixture
  checks. Documented in the module docstring.
- Convergence: M=N increased adaptively until adding 10 modes changes |Z| by < 0.5%
  up to f_max.

## Validation invariants (the exit-gate math)

- **Resonance peaks** at `f_mn = (c / (2·√εr)) · √((m/a)² + (n/b)²)`.
- **Low-frequency asymptote**: `|Z| → 1/(ωC)` as ω→0, with `C = ε₀·εr·a·b/d`
  (the m=n=0 term of the sum).

## Hand-computed golden (fixtures/golden/pdn/expected_resonances.json)

Cavity a=40 mm, b=30 mm, d=0.8 mm, εr=4.0, tanδ=0.02, c=2.99792458e8 m/s:

- `C = ε₀·εr·a·b/d = 8.854e-12 · 4 · (0.04·0.03)/0.0008 = 5.3126e-11 F` (53.13 pF)
- `|Z|(1 MHz) = 1/(2π·1e6·C) = 2996 Ω`
- `f₁₀ = (c/2√εr)·(1/a) = 7.4948e7 · 25      = 1.8737 GHz`
- `f₀₁ = (c/2√εr)·(1/b) = 7.4948e7 · 33.333  = 2.4983 GHz`
- `f₁₁ = (c/2√εr)·√((1/a)²+(1/b)²) = 7.4948e7 · 41.667 = 3.1228 GHz`

## Decaps
1-port shunt series-RLC at (x,y): `Z_cap = R + jωL + 1/(jωC)`. Combine with the plane's
Z-matrix by building the multiport Z among {observation port + decap ports}, terminating
each decap port in its `Z_cap`, and reducing to the observation port (standard shunt
termination reduction). scipy handles the small dense linear algebra.

## Target mask + artifact
Piecewise-linear `Z_target(f)` from YAML; report worst margin + frequency. matplotlib
log-log |Z| vs mask → PNG.
