import sys, os
import pathlib
import ctypes, sys
import subprocess
import glob
import bpy

print("Thank you for using Sublender")
default_sat = r"C:\Program Files\Allegorithmic\Substance Automation Toolkit"
sat = input("SAT Path({0}):".format(default_sat))

if sat == "":
    sat = default_sat
pysbs_dir = os.path.join(sat, "Python API")
pysbs_full_path = None
for f in os.listdir(pysbs_dir):
    if f.endswith('.zip'):
        pysbs_full_path = os.path.join(pysbs_dir, f)
if pysbs_full_path is None:
    exit()

_, blender_name = os.path.split(pathlib.Path(sys.executable).parent)
_, version = blender_name.split(" ")
bundled_py = str(pathlib.Path(sys.executable).parent.joinpath(version, "python", "bin", "python.exe"))
subprocess.run([bundled_py, "-m", "pip", "install", pysbs_full_path])

# https://blender.stackexchange.com/questions/73759/install-addons-in-headless-blender
# bpy.ops.preferences.addon_install(filepath=r"E:\sublender_v1.0.1-1-g648968d.zip")
# bpy.ops.preferences.addon_enable(module='sublender')
# bpy.ops.wm.save_userpref()
