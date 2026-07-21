"""IPC-2581 XML -> EDB -> ports on named nets -> headless siwave_ng SYZ -> touchstone.

The solver leg of the SIwave -> .sip loop. Timeboxed, fail-loud, idempotent per
workdir. Requires in-session env: ANSYSEM_ROOT261, ANSYSLMD_LICENSE_FILE.

Steps: translate XML to EDB (timebox: the translator is licensed via
elec_solve_level1/2 for IPC-2581), optionally fix up dielectric permittivity
(IPC-2581 often carries no Dk), place two circuit ports (point terminals at
interior points of primitives on the pos/neg nets), add a linear_count SYZ
sweep, write the exec, solve with siwave_ng, and report the touchstone path.

Exit codes: 0 = touchstone produced, 1 = stage failed (message says which), 2 = usage/env.

Usage:
  python build_and_solve.py design.xml workdir --pos-net VDD --neg-net VSS \
      [--sweep 0.001:12:601] [--fixup-er 4.4] [--port-xy-mm X,Y[;X,Y]] [--timeout 900]
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import time
from pathlib import Path


def fail(stage: str, detail: str) -> int:
    print(json.dumps({"ok": False, "stage": stage, "detail": detail}, indent=2))
    return 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("design_xml")
    ap.add_argument("workdir")
    ap.add_argument("--pos-net", required=True)
    ap.add_argument("--neg-net", required=True)
    ap.add_argument("--sweep", default="0.001:12:601",
                    help="F_LO_GHZ:F_HI_GHZ:NPOINTS (linear_count)")
    ap.add_argument("--fixup-er", type=float, default=None,
                    help="force all dielectric layers' material to this Dk")
    ap.add_argument("--port-xy-mm", default=None,
                    help="explicit port points 'X,Y[;X,Y]' in mm (else auto-pick "
                         "via-anchored on-copper points; reuse the reported xy "
                         "across iterations for stable comparisons)")
    ap.add_argument("--port-layer", default="TOP_COND")
    ap.add_argument("--neg-layer", default=None,
                    help="layer for the negative terminal (default: --port-layer)")
    ap.add_argument("--stitch", action="append", default=[],
                    help="NET:FROM_LAYER:TO_LAYER - restore via-to-inner-plane "
                         "galvanic connectivity the IPC-2581 bridge drops: for up "
                         "to 12 existing same-net vias whose xy lies on net copper "
                         "of BOTH layers, place a short-range stub via. The .mcm "
                         "truth (extracta pad table) justifies this; it restores, "
                         "never invents, connectivity. Repeatable.")
    ap.add_argument("--timeout", type=int, default=900)
    ap.add_argument("--version", default="2026.1")
    a = ap.parse_args()

    root = os.environ.get("ANSYSEM_ROOT261")
    if not root or not Path(root, "siwave_ng.exe").is_file():
        print("error: ANSYSEM_ROOT261 not set / siwave_ng.exe not found "
              "(set env in-session; see PLAYBOOK)")
        return 2
    if not os.environ.get("ANSYSLMD_LICENSE_FILE"):
        print("error: ANSYSLMD_LICENSE_FILE not set (missing it = silent hangs)")
        return 2
    xml = Path(a.design_xml).resolve()
    if not xml.is_file():
        print(f"error: not found: {xml}")
        return 2
    work = Path(a.workdir).resolve()
    work.mkdir(parents=True, exist_ok=True)
    lo, hi, npts = a.sweep.split(":")

    # fresh translate every run: copy XML in, remove stale aedb
    local_xml = work / xml.name
    if local_xml != xml:
        shutil.copy2(xml, local_xml)
    aedb = work / (xml.stem + ".aedb")
    if aedb.exists():
        shutil.rmtree(aedb)

    from pyedb import Edb  # deferred: import cost + env must be set first

    # Concurrent pyedb processes share one EDB_RPC_Server on this machine and a
    # sibling's close() can kill our session (observed live: gRPC UNAVAILABLE
    # mid-setup). Policy: never run two pyedb jobs at once; belt-and-braces we
    # retry the whole open+setup once on transient RPC failure.
    t0 = time.perf_counter()
    edb = None
    last = None
    for _attempt in (1, 2):
        try:
            if aedb.exists():
                shutil.rmtree(aedb)
            edb = Edb(edbpath=str(local_xml), version=a.version)
            break
        except Exception as e:
            last = e
            time.sleep(3)
    if edb is None:
        return fail("translate", f"Edb(xml) failed twice: {last!r} - check "
                                 f"translator log next to {local_xml}")
    t_translate = time.perf_counter() - t0

    try:
        nets = list(edb.nets.netlist)
        for want in (a.pos_net, a.neg_net):
            if want not in nets:
                edb.close()
                return fail("nets", f"net '{want}' not in imported design "
                                    f"(has: {sorted(nets)[:40]}...)")

        if a.fixup_er is not None:
            for lname, layer in edb.stackup.layers.items():
                if getattr(layer, "type", "") == "dielectric":
                    try:
                        edb.materials.add_dielectric_material(
                            f"fixup_er_{lname}", a.fixup_er, 0.02)
                        layer.material = f"fixup_er_{lname}"
                    except Exception as e:
                        print(f"  fixup-er warn on {lname}: {e!r}")

        # Port placement per the spike's round-3 recipe: terminals must sit at
        # VIA positions that lie ON a polygon of the target net on the port
        # layer (void-aware). Terminals on disjoint islands solve to GOhm
        # garbage; terminals on pruned non-functional pads fail with exit 1004.
        port_layer = a.port_layer
        neg_layer_arg = a.neg_layer or a.port_layer

        def net_polys(net: str, layer: str) -> list:
            return [p for p in edb.layout.primitives
                    if getattr(p, "net_name", None) == net
                    and getattr(p, "layer_name", None) == layer
                    and getattr(p, "polygon_data", None)]

        def on_copper(net: str, x: float, y: float,
                      layer: str | None = None) -> bool:
            for p in net_polys(net, layer or port_layer):
                try:
                    if not p.polygon_data.is_inside((x, y)):
                        continue
                    in_void = False
                    for v in (getattr(p, "voids", None) or []):
                        vpd = getattr(v, "polygon_data", v)
                        try:
                            if vpd.is_inside((x, y)):
                                in_void = True
                                break
                        except Exception:
                            pass
                    if not in_void:
                        return True
                except Exception:
                    continue
            return False

        def anchored_vias(net: str) -> list[tuple[float, float]]:
            out = []
            for inst in edb.padstacks.instances.values():
                if getattr(inst, "net_name", None) != net:
                    continue
                try:
                    x, y = inst.position
                except Exception:
                    continue
                if on_copper(net, x, y):
                    out.append((float(x), float(y)))
            return out

        if a.port_xy_mm:
            pts = [tuple(float(v) / 1e3 for v in s.split(","))
                   for s in a.port_xy_mm.split(";")]
            (px, py), (nx_, ny_) = pts[0], (pts[1] if len(pts) > 1 else pts[0])
            for net, (x, y), lay in ((a.pos_net, (px, py), port_layer),
                                     (a.neg_net, (nx_, ny_), neg_layer_arg)):
                if not on_copper(net, x, y, lay):
                    edb.close()
                    return fail("ports", f"explicit port point ({x},{y}) is not "
                                         f"on {net} copper of {lay}")
        else:
            pos_c = anchored_vias(a.pos_net)
            neg_c = anchored_vias(a.neg_net)
            if not pos_c or not neg_c:
                edb.close()
                return fail("ports",
                            f"no via-anchored on-copper points: {a.pos_net} has "
                            f"{len(pos_c)}, {a.neg_net} has {len(neg_c)} on "
                            f"{port_layer}")
            px, py = pos_c[0]
            nx_, ny_ = min(neg_c,
                           key=lambda q: (q[0] - px) ** 2 + (q[1] - py) ** 2)

        # BRIDGE FIXUP (root-caused live): anstranslator imports IPC-2581 padstack
        # definitions with an EMPTY hole material -> every via barrel is
        # non-conductive and nothing galvanically reaches inner layers. Restore
        # the physical truth (plated copper barrels). Loud, never silent.
        via_fixups = []
        for pname, pdef in edb.padstacks.definitions.items():
            if not getattr(pdef, "material", None):
                try:
                    pdef.material = "COPPER"
                    via_fixups.append(pname)
                except Exception as e:
                    print(f"  via-material fixup FAILED on {pname}: {e!r}")
        if via_fixups:
            print(f"  via-material fixup: set COPPER barrel on {via_fixups}")

        stitch_report = []
        for spec in a.stitch:
            snet, lfrom, lto = spec.split(":")
            placed = 0
            for inst in edb.padstacks.instances.values():
                if placed >= 12:
                    break
                if getattr(inst, "net_name", None) != snet:
                    continue
                try:
                    x, y = inst.position
                except Exception:
                    continue
                if on_copper(snet, x, y, lfrom) and on_copper(snet, x, y, lto):
                    try:
                        edb.padstacks.place(
                            [x, y], inst.padstack_definition
                            if hasattr(inst, "padstack_definition")
                            else "VIA_THT",
                            net_name=snet, fromlayer=lfrom, tolayer=lto)
                        placed += 1
                    except TypeError:
                        edb.padstacks.place([x, y], "VIA_THT", net_name=snet)
                        placed += 1
            stitch_report.append({"spec": spec, "placed": placed})
            if placed == 0:
                edb.close()
                return fail("stitch", f"no eligible via sites for {spec} "
                                      "(need same-net copper on both layers)")

        se = edb.excitation_manager
        t_pos = se.create_point_terminal(px, py, port_layer, a.pos_net,
                                         name="LP_pos")
        t_neg = se.create_point_terminal(nx_, ny_, neg_layer_arg, a.neg_net,
                                         name="LP_neg")
        se.create_port(t_pos, t_neg, is_circuit_port=True, name="P1")
        pos_layer, neg_layer = port_layer, neg_layer_arg

        edb.simulation_setups.create_siwave_setup(
            name="loop_syz", distribution="linear_count",
            start_freq=f"{lo}GHz", stop_freq=f"{hi}GHz", step_freq=int(npts))
        exec_path = edb.siwave.create_exec_file(
            add_syz=True, export_touchstone=True)
        ep = Path(exec_path) if exec_path else next(work.glob("*.exec"), None)
        if ep and "SetNumCpus" not in ep.read_text(encoding="utf-8",
                                                   errors="replace"):
            ep.write_text("SetNumCpus 4\n" + ep.read_text(encoding="utf-8",
                                                          errors="replace"),
                          encoding="utf-8")
        edb.save()
        edb.close()
    except Exception as e:
        try:
            edb.close()
        except Exception:
            pass
        return fail("setup", repr(e))

    exe = str(Path(root, "siwave_ng.exe"))
    t0 = time.perf_counter()
    try:
        r = subprocess.run(
            [exe, str(aedb), str(ep), "-formatOutput", "-useSubdir",
             "-WaitForLicense"],
            capture_output=True, text=True, timeout=a.timeout, cwd=str(work))
    except subprocess.TimeoutExpired:
        return fail("solve", f"siwave_ng timed out after {a.timeout}s")
    t_solve = time.perf_counter() - t0
    if r.returncode != 0:
        return fail("solve", f"siwave_ng rc={r.returncode}: {r.stdout[-1500:]} "
                             f"{r.stderr[-1500:]}")

    snp = sorted(work.glob("*.s*p"), key=lambda p: p.stat().st_mtime)
    if not snp:
        snp = sorted(work.rglob("*.s*p"), key=lambda p: p.stat().st_mtime)
    if not snp:
        return fail("collect", "solve rc=0 but no touchstone found in workdir")

    print(json.dumps({
        "ok": True, "touchstone": str(snp[-1]),
        "ports": {"pos": [px, py, pos_layer], "neg": [nx_, ny_, neg_layer]},
        "stitch": stitch_report,
        "wall_s": {"translate": round(t_translate, 1), "solve": round(t_solve, 1)},
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
