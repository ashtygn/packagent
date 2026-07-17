"""Touchstone intake gate: sanity battery + passivity/reciprocity (IEEE-370 style).

Self-contained numpy parser (no scikit-rf dependency) so the gate runs in core CI.
See docs/models-spec.md (normative). Never auto-fixes a file; read-only verdicts.
"""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np

from pkgtk.schemas.violation import (
    Citation,
    LogicalLocation,
    MeasurementValue,
    Violation,
)

CHECK_VERSION = "0.1.0"
_FREQ_MULT = {"HZ": 1.0, "KHZ": 1e3, "MHZ": 1e6, "GHZ": 1e9}


class TouchstoneError(ValueError):
    pass


def ports_from_extension(path: str | Path) -> int | None:
    m = re.search(r"\.s(\d+)p$", str(path), re.IGNORECASE)
    return int(m.group(1)) if m else None


def parse_touchstone(path: str | Path):
    """Return (freqs_hz [F], S [F,N,N] complex, z0, n_ports)."""
    text = Path(path).read_text(encoding="utf-8", errors="replace")
    freq_unit, fmt, z0 = "GHZ", "MA", 50.0
    nums: list[float] = []
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith("!"):
            continue
        if s.startswith("#"):
            toks = s[1:].split()
            i = 0
            while i < len(toks):
                t = toks[i].upper()
                if t in _FREQ_MULT:
                    freq_unit = t
                elif t in ("RI", "MA", "DB"):
                    fmt = t
                elif t == "R" and i + 1 < len(toks):
                    z0 = float(toks[i + 1])
                    i += 1
                i += 1
            continue
        nums.extend(float(x) for x in s.replace(",", " ").split())

    if not nums:
        raise TouchstoneError("no data rows")
    # Infer ports: each row = 1 freq + 2*N^2 values. Try N from extension, else solve.
    n_ext = ports_from_extension(path)
    per_row = None
    if n_ext:
        per_row = 1 + 2 * n_ext * n_ext
        if len(nums) % per_row != 0:
            # Port-count mismatch: extension disagrees with row width. Report N from ext
            # but flag; try to recover row width from the data for downstream shape.
            return _mismatch(nums, n_ext, freq_unit, z0)
    else:
        raise TouchstoneError("cannot infer port count without .sNp extension")

    rows = np.array(nums, dtype=float).reshape(-1, per_row)
    freqs = rows[:, 0] * _FREQ_MULT[freq_unit]
    body = rows[:, 1:].reshape(len(rows), n_ext * n_ext, 2)
    s_flat = _to_complex(body, fmt)  # [F, N*N]
    s = s_flat.reshape(len(rows), n_ext, n_ext)
    if n_ext == 2:
        # Touchstone 2-port order is S11 S21 S12 S22 -> transpose the 2x2.
        s = s.transpose(0, 2, 1)
    return freqs, s, z0, n_ext


def _mismatch(nums, n_ext, freq_unit, z0):
    raise _PortMismatch(n_ext, len(nums))


class _PortMismatch(Exception):
    def __init__(self, declared, total):
        self.declared = declared
        self.total = total


def _to_complex(body, fmt):
    a, b = body[..., 0], body[..., 1]
    if fmt == "RI":
        return a + 1j * b
    if fmt == "MA":
        return a * np.exp(1j * np.deg2rad(b))
    if fmt == "DB":
        return (10 ** (a / 20.0)) * np.exp(1j * np.deg2rad(b))
    raise TouchstoneError(f"unknown format {fmt}")


def _violation(rule_id, measured, required, units, reason):
    return Violation(
        rule_id=rule_id, severity="hard",
        location=LogicalLocation(kind="logical", net=reason),
        measured=(MeasurementValue(value=round(measured, 6), units=units)
                  if measured is not None else None),
        required=(MeasurementValue(value=required, units=units)
                  if required is not None else None),
        citation=Citation(doc="IEEE Std 370-2020", note=reason),
        check_version=CHECK_VERSION,
    )


def gate(path: str | Path) -> dict:
    name = Path(path).name
    n_ext = ports_from_extension(path)
    try:
        freqs, s, z0, n = parse_touchstone(path)
    except _PortMismatch as exc:
        v = _violation("touchstone.port_count", exc.total, exc.declared, "count",
                       "port_count_mismatch")
        return _result(name, n_ext, "reject", None, None, None, [v],
                       sanity={"port_count_ok": False})

    finite = bool(np.all(np.isfinite(s)))
    monotonic = bool(np.all(np.diff(freqs) > 0))
    low_freq_flag = bool(freqs[0] > 1e6)

    sigma = np.array([np.linalg.svd(s[i], compute_uv=False)[0]
                      for i in range(len(freqs))])
    sigma_max = float(np.max(sigma))
    worst_freq = float(freqs[int(np.argmax(sigma))])
    recip = float(np.max(np.abs(s - s.transpose(0, 2, 1)))) if n > 1 else 0.0

    if sigma_max <= 1.001:
        band, decision = "good", "pass"
    elif sigma_max <= 1.05:
        band, decision = "acceptable", "pass-with-flags"
    else:
        band, decision = "poor", "reject"

    violations = []
    if not finite:
        decision = "reject"
        violations.append(_violation("touchstone.finite", None, None, "", "non_finite"))
    if not monotonic:
        decision = "reject"
        violations.append(
            _violation("touchstone.frequency", None, None, "", "freq_not_monotonic"))
    if band == "poor":
        violations.append(_violation("touchstone.passivity", sigma_max, 1.0,
                                     "sigma_max", "non_passive"))

    return _result(name, n, decision, round(sigma_max, 6), round(worst_freq, 3),
                   round(recip, 6), violations,
                   sanity={"port_count_ok": True, "freq_monotonic": monotonic,
                           "finite": finite, "low_freq_flag": low_freq_flag},
                   band=band)


def _result(name, ports, decision, sigma_max, worst_freq, recip, violations,
            sanity, band=None):
    return {
        "file": name,
        "ports": ports,
        "decision": decision,
        "passivity": {"sigma_max": sigma_max, "worst_freq_hz": worst_freq,
                      "band": band},
        "reciprocity": {"max_asymmetry": recip},
        "causality": "unassessed",
        "sanity": sanity,
        "violations": [v.model_dump(mode="json", exclude_none=True)
                       for v in violations],
    }
