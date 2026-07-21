"""Run ONE full loop iteration end-to-end: edit -> export -> solve -> analyze -> judge.

This is the deterministic harness used to prove the loop is mistake-independent
(the live agent normally drives the same steps one by one, reasoning in between).
Each iteration gets its own numbered directory under the loop workspace with every
artifact + a manifest, so evidence is never overwritten.

Exit codes: 0 = iteration completed AND fix verified by loop_check, 1 = any stage
failed or fix not proven, 2 = usage/env.

Usage:
  python run_iteration.py WORKSPACE DESIGN.mcm --iter-name iter_002 \
      --edit resize-plane --net VDD --layer TOP_COND --rect X1,Y1,X2,Y2 \
      --pos-net VDD --neg-net VSS --mask 3:8:20 --port 1 \
      --baseline-verdict WORKSPACE/iter_001/verdict.json [--sweep 0.001:12:601]
Skip --edit to run a baseline (solve+analyze only) iteration.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent


def step(name: str, cmd: list[str], log: Path, ok_codes: tuple = (0,)) -> tuple[bool, int]:
    t0 = time.perf_counter()
    r = subprocess.run(cmd, capture_output=True, text=True)
    wall = time.perf_counter() - t0
    log.write_text(
        f"$ {' '.join(cmd)}\nrc={r.returncode} wall={wall:.1f}s\n\n"
        f"{r.stdout}\n{r.stderr}", encoding="utf-8")
    ok = r.returncode in ok_codes
    print(f"  [{name}] rc={r.returncode} wall={wall:.1f}s "
          f"{'OK' if ok else 'FAIL -> ' + str(log)}")
    return ok, r.returncode


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("workspace")
    ap.add_argument("design")
    ap.add_argument("--iter-name", required=True)
    ap.add_argument("--edit", choices=["resize-plane", "add-via", "none"],
                    default="none")
    ap.add_argument("--net")
    ap.add_argument("--layer")
    ap.add_argument("--rect")
    ap.add_argument("--xy")
    ap.add_argument("--padstack")
    ap.add_argument("--pos-net", required=True)
    ap.add_argument("--neg-net", required=True)
    ap.add_argument("--mask", action="append", default=[])
    ap.add_argument("--port", type=int, default=1)
    ap.add_argument("--sweep", default="0.001:12:601")
    ap.add_argument("--fixup-er", type=float, default=None)
    ap.add_argument("--baseline-verdict",
                    help="prior verdict.json to judge improvement against")
    a = ap.parse_args()

    ws = Path(a.workspace).resolve()
    itdir = ws / a.iter_name
    if itdir.exists():
        # a pre-seeded PREDICTION.md is encouraged (playbook: predict BEFORE
        # solving); anything else means the iteration already ran.
        leftovers = {p.name for p in itdir.iterdir()} - {"PREDICTION.md"}
        if leftovers:
            print(f"error: {itdir} already has artifacts {sorted(leftovers)} - "
                  "iterations are append-only")
            return 2
    itdir.mkdir(parents=True, exist_ok=True)
    design_src = Path(a.design).resolve()
    design = itdir / design_src.name
    shutil.copy2(design_src, design)
    py = sys.executable
    manifest: dict = {"iter": a.iter_name, "design_src": str(design_src),
                      "edit": a.edit, "stages": {}}

    if a.edit != "none":
        cmd = [py, str(HERE / "apply_edit.py"), str(design), a.edit,
               "--net", a.net or ""]
        if a.edit == "resize-plane":
            cmd += ["--layer", a.layer or "", "--rect", a.rect or ""]
        else:
            cmd += ["--xy", a.xy or "", "--padstack", a.padstack or ""]
        ok, rc = step("edit+verify", cmd, itdir / "edit.log")
        manifest["stages"]["edit"] = rc
        if not ok:
            (itdir / "manifest.json").write_text(json.dumps(manifest, indent=2))
            return 1

    xml = itdir / "design.xml"
    ok, rc = step("export", [py, str(HERE / "export_design.py"), str(design),
                             str(xml)], itdir / "export.log")
    manifest["stages"]["export"] = rc
    if not ok:
        (itdir / "manifest.json").write_text(json.dumps(manifest, indent=2))
        return 1

    solve_dir = itdir / "solve"
    cmd = [py, str(HERE / "build_and_solve.py"), str(xml), str(solve_dir),
           "--pos-net", a.pos_net, "--neg-net", a.neg_net, "--sweep", a.sweep]
    if a.fixup_er is not None:
        cmd += ["--fixup-er", str(a.fixup_er)]
    ok, rc = step("solve", cmd, itdir / "solve.log", ok_codes=(0,))
    manifest["stages"]["solve"] = rc
    if not ok:
        (itdir / "manifest.json").write_text(json.dumps(manifest, indent=2))
        return 1
    # robust touchstone discovery: newest s*p under solve dir
    snp = sorted(solve_dir.rglob("*.s*p"), key=lambda p: p.stat().st_mtime)
    if not snp:
        print("  [collect] FAIL no touchstone")
        manifest["stages"]["collect"] = 1
        (itdir / "manifest.json").write_text(json.dumps(manifest, indent=2))
        return 1
    ts = snp[-1]

    verdict = itdir / "verdict.json"
    cmd = [py, str(HERE / "analyze.py"), str(ts), "--port", str(a.port),
           "--json", str(verdict), "--png", str(itdir / "z.png")]
    for m in a.mask:
        cmd += ["--mask", m]
    ok, rc = step("analyze", cmd, itdir / "analyze.log", ok_codes=(0, 1))
    manifest["stages"]["analyze"] = rc
    manifest["touchstone"] = str(ts)

    judged = None
    if a.baseline_verdict:
        cmd = [py, str(HERE / "loop_check.py"), a.baseline_verdict, str(verdict),
               "--json", str(itdir / "judge.json"),
               "--png", str(itdir / "before_after.png")]
        okj, rcj = step("judge", cmd, itdir / "judge.log", ok_codes=(0, 1))
        manifest["stages"]["judge"] = rcj
        judged = rcj

    (itdir / "manifest.json").write_text(json.dumps(manifest, indent=2),
                                         encoding="utf-8")
    print(json.dumps({"iter": a.iter_name, "verdict": str(verdict),
                      "analyze_rc": rc, "judge_rc": judged}, indent=2))
    if a.baseline_verdict:
        return 0 if judged == 0 else 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
