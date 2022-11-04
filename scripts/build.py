import subprocess

result = subprocess.run(["git", "describe", "--tags"], stdout=subprocess.PIPE)
current_version = str(result.stdout, encoding="ascii").strip()
instr = input("Sbsarlite(default) or sbsarlite-dev(1):")
branch = "sbsarlite"
if instr == 1:
    branch = "sbsarlite-dev"
package_name = r"../sublender_sbsarlite_{0}.zip".format(current_version)
print("Writing {0}".format(package_name))
subprocess.run([
    "git", "archive", "--format", "zip",
    "--output", package_name, branch,
    "--prefix", "sublender/"
])
