"""Cavity-model PDN impedance engine. Implements docs/pdn-spec.md verbatim.

Omission (documented): conductor/skin loss is not modeled (tanδ_eff = tanδ, dielectric
only). This affects peak Q, not peak location (what the physics fixture checks).
numpy/scipy only; vectorized over frequency.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

MU0 = 1.2566370614e-6
EPS0 = 8.854e-12
C0 = 299792458.0


@dataclass
class Cavity:
    a: float  # m
    b: float  # m
    d: float  # m
    epsilon_r: float
    tan_delta: float = 0.0


@dataclass
class Decap:
    x: float
    y: float
    r: float  # ohm
    ind: float  # H
    c: float  # F


@dataclass
class Port:
    x: float
    y: float


def capacitance(cav: Cavity) -> float:
    return EPS0 * cav.epsilon_r * cav.a * cav.b / cav.d


def resonance_frequencies(cav: Cavity, max_m: int = 2, max_n: int = 2) -> dict:
    """Analytic f_mn = (c / (2√εr)) · √((m/a)² + (n/b)²)."""
    out = {}
    factor = C0 / (2.0 * np.sqrt(cav.epsilon_r))
    for m in range(max_m + 1):
        for n in range(max_n + 1):
            if m == 0 and n == 0:
                continue
            out[f"{m}_{n}"] = factor * np.sqrt((m / cav.a) ** 2 + (n / cav.b) ** 2)
    return out


def _mode_arrays(cav: Cavity, ports, M: int, N: int):
    m = np.arange(M + 1)
    n = np.arange(N + 1)
    km = m * np.pi / cav.a
    kn = n * np.pi / cav.b
    chi_m = np.where(m == 0, 1.0, 2.0)
    chi_n = np.where(n == 0, 1.0, 2.0)
    kmn2 = km[:, None] ** 2 + kn[None, :] ** 2  # [M+1, N+1]
    # cos factors per port: cos_m[port, m], cos_n[port, n]
    cos_m = np.cos(np.outer([p.x for p in ports], km))
    cos_n = np.cos(np.outer([p.y for p in ports], kn))
    return km, kn, chi_m, chi_n, kmn2, cos_m, cos_n


def z_matrix(freqs, cav: Cavity, ports, M: int = 30, N: int = 30):
    """Full P×P Z-matrix over frequency: returns [F, P, P] complex."""
    freqs = np.asarray(freqs, dtype=float)
    omega = 2 * np.pi * freqs
    k2 = omega ** 2 * MU0 * EPS0 * cav.epsilon_r * (1 - 1j * cav.tan_delta)  # [F]
    _, _, chi_m, chi_n, kmn2, cos_m, cos_n = _mode_arrays(cav, ports, M, N)
    chi = chi_m[:, None] * chi_n[None, :]  # [M+1,N+1]
    P = len(ports)
    prefactor = 1j * omega * MU0 * cav.d / (cav.a * cav.b)  # [F]
    Z = np.zeros((len(freqs), P, P), dtype=complex)
    # denom[m,n,f] = kmn2 - k2
    denom = kmn2[:, :, None] - k2[None, None, :]  # [M+1,N+1,F]
    for p in range(P):
        for q in range(p, P):
            # numerator coeff[m,n] = chi * cos_m[p,m]cos_m[q,m] * cos_n[p,n]cos_n[q,n]
            coeff = (chi * np.outer(cos_m[p], cos_m[q])
                     * np.outer(cos_n[p], cos_n[q]))  # [M+1,N+1]
            s = np.sum(coeff[:, :, None] / denom, axis=(0, 1))  # [F]
            Zpq = prefactor * s
            Z[:, p, q] = Zpq
            Z[:, q, p] = Zpq
    return Z


def z_self(freqs, cav: Cavity, port: Port, M: int = 30, N: int = 30):
    return z_matrix(freqs, cav, [port], M, N)[:, 0, 0]


def z_with_decaps(freqs, cav: Cavity, obs: Port, decaps, M: int = 30, N: int = 30):
    """Observation-port |Z| with decaps terminated (multiport shunt reduction)."""
    freqs = np.asarray(freqs, dtype=float)
    omega = 2 * np.pi * freqs
    ports = [obs] + [Port(dc.x, dc.y) for dc in decaps]
    Z = z_matrix(freqs, cav, ports, M, N)  # [F, P, P]
    if not decaps:
        return Z[:, 0, 0]
    out = np.empty(len(freqs), dtype=complex)
    for i, w in enumerate(omega):
        zcap = np.array(
            [dc.r + 1j * w * dc.ind + 1.0 / (1j * w * dc.c) for dc in decaps])
        Zdd = Z[i, 1:, 1:] + np.diag(zcap)
        Zod = Z[i, 0:1, 1:]
        Zdo = Z[i, 1:, 0:1]
        out[i] = Z[i, 0, 0] - (Zod @ np.linalg.solve(Zdd, Zdo))[0, 0]
    return out


def find_resonance_peaks(freqs, z):
    """Return frequencies of |Z| local maxima (scipy.signal.find_peaks)."""
    from scipy.signal import find_peaks

    mag = np.abs(z)
    idx, _ = find_peaks(np.log10(mag))
    return np.asarray(freqs)[idx]


@dataclass
class TargetMask:
    freqs: list[float] = field(default_factory=list)
    z: list[float] = field(default_factory=list)

    def value_at(self, f):
        return np.interp(f, self.freqs, self.z)


def worst_margin(freqs, z, mask: TargetMask):
    """Return (worst_margin_ohm, frequency) where margin = target - |Z| (neg = fail)."""
    mag = np.abs(z)
    target = mask.value_at(np.asarray(freqs))
    margin = target - mag
    i = int(np.argmin(margin))
    return float(margin[i]), float(np.asarray(freqs)[i])


def plot_impedance(freqs, z, path, mask: TargetMask | None = None):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots()
    ax.loglog(freqs, np.abs(z), label="|Z|")
    if mask is not None:
        ax.loglog(mask.freqs, mask.z, "r--", label="target")
    ax.set_xlabel("Frequency (Hz)")
    ax.set_ylabel("|Z| (ohm)")
    ax.legend()
    ax.grid(True, which="both", ls=":")
    fig.savefig(path, dpi=80)
    plt.close(fig)
    return path
