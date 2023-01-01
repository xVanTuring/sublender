import subprocess
import pathlib

result = subprocess.run(["git", "describe", "--tags"], stdout=subprocess.PIPE)
current_version = str(result.stdout, encoding="ascii").strip()
instr = input("Sbsarlite(default) or sbsarlite-dev(1):")
branch = "sbsarlite"
if instr == 1:
    branch = "sbsarlite-dev"
package_name = pathlib.Path("../sublender_{0}.zip".format(current_version)).resolve()

print("Writing {0}".format(package_name))
subprocess.run(
    ["git", "archive", "--format", "zip", "--output", package_name, branch, "--prefix", "sublender/"])

package_mirror_name = pathlib.Path("../sublender_{0}_cn_mirror.zip".format(current_version)).resolve()
print("Writing {0}".format(package_mirror_name))
subprocess.run(
    ["git", "archive", "--format", "zip", "--output", package_mirror_name, branch, "--prefix", "sublender/"])
patched_path = "/tmp/sublender/install_lib.py"
pathlib.Path("/tmp/sublender").mkdir(parents=True, exist_ok=True)
subprocess.run(["patch", "./install_lib.py", "./scripts/install_lib.patch", "-o", patched_path])
subprocess.run([
    "zip",
    package_mirror_name,
    "./sublender/install_lib.py",
], cwd="/tmp")
