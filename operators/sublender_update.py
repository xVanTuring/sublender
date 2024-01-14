import bpy
from ..utils import consts, globalvar
from .. import async_loop
import datetime
import asyncio
import logging

log = logging.getLogger(__name__)


def fetch_status():
    import urllib.request
    import json
    try:
        with urllib.request.urlopen(consts.sublender_status_url) as response:
            data = response.read()
            json_str = str(data, encoding='utf-8')
            return json.loads(json_str)
    except Exception as e:
        log.exception("Error fetching sublender %s", e)
        return []


class SublenderOTCheckVersion(async_loop.AsyncModalOperatorMixin, bpy.types.Operator):
    bl_idname = "sublender.check_version"
    bl_label = "Check Version"
    bl_description = "Remove target image"
    task_id = "SublenderOTCheckVersion"

    async def async_execute(self, context):
        status = await asyncio.get_event_loop().run_in_executor(None, fetch_status)
        latest_info = status[0]
        latest_version = tuple(map(int, latest_info["version"].split(".")))
        preferences = context.preferences.addons["sublender"].preferences
        if latest_version > globalvar.version:
            preferences.latest_version = ",".join(map(str, latest_version))
            preferences.latest_changelog = latest_info["changelog"]
            self.report({"INFO"}, "Update Available")
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
            bpy.ops.sublender.check_version()


def register():
    bpy.utils.register_class(SublenderOTCheckVersion)


def unregister():
    bpy.utils.unregister_class(SublenderOTCheckVersion)
