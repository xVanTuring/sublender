import sys
import os
import subprocess


def download_dep(dep_name: str, target_dir: str):
    args = [
        sys.executable,
        "-m",
        "pip",
        "wheel",
        dep_name,
        "-w",
        target_dir,
    ]
    subprocess.run(args)


deps = ["ppmd-cffi==0.5.0", "bcj-cffi==0.5.1", "py7zr==0.20.8", "xmltodict==0.13.0", "platformdirs==4.1.0"]


def download_all(wheel_dir: str):
    for dep in deps:
        download_dep(dep, wheel_dir)
