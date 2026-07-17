"""PDN cavity-model physics invariants (the Phase-5 exit-gate math).

Ground truth is fixtures/golden/pdn/expected_resonances.json (hand-computed).
"""

import json
import time

import numpy as np

from pkgtk.oracles.pdn_cavity import (
    Cavity,
    Decap,
    Port,
    TargetMask,
    capacitance,
    find_resonance_peaks,
    resonance_frequencies,
    worst_margin,
    z_self,
    z_with_decaps,
)
from pkgtk.schemas import schemas_dir

GOLDEN = json.loads(
    (schemas_dir().parent / "fixtures" / "golden" / "pdn" /
     "expected_resonances.json").read_text("utf-8")
)
CAV = Cavity(a=0.040, b=0.030, d=0.0008, epsilon_r=4.0, tan_delta=0.02)
PORT = Port(0.040 * 0.15, 0.030 * 0.15)


def test_capacitance_matches_golden():
    assert abs(capacitance(CAV) - GOLDEN["capacitance_F"]) / GOLDEN["capacitance_F"] \
        < 0.01


def test_analytic_resonances_match_golden():
    res = resonance_frequencies(CAV)
    tol = GOLDEN["tolerances"]["resonance_rel"]
    for key, f_golden in GOLDEN["resonances_hz"].items():
        assert abs(res[key] - f_golden) / f_golden < tol


def test_simulated_peaks_match_fmn_within_1pct():
    f = np.linspace(0.1e9, 4e9, 4000)
    z = z_self(f, CAV, PORT, 30, 30)
    peaks = find_resonance_peaks(f, z)
    for key, f_golden in GOLDEN["resonances_hz"].items():
        nearest = peaks[np.argmin(np.abs(peaks - f_golden))]
        assert abs(nearest - f_golden) / f_golden < 0.01, f"no peak near {key}"


def test_lowfreq_asymptote_within_2pct():
    f = 1e6
    z = z_self([f], CAV, PORT)[0]
    expected = 1.0 / (2 * np.pi * f * capacitance(CAV))
    assert abs(abs(z) - expected) / expected < GOLDEN["tolerances"]["lowfreq_rel"]


def test_decap_lowers_low_frequency_impedance():
    f = [1e6]
    bare = abs(z_self(f, CAV, PORT)[0])
    decap = Decap(x=PORT.x, y=PORT.y, r=0.01, ind=0.5e-9, c=100e-9)
    withcap = abs(z_with_decaps(f, CAV, PORT, [decap])[0])
    # A 100 nF decap presents ~1.6 ohm at 1 MHz; the bare plane is ~3 kohm.
    assert withcap < bare / 10.0


def test_runtime_under_1s():
    f = np.linspace(1e6, 4e9, 1000)
    t = time.time()
    z_self(f, CAV, PORT, 30, 30)
    assert time.time() - t < 1.0


def test_target_mask_worst_margin():
    f = np.array([1e6, 1e7, 1e8])
    z = z_self(f, CAV, PORT)
    mask = TargetMask(freqs=[1e6, 1e9], z=[5000.0, 5.0])
    margin, freq = worst_margin(f, z, mask)
    assert isinstance(margin, float) and freq in f
