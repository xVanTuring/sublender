import bpy
from bpy.types import Operator
from ..utils import consts, globalvar
from .. import async_loop
import aiohttp


async def fetch_status():
    async with aiohttp.ClientSession() as session:
        async with session.get(consts.sublender_status_url, ssl=False) as resp:
            return await resp.json()


class SublenderOTCheckVersion(async_loop.AsyncModalOperatorMixin, Operator):
    bl_idname = "sublender.check_version"
    bl_label = "Check Version"
    bl_description = "Remove target image"
    task_id = "SublenderOTCheckVersion"

    async def async_execute(self, context):
        status = await fetch_status()
        latest_info = status[0]
        latest_version = tuple(map(int, latest_info["version"].split(".")))
        preferences = context.preferences.addons["sublender"].preferences
        if latest_version > globalvar.version:
            # Compare at start
            preferences.latest_version = ",".join(map(str, latest_version))
            preferences.latest_changelog = latest_info["changelog"]
        else:
            preferences.latest_version = ""
            preferences.latest_changelog = latest_info["changelog"]


def register():
    bpy.utils.register_class(SublenderOTCheckVersion)


def unregister():
    bpy.utils.unregister_class(SublenderOTCheckVersion)