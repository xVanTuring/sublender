import subprocess
import pathlib

result = subprocess.run(["git", "describe", "--tags"], stdout=subprocess.PIPE)
current_version = str(result.stdout, encoding="ascii").strip()
instr = int(input("Sbsarlite(default) or sbsarlite-dev(1):"))
branch = "sbsarlite"
install_lib_base_path = "./utils/install_lib.py"
if instr == 1:
    branch = "sbsarlite-dev"
package_name = pathlib.Path("../sublender_{0}.zip".format(current_version)).resolve()

print("Writing {0}".format(package_name))
subprocess.run(["git", "archive", "--format", "zip", "--output", package_name, branch, "--prefix", "sublender/"])

package_mirror_name = pathlib.Path("../sublender_{0}_cn_mirror.zip".format(current_version)).resolve()
print("Writing {0}".format(package_mirror_name))
subprocess.run(
    ["git", "archive", "--format", "zip", "--output", package_mirror_name, branch, "--prefix", "sublender/"])
patched_path = str(pathlib.Path("/tmp/sublender/", install_lib_base_path))
pathlib.Path("/tmp/sublender/utils").mkdir(parents=True, exist_ok=True)
with open(install_lib_base_path, "r") as basefile:
    content = basefile.read()
    content = content.replace('run_pip("--upgrade", "pip")','run_pip("--upgrade", "pip", "-i", "https://pypi.tuna.tsinghua.edu.cn/simple")') \
                        .replace('run_pip("wheel")','run_pip("wheel", "-i", "https://pypi.tuna.tsinghua.edu.cn/simple")') \
                        .replace('run_pip("py7zr")','run_pip("py7zr", "-i", "https://pypi.tuna.tsinghua.edu.cn/simple")') \
                        .replace('run_pip("xmltodict")', 'run_pip("xmltodict", "-i", "https://pypi.tuna.tsinghua.edu.cn/simple")')
    with open(patched_path, "w") as updatingfile:
        updatingfile.write(content)
subprocess.run([
    "zip",
    package_mirror_name,
    str(pathlib.Path("./sublender/", install_lib_base_path)),
], cwd="/tmp")
