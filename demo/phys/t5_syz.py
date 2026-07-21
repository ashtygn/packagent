"""Probe 5a: add ports + SYZ setup + exec file on the synthetic plane pair."""
import os
import sys
import traceback

AEDB = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "out", "plane_pair.aedb")
from pyedb import Edb

edb = Edb(edbpath=AEDB, version="2026.1")
print("Opened:", edb.edbpath)

se = edb.excitation_manager
print("excitation_manager:", type(se).__name__)

# port 1: point terminal VDD on TOP vs GND on BOT at plane center
try:
    t_pos = se.create_point_terminal(0.005, 0.005, "TOP", "VDD", name="P1_VDD")
    t_ref = se.create_point_terminal(0.005, 0.005, "BOT", "GND", name="P1_ref")
    port = se.create_port(t_pos, t_ref, is_circuit_port=True, name="P1")
    print("STEP create_point_terminal x2 + create_port(P1, circuit): OK ->", port, type(port).__name__)
except Exception as e:
    print("STEP port P1 FAILED:", repr(e))
    traceback.print_exc()

# port 2 near a corner, for a 2-port S-matrix
try:
    t_pos2 = se.create_point_terminal(0.001, 0.001, "TOP", "VDD", name="P2_VDD")
    t_ref2 = se.create_point_terminal(0.001, 0.001, "BOT", "GND", name="P2_ref")
    port2 = se.create_port(t_pos2, t_ref2, is_circuit_port=True, name="P2")
    print("STEP create_port(P2, circuit): OK ->", port2, type(port2).__name__)
except Exception as e:
    print("STEP port P2 FAILED:", repr(e))
    traceback.print_exc()

print("Ports now:", list(edb.ports.keys()))

# SYZ setup: 10 points, 1MHz - 1GHz linear_count
try:
    setup = edb.simulation_setups.create_siwave_setup(
        name="syz_probe",
        distribution="linear_count",
        start_freq="1MHz",
        stop_freq="1GHz",
        step_freq=10,
    )
    print("STEP simulation_setups.create_siwave_setup(linear_count 1MHz-1GHz n=10): OK ->", type(setup).__name__)
    try:
        for sw_name, sw in setup.sweep_data.items() if isinstance(setup.sweep_data, dict) else []:
            print("  sweep:", sw_name, sw)
    except Exception:
        pass
except Exception as e:
    print("STEP create_siwave_setup FAILED:", repr(e))
    traceback.print_exc()

# exec file via API
try:
    exec_path = edb.siwave.create_exec_file(add_syz=True, export_touchstone=True)
    print("STEP siwave.create_exec_file(add_syz, export_touchstone): OK ->", exec_path)
    txt = open(exec_path).read()
    # prepend cpu count
    with open(exec_path, "w") as f:
        f.write("SetNumCpus 4\n" + txt)
    print("---- exec file content ----")
    print(open(exec_path).read())
except Exception as e:
    print("STEP create_exec_file FAILED:", repr(e))
    traceback.print_exc()

print("save() ->", edb.save())
print("close() ->", edb.close())
print("T5A DONE")
