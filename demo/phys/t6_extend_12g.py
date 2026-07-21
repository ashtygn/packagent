"""Stretch: same synthetic plane pair, sweep extended to 12 GHz to capture f10~7.15 GHz.

Rebuilds the t1_create.py structure from scratch (deterministic, zero design data),
adds the t5_syz.py ports, but with a 1 MHz - 12 GHz linear_count sweep (601 pts,
~20 MHz grid -> peak location to ~0.3%), writes the exec file, then solves headless:

    siwave_ng.exe plane_pair_12g.aedb plane_pair_12g.exec -formatOutput -useSubdir

Timebox: 400 s on the solve; on timeout the solver child (and only it) is killed
and the script exits 2 (skip cleanly). License draw: elec_solve_siwave (free seats).

Env required in-session:
    ANSYSEM_ROOT261=C:\\Program Files\\ANSYS Inc\\v261\\AnsysEM
    ANSYSLMD_LICENSE_FILE=<port>@<license-server>   (site-specific)

Usage: python t6_extend_12g.py [workdir]   (default: <script dir>\\ext12g)
"""

import os
import shutil
import subprocess
import sys
import time

TIMEBOX_S = 400
HERE = os.path.dirname(os.path.abspath(__file__))
WORK = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "ext12g")
AEDB = os.path.join(WORK, "plane_pair_12g.aedb")

t_all = time.perf_counter()
os.makedirs(WORK, exist_ok=True)
if os.path.exists(AEDB):
    shutil.rmtree(AEDB)

# ---- build (t1_create.py recipe, verbatim dims) -----------------------------
t0 = time.perf_counter()
from pyedb import Edb  # noqa: E402

edb = Edb(edbpath=AEDB, version="2026.1")
edb.materials.add_conductor_material("copper_probe", 5.8e7)
edb.materials.add_dielectric_material("FR4_probe", 4.4, 0.02)
for name, ltype, mat, th in [
    ("BOT", "signal", "copper", "35um"),
    ("D3", "dielectric", "FR4_probe", "200um"),
    ("L3", "signal", "copper", "17um"),
    ("D2", "dielectric", "FR4_probe", "200um"),
    ("L2", "signal", "copper", "17um"),
    ("D1", "dielectric", "FR4_probe", "200um"),
    ("TOP", "signal", "copper", "35um"),
]:
    edb.stackup.add_layer(name, layer_type=ltype, material=mat, thickness=th,
                          filling_material="FR4_probe")
edb.modeler.create_rectangle(layer_name="TOP", net_name="VDD",
                             lower_left_point=["0mm", "0mm"],
                             upper_right_point=["10mm", "10mm"])
edb.modeler.create_rectangle(layer_name="BOT", net_name="GND",
                             lower_left_point=["0mm", "0mm"],
                             upper_right_point=["10mm", "10mm"])

# ---- ports (t5_syz.py recipe) -----------------------------------------------
se = edb.excitation_manager
t_pos = se.create_point_terminal(0.005, 0.005, "TOP", "VDD", name="P1_VDD")
t_ref = se.create_point_terminal(0.005, 0.005, "BOT", "GND", name="P1_ref")
se.create_port(t_pos, t_ref, is_circuit_port=True, name="P1")
t_pos2 = se.create_point_terminal(0.001, 0.001, "TOP", "VDD", name="P2_VDD")
t_ref2 = se.create_point_terminal(0.001, 0.001, "BOT", "GND", name="P2_ref")
se.create_port(t_pos2, t_ref2, is_circuit_port=True, name="P2")
print("ports:", list(edb.ports.keys()))

# ---- extended sweep + exec ---------------------------------------------------
edb.simulation_setups.create_siwave_setup(
    name="syz_12g", distribution="linear_count",
    start_freq="1MHz", stop_freq="12GHz", step_freq=601)
exec_path = edb.siwave.create_exec_file(add_syz=True, export_touchstone=True)
txt = open(exec_path).read()
with open(exec_path, "w") as f:
    f.write("SetNumCpus 4\n" + txt)
edb.save()
edb.close()
print(f"WALL build EDB: {time.perf_counter() - t0:.1f}s")
print("exec file:", exec_path)

# ---- headless solve, timeboxed ----------------------------------------------
siwave_ng = os.path.join(os.environ["ANSYSEM_ROOT261"], "siwave_ng.exe")
cmd = [siwave_ng, AEDB, exec_path, "-formatOutput", "-useSubdir"]
print("solve:", " ".join(cmd))
t0 = time.perf_counter()
try:
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=TIMEBOX_S)
except subprocess.TimeoutExpired:
    print(f"SOLVE TIMEBOX ({TIMEBOX_S}s) EXCEEDED - solver killed, skipping "
          f"cleanly (1 MHz-1 GHz beat still stands)")
    sys.exit(2)
wall = time.perf_counter() - t0
print(f"WALL siwave_ng solve: {wall:.1f}s  exit={r.returncode}")
if r.returncode != 0:
    print("--- stdout tail ---\n" + r.stdout[-2000:])
    print("--- stderr tail ---\n" + r.stderr[-2000:])
    sys.exit(1)

s2p = os.path.join(WORK, "plane_pair_12g_touchstone.s2p")
print("touchstone exists:", os.path.isfile(s2p), "->", s2p)
print(f"WALL t6 total: {time.perf_counter() - t_all:.1f}s")
print("T6 DONE")
