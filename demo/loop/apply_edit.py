"""Apply a parameterized geometric edit to a Cadence .mcm/.sip, headless + verified.

The edit leg of the SIwave -> .sip loop. Generates a SKILL job from a
spike-verified template, runs it in headless APD (exit auto-saves = the commit),
then runs an INDEPENDENT verification pass in a fresh APD session that
geometrically confirms the database matches the command. An unverified edit
exits 1 and must never be solved.

Edits (all primitives verified live on APD 24.1):
  add-plane     --net VDD --layer SUPPLY --rect X1,Y1,X2,Y2      (um; net-assigned
                solid static shape via axlDBCreateShape)
  resize-plane  --net VDD --layer SUPPLY --old-rect ... --rect ...  (find by
                layer+bbox, axlDeleteObject, recreate — the loop's edit primitive)
  delete-plane  --net VDD --layer SUPPLY --old-rect ...
  add-via       --net VSS --xy X,Y --padstack VIA_THT            (axlDBCreateVia)

Notes from the spike: create accepts "ETCH/<layer>" but the DB canonicalizes to
"CONDUCTOR/<layer>" — all verification compares canonical names. dbids are
session-local: every run re-finds objects by layer+bBox. Find filters need BOTH
?enabled and ?onButtons plus "INVISIBLE" headless.

Exit codes: 0 = edited AND verified, 1 = edit or verification failed, 2 = usage.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import time
from pathlib import Path

APD_ROOT = os.environ.get("PKGTK_APD_ROOT", r"C:\Cadence\SPB_24.1")
PRODUCT = os.environ.get("PKGTK_APD_PRODUCT", "SiP_Layout_Bundle_1")


def run_headless(design: Path, il_text: str, tag: str,
                 timeout: int = 300) -> tuple[int, str, str]:
    """Run a SKILL job headless. Returns (rc, harness_output, job_log_text).

    The job writes its RESULT/VERIFY lines to its own log file via outfile()
    (site skillinit noise pollutes stdout), which we read back.
    """
    work = design.parent
    log = work / f"{tag}.log"
    if log.exists():
        log.unlink()
    il = work / f"{tag}.il"
    scr = work / f"{tag}.scr"
    il.write_text(il_text.replace("__LOG__", log.as_posix()), encoding="ascii")
    scr.write_text(f'skill load("{il.name}")\nskill main()\nexit\n',
                   encoding="ascii")
    exe = str(Path(APD_ROOT, "tools", "bin", "allegro.exe"))
    cmd = [exe, "-apd", "-product", PRODUCT, "-s", scr.name, "-nograph",
           design.name]
    t0 = time.perf_counter()
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                           cwd=str(work))
    except subprocess.TimeoutExpired:
        return 1, f"headless APD timed out ({timeout}s) - check for stray " \
                  f"allegro PID and {design.name}.lck", ""
    wall = time.perf_counter() - t0
    job_log = log.read_text(encoding="utf-8", errors="replace") if log.exists() else ""
    return r.returncode, f"[apd {wall:.1f}s rc={r.returncode}]", job_log


# --- spike-verified SKILL templates (RESULT/VERIFY lines go to __LOG__) -------

PROLOG = r"""
(defun lp_log (fmt @rest args)
  (let ((f (outfile "__LOG__" "a")))
    (apply 'fprintf (cons f (cons fmt args)))
    (close f)))
(defun lp_shapes ()
  (axlSetFindFilter ?enabled '("NOALL" "SHAPES" "INVISIBLE")
                    ?onButtons '("NOALL" "SHAPES"))
  (axlAddSelectAll)
  (let ((s (axlGetSelSet))) (axlClearSelSet) s))
(defun lp_vias ()
  (axlSetFindFilter ?enabled '("NOALL" "VIAS" "INVISIBLE")
                    ?onButtons '("NOALL" "VIAS"))
  (axlAddSelectAll)
  (let ((s (axlGetSelSet))) (axlClearSelSet) s))
(defun lp_bbox_eq (bb x1 y1 x2 y2)
  (and bb
       (lessp (abs (difference (xCoord (car bb)) x1)) 0.5)
       (lessp (abs (difference (yCoord (car bb)) y1)) 0.5)
       (lessp (abs (difference (xCoord (cadr bb)) x2)) 0.5)
       (lessp (abs (difference (yCoord (cadr bb)) y2)) 0.5)))
"""

CREATE_IL = PROLOG + r"""
(defun main ()
  (let (path res)
    (setq path (axlPathStart
                 (list {x1}:{y1} {x2}:{y1} {x2}:{y2} {x1}:{y2} {x1}:{y1}) 0.0))
    (setq res (axlDBCreateShape path t "ETCH/{layer}" "{net}" nil))
    (if (and res (car res))
        (lp_log "RESULT: created net=%s layer=%s bbox=%L\n"
                "{net}" (car res)->layer (car res)->bBox)
        (lp_log "RESULT: FAIL axlDBCreateShape nil (net {net} layer {layer})\n"))))
"""

DELETE_IL = PROLOG + r"""
(defun main ()
  (let ((hits 0))
    (foreach s (lp_shapes)
      (when (and (equal s->layer "CONDUCTOR/{layer}")
                 s->net (equal s->net->name "{net}")
                 (null s->shapeIsBoundary)
                 (lp_bbox_eq s->bBox {ox1} {oy1} {ox2} {oy2}))
        (setq hits (add1 hits))
        (axlDeleteObject s)
        (lp_log "RESULT: deleted net={net} layer={layer} bbox=((%f %f)(%f %f))\n"
                (float {ox1}) (float {oy1}) (float {ox2}) (float {oy2}))))
    (when (equal hits 0)
      (lp_log "RESULT: FAIL no matching shape to delete (net {net} layer {layer})\n"))))
"""

RESIZE_IL = PROLOG + r"""
(defun main ()
  (let ((hits 0) path res)
    (foreach s (lp_shapes)
      (when (and (equal s->layer "CONDUCTOR/{layer}")
                 s->net (equal s->net->name "{net}")
                 (null s->shapeIsBoundary)
                 (lp_bbox_eq s->bBox {ox1} {oy1} {ox2} {oy2}))
        (setq hits (add1 hits))
        (axlDeleteObject s)))
    (if (equal hits 1)
        (progn
          (setq path (axlPathStart
                       (list {x1}:{y1} {x2}:{y1} {x2}:{y2} {x1}:{y2} {x1}:{y1})
                       0.0))
          (setq res (axlDBCreateShape path t "ETCH/{layer}" "{net}" nil))
          (if (and res (car res))
              (lp_log "RESULT: resized net={net} layer={layer} new_bbox=%L\n"
                      (car res)->bBox)
              (lp_log "RESULT: FAIL recreate returned nil\n")))
        (lp_log "RESULT: FAIL expected exactly 1 old shape, found %d\n" hits))))
"""

ADDVIA_IL = PROLOG + r"""
(defun main ()
  (let (res)
    (setq res (axlDBCreateVia "{padstack}" {x}:{y} "{net}" nil 0.0 nil))
    (if (and res (car res))
        (lp_log "RESULT: via net={net} padstack={padstack} xy=%L\n" (car res)->xy)
        (lp_log "RESULT: FAIL axlDBCreateVia nil\n"))))
"""

VERIFY_SHAPE_IL = PROLOG + r"""
(defun main ()
  (let ((found 0))
    (foreach s (lp_shapes)
      (when (and (equal s->layer "CONDUCTOR/{layer}")
                 s->net (equal s->net->name "{net}")
                 (null s->shapeIsBoundary)
                 (lp_bbox_eq s->bBox {x1} {y1} {x2} {y2}))
        (setq found (add1 found))
        (lp_log "VERIFY: shape net={net} layer=%s bbox=%L\n" s->layer s->bBox)))
    (lp_log "VERIFY: managed_count=%d\n" found)))
"""

VERIFY_GONE_IL = PROLOG + r"""
(defun main ()
  (let ((found 0))
    (foreach s (lp_shapes)
      (when (and (equal s->layer "CONDUCTOR/{layer}")
                 s->net (equal s->net->name "{net}")
                 (null s->shapeIsBoundary)
                 (lp_bbox_eq s->bBox {x1} {y1} {x2} {y2}))
        (setq found (add1 found))))
    (lp_log "VERIFY: managed_count=%d\n" found)))
"""

VERIFY_VIA_IL = PROLOG + r"""
(defun main ()
  (let ((found 0))
    ; NOTE: APD 24.1 via dbids have no padStackDef attribute (matrix case E1
    ; found the nil deref crashing main() = false negative on every good via);
    ; the padstack name is v->name. %L is nil-safe.
    (foreach v (lp_vias)
      (when (and v->net (equal v->net->name "{net}")
                 (lessp (abs (difference (xCoord v->xy) {x})) 1.0)
                 (lessp (abs (difference (yCoord v->xy) {y})) 1.0))
        (setq found (add1 found))
        (lp_log "VERIFY: via net={net} xy=%L padstack=%L\n" v->xy v->name)))
    (lp_log "VERIFY: managed_count=%d\n" found)))
"""


def rect4(s: str) -> tuple[float, float, float, float]:
    x1, y1, x2, y2 = (float(v) for v in s.split(","))
    return min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2)


def edit_and_verify(design: Path, edit_il: str, verify_il: str,
                    expect_count: int, meta: dict) -> int:
    rc, info, log = run_headless(design, edit_il, "loop_edit")
    print(info)
    print(log.strip())
    if rc != 0 or "RESULT: FAIL" in log or "RESULT:" not in log:
        print(json.dumps({"ok": False, "stage": "edit", **meta}))
        return 1
    rc, info, vlog = run_headless(design, verify_il, "loop_verify")
    print(info)
    print(vlog.strip())
    ok = rc == 0 and f"managed_count={expect_count}" in vlog
    print(json.dumps({"ok": ok, "stage": "verified" if ok else "verify", **meta}))
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("design")
    ap.add_argument("edit", choices=["add-plane", "resize-plane", "delete-plane",
                                     "add-via"])
    ap.add_argument("--net", required=True)
    ap.add_argument("--layer")
    ap.add_argument("--rect", help="X1,Y1,X2,Y2 um (target rect)")
    ap.add_argument("--old-rect", help="X1,Y1,X2,Y2 um (existing shape to match)")
    ap.add_argument("--xy", help="X,Y um (add-via)")
    ap.add_argument("--padstack", help="padstack name (add-via)")
    a = ap.parse_args()

    design = Path(a.design).resolve()
    if not design.is_file():
        print(f"error: not found: {design}")
        return 2
    if design.with_suffix(design.suffix + ".lck").exists():
        print(f"error: {design.name} is locked (.lck) - close the holder first")
        return 2

    if a.edit == "add-plane":
        if not (a.layer and a.rect):
            print("error: add-plane needs --layer and --rect")
            return 2
        x1, y1, x2, y2 = rect4(a.rect)
        return edit_and_verify(
            design,
            CREATE_IL.format(net=a.net, layer=a.layer, x1=x1, y1=y1, x2=x2, y2=y2),
            VERIFY_SHAPE_IL.format(net=a.net, layer=a.layer,
                                   x1=x1, y1=y1, x2=x2, y2=y2),
            1, {"edit": "add-plane", "net": a.net, "layer": a.layer,
                "rect_um": [x1, y1, x2, y2]})

    if a.edit == "resize-plane":
        if not (a.layer and a.rect and a.old_rect):
            print("error: resize-plane needs --layer, --old-rect and --rect")
            return 2
        ox1, oy1, ox2, oy2 = rect4(a.old_rect)
        x1, y1, x2, y2 = rect4(a.rect)
        return edit_and_verify(
            design,
            RESIZE_IL.format(net=a.net, layer=a.layer, ox1=ox1, oy1=oy1,
                             ox2=ox2, oy2=oy2, x1=x1, y1=y1, x2=x2, y2=y2),
            VERIFY_SHAPE_IL.format(net=a.net, layer=a.layer,
                                   x1=x1, y1=y1, x2=x2, y2=y2),
            1, {"edit": "resize-plane", "net": a.net, "layer": a.layer,
                "old_rect_um": [ox1, oy1, ox2, oy2],
                "rect_um": [x1, y1, x2, y2]})

    if a.edit == "delete-plane":
        if not (a.layer and a.old_rect):
            print("error: delete-plane needs --layer and --old-rect")
            return 2
        ox1, oy1, ox2, oy2 = rect4(a.old_rect)
        return edit_and_verify(
            design,
            DELETE_IL.format(net=a.net, layer=a.layer,
                             ox1=ox1, oy1=oy1, ox2=ox2, oy2=oy2),
            VERIFY_GONE_IL.format(net=a.net, layer=a.layer,
                                  x1=ox1, y1=oy1, x2=ox2, y2=oy2),
            0, {"edit": "delete-plane", "net": a.net, "layer": a.layer,
                "old_rect_um": [ox1, oy1, ox2, oy2]})

    if a.edit == "add-via":
        if not (a.xy and a.padstack):
            print("error: add-via needs --xy and --padstack")
            return 2
        x, y = (float(v) for v in a.xy.split(","))
        return edit_and_verify(
            design,
            ADDVIA_IL.format(net=a.net, x=x, y=y, padstack=a.padstack),
            VERIFY_VIA_IL.format(net=a.net, x=x, y=y),
            1, {"edit": "add-via", "net": a.net, "xy_um": [x, y],
                "padstack": a.padstack})
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
