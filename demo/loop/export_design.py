"""Cadence design (.mcm/.sip/.brd) -> IPC-2581 XML, headless, verified.

Wraps ipc2581_out.exe with the flags proven tonight, timeboxed, and verifies the
output XML exists, is non-trivial, and contains LogicalNet + Stackup sections
(fail-loud: a silent half-export must never reach the solver).

Exit codes: 0 = exported+verified, 1 = export ran but verification failed, 2 = usage/env.

Usage: python export_design.py design.mcm out.xml [--apd-root DIR] [--timeout S]
"""

from __future__ import annotations

import argparse
import os
import subprocess
import time
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("design")
    ap.add_argument("out_xml")
    ap.add_argument("--apd-root", default=os.environ.get("PKGTK_APD_ROOT",
                                                         r"C:\Cadence\SPB_24.1"))
    ap.add_argument("--timeout", type=int, default=300)
    a = ap.parse_args()

    design = Path(a.design).resolve()
    out_xml = Path(a.out_xml).resolve()
    out_xml.parent.mkdir(parents=True, exist_ok=True)
    exe = Path(a.apd_root) / "tools" / "bin" / "ipc2581_out.exe"
    if not design.is_file():
        print(f"error: design not found: {design}")
        return 2
    if not exe.is_file():
        print(f"error: ipc2581_out.exe not found under {a.apd_root}")
        return 2
    if design.with_suffix(design.suffix + ".lck").exists():
        print(f"error: {design.name} is locked (.lck present) - close the session "
              "holding it or work on a fresh copy")
        return 2

    # ipc2581_out appends .xml to -o; hand it the stem and rename if needed.
    # Flag set is the FULL-CONTENT export proven in the bridge spike: -O/-I carry
    # outer/inner copper (without them the XML has netlist+stackup but ZERO
    # geometry and the solve is meaningless), -R drills, -p/-c/-t components.
    stem = out_xml.with_suffix("")
    cmd = [str(exe), str(design), "-o", str(stem), "-f", "1.03",
           "-n", "-k", "-l", "-p", "-c", "-t", "-R", "-O", "-I", "-D", "-M",
           "-S", "-u", "MICRON"]
    t0 = time.perf_counter()
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=a.timeout,
                           cwd=str(design.parent))
    except subprocess.TimeoutExpired:
        print(f"error: ipc2581_out timed out after {a.timeout}s")
        return 1
    wall = time.perf_counter() - t0

    produced = stem.with_suffix(".xml")
    if r.returncode != 0 or not produced.is_file():
        print(f"error: export failed rc={r.returncode}")
        print(r.stdout[-2000:])
        print(r.stderr[-2000:])
        return 1
    if produced != out_xml:
        produced.replace(out_xml)

    text = out_xml.read_text(encoding="utf-8", errors="replace")
    checks = {
        "size>50KB": out_xml.stat().st_size > 50_000,
        "LogicalNet": "<LogicalNet" in text,
        "Stackup": "<Stackup" in text,
        "Layer": "<Layer" in text,
        "LayerFeature(copper!)": "<LayerFeature" in text,
    }
    for name, ok in checks.items():
        print(f"  verify {name}: {'OK' if ok else 'FAIL'}")
    if not all(checks.values()):
        print("error: exported XML failed content verification - do not solve this")
        return 1

    print(f"exported {out_xml} ({out_xml.stat().st_size:,} bytes) in {wall:.1f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
