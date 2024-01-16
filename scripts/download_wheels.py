import os
import subprocess
import sys

deps = ["py7zr", "xmltodict"]


# https://packaging.python.org/en/latest/specifications/platform-compatibility-tags/
#  pip download py7zr --platform win_amd64 --platform any --python-version 310 --only-binary=:all:
# pip download py7zr --platform manylinux2014_x86_64 --platform any --python-version 310 --only-binary=:all:


def download_deps(dep_name: str, target_dir: str, platform: str, python_version: str):
    args = [
        sys.executable,
        "-m",
        "pip",
        "download",
        dep_name,
        "--platform",
        platform,
        "--platform",
        "any",
        "--python-version",
        python_version,
        "--only-binary=:all:",
        "-d",
        target_dir,
    ]
    subprocess.run(args)


platform_env = {
    "windows_x64": "win_amd64",
    "linux_x64": "manylinux2014_x86_64",
    "macos_x64": "",
    "macos_arm": "",
}


def remove_previous_whl(wheel_dir: str):
    for file in os.listdir(wheel_dir):
        if file.endswith(".whl"):
            os.remove(os.path.join(wheel_dir, file))


if __name__ == "__main__":
    wheel_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../", "wheels")
    )
    remove_previous_whl(wheel_dir)

    platform = os.environ.get("PLATFORM") or "windows"
    arch = os.environ.get("ARCH") or "x64"
    platform_key = f"{platform}_{arch}"
    if platform_key not in platform_env:
        exit()
    platform = platform_env[platform_key]

    python_version = os.environ.get("BLENDER_PY_VERSION") or "310"

    for dep in deps:
        download_deps(dep, wheel_dir, platform, python_version)
