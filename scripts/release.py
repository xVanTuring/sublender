import os
import pathlib
import subprocess
import download_wheels
import zipfile

matrix = {"windows": ["x64"], "linux": ["x64"], "macos": ["x64", "arm64"]}
blender_matrix = {"310": "bl3.3-bl4.0"}
project_path = pathlib.Path(__file__).parent.parent.absolute()
wheel_dir = project_path.joinpath("wheels")
dist_path = project_path.joinpath("dist")


def do_pack(wheel_dir: pathlib.Path, dist_path: pathlib.Path, platform_key: str):
    branch = "dev"
    for python_version, blender_version in blender_matrix.items():
        print(f"Download deps for {python_version}")
        download_wheels.download(str(wheel_dir), platform_key, python_version)
        packing_file = f"sublender-{blender_version}-{platform_key}.zip"
        print(f"Packing for {packing_file}")
        packing_file = str(dist_path.joinpath(packing_file))
        subprocess.run(
            [
                "git",
                "archive",
                "--format",
                "zip",
                "--output",
                packing_file,
                branch,
                "--prefix",
                "sublender/",
            ]
        )

        wheels = list(
            map(
                lambda x: str(wheel_dir.joinpath(x)),
                filter(lambda x: x.endswith(".whl"), os.listdir(wheel_dir)),
            )
        )
        for wheel in wheels:
            with zipfile.ZipFile(packing_file, "a") as zfile:
                zfile.write(wheel, f"sublender/wheels/{os.path.basename(wheel)}")


if __name__ == "__main__":
    print(f"Project is located at {str(project_path)}")
    if not dist_path.exists():
        print(f"Creating dist_folder at {dist_path}")
        os.mkdir(dist_path)

    for platform, arches in matrix.items():
        for arch in arches:
            platform_key = f"{platform}_{arch}"
            do_pack(wheel_dir, dist_path, platform_key)
