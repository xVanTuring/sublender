import os
import subprocess
import sys

deps = ["py7zr", "xmltodict", "platformdirs"]


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
    "macos_x64": "macosx_11_0_x86_64",
    "macos_arm64": "macosx_11_0_arm64",
}


def remove_previous_whl(wheel_dir: str):
    for file in os.listdir(wheel_dir):
        if file.endswith(".whl"):
            os.remove(os.path.join(wheel_dir, file))


def download(wheel_dir: str, platform_key: str, python_version: str):
    remove_previous_whl(wheel_dir)
    if platform_key not in platform_env:
        print(f"Unable to pack for platform {platform_key}")
        return
    platform = platform_env[platform_key]

    for dep in deps:
        download_deps(dep, wheel_dir, platform, python_version)


if __name__ == "__main__":
    wheel_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../", "wheels")
    )
    python_version = os.environ.get("BLENDER_PY_VERSION") or "310"
    platform = os.environ.get("PLATFORM") or "windows"
    arch = os.environ.get("ARCH") or "x64"
    platform_key = f"{platform}_{arch}"

    download(
        wheel_dir=wheel_dir, platform_key=platform_key, python_version=python_version
    )
