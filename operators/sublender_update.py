import bpy
from bpy.types import Operator
from ..utils import consts, globalvar
from .. import async_loop
import datetime


async def fetch_status():
    if "aiohttp" not in globals():
        import aiohttp
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(consts.sublender_status_url) as resp:
                return await resp.json()
        # blender build-in python requires ssl=False
        except aiohttp.client_exceptions.ClientConnectorError as e:
            print(e)
            async with session.get(consts.sublender_status_url, ssl=False) as resp:
                return await resp.json()
        except aiohttp.client_exceptions.ClientConnectorError as e:
            # UX
            pass


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
        print(latest_version, globalvar.version)
        if latest_version > globalvar.version:
            preferences.latest_version = ",".join(map(str, latest_version))
            preferences.latest_changelog = latest_info["changelog"]
            self.report({"INFO"}, "Update Avaliable")
        else:
            preferences.latest_version = ""
            preferences.latest_changelog = latest_info["changelog"]
        preferences.last_check = datetime.datetime.now().timestamp()


def auto_check():
    preferences = bpy.context.preferences.addons["sublender"].preferences
    if preferences.auto_check_every_day:
        last_check_stamp = preferences.last_check
        now = datetime.datetime.now()
        last_check_datetime = datetime.datetime.fromtimestamp(last_check_stamp)
        if (now - last_check_datetime) > datetime.timedelta(hours=12):
            print("Checking Update Now")
            bpy.ops.sublender.check_version()


def register():
    bpy.utils.register_class(SublenderOTCheckVersion)


def unregister():
    bpy.utils.unregister_class(SublenderOTCheckVersion)