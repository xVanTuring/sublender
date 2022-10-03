import sys

print("Thank you for using Sublender")
default_sat = r"C:\Program Files\Allegorithmic\Substance Automation Toolkit"
sat = input("SAT Path({0}):".format(default_sat))
print(sat)
print(sys.executable)
# https://blender.stackexchange.com/questions/73759/install-addons-in-headless-blender

# bpy.ops.wm.addon_install(filepath='/home/shane/Downloads/testaddon.py')
# bpy.ops.wm.addon_enable(module='testaddon')
# bpy.ops.wm.save_userpref()
