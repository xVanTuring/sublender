import subprocess

result = subprocess.run(["git", "describe", "--tags"], stdout=subprocess.PIPE)
current_version = str(result.stdout, encoding="ascii").strip()
instr = input("Master(default) or Dev(1):")
branch = "master"
if instr == 1:
    branch = "dev"
package_name = r"..\sublender_{0}.zip".format(current_version)
print("Writing {0}".format(package_name))
subprocess.run([
    "git", "archive", "--format", "zip",
    "--output", package_name, branch,
    "--prefix", "sublender/"
])
