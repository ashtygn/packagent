"""Probe 1: synthetic 4-layer plane-pair EDB from scratch (pyedb 0.80.2, gRPC backend)."""
import os
import shutil
import sys
import traceback

SCRATCH = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "out")
os.makedirs(SCRATCH, exist_ok=True)
AEDB = os.path.join(SCRATCH, "plane_pair.aedb")
if os.path.exists(AEDB):
    shutil.rmtree(AEDB)

from pyedb import Edb

print("STEP: Edb() create ...")
edb = Edb(edbpath=AEDB, version="2026.1")
print("  OK backend class:", type(edb).__module__ + "." + type(edb).__name__)
print("  edbpath:", edb.edbpath)

# --- materials ---
try:
    m = edb.materials.add_conductor_material("copper_probe", 5.8e7)
    print("STEP materials.add_conductor_material('copper_probe', 5.8e7): OK ->", m.name)
except Exception as e:
    print("STEP materials.add_conductor_material FAILED:", repr(e))

try:
    m = edb.materials.add_dielectric_material("FR4_probe", 4.4, 0.02)
    print("STEP materials.add_dielectric_material('FR4_probe', 4.4, 0.02): OK ->", m.name)
except Exception as e:
    print("STEP materials.add_dielectric_material FAILED:", repr(e))

# --- stackup: 4 metal layers, manual add_layer (note: 0.80.2 kw is filling_material) ---
layers = [
    ("BOT", "signal", "copper", "35um"),
    ("D3", "dielectric", "FR4_probe", "200um"),
    ("L3", "signal", "copper", "17um"),
    ("D2", "dielectric", "FR4_probe", "200um"),
    ("L2", "signal", "copper", "17um"),
    ("D1", "dielectric", "FR4_probe", "200um"),
    ("TOP", "signal", "copper", "35um"),
]
for name, ltype, mat, th in layers:
    try:
        r = edb.stackup.add_layer(
            name, layer_type=ltype, material=mat, thickness=th, filling_material="FR4_probe"
        )
        print(f"STEP stackup.add_layer({name}, {ltype}, {mat}, {th}): OK ->", r)
    except Exception as e:
        print(f"STEP stackup.add_layer({name}) FAILED:", repr(e))
        traceback.print_exc()

print("Stackup layers now:", list(edb.stackup.layers.keys()))

# --- planes: two overlapping 10x10 mm rectangles ---
try:
    r1 = edb.modeler.create_rectangle(
        layer_name="TOP",
        net_name="VDD",
        lower_left_point=["0mm", "0mm"],
        upper_right_point=["10mm", "10mm"],
    )
    print("STEP modeler.create_rectangle TOP/VDD: OK ->", r1, type(r1).__name__)
except Exception as e:
    print("STEP create_rectangle TOP/VDD FAILED:", repr(e))
    traceback.print_exc()

try:
    r2 = edb.modeler.create_rectangle(
        layer_name="BOT",
        net_name="GND",
        lower_left_point=["0mm", "0mm"],
        upper_right_point=["10mm", "10mm"],
    )
    print("STEP modeler.create_rectangle BOT/GND: OK ->", r2, type(r2).__name__)
except Exception as e:
    print("STEP create_rectangle BOT/GND FAILED:", repr(e))
    traceback.print_exc()

print("Nets now:", list(edb.nets.netlist))
print("Primitive count:", len(edb.layout.primitives))

print("STEP save ...")
print("  save() ->", edb.save())
print("STEP close ...")
print("  close() ->", edb.close())
print("AEDB exists on disk:", os.path.isdir(AEDB), "-> contents:", os.listdir(AEDB) if os.path.isdir(AEDB) else "N/A")
print("T1 DONE")
