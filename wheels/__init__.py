# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

"""External dependencies loader."""

import glob
import os.path
import sys
import logging
import zipfile

my_dir = os.path.join(os.path.dirname(__file__))
log = logging.getLogger(__name__)


def load_wheel(module_name, fname_prefix):
    """Loads a wheel from 'fname_prefix*.whl', unless the named module can be imported.

    This allows us to use system-installed packages before falling back to the shipped wheels.
    This is useful for development, less so for deployment.
    """

    try:
        module = __import__(module_name)
    except ImportError as ex:
        log.debug("Unable to import %s directly, will try wheel: %s", module_name, ex)
    else:
        log.debug(
            "Was able to load %s from %s, no need to load wheel %s",
            module_name,
            module.__file__,
            fname_prefix,
        )
        return

    sys.path.append(wheel_filename(fname_prefix))
    module = __import__(module_name)
    log.debug("Loaded %s from %s", module_name, module.__file__)


def wheel_filename(fname_prefix: str) -> str:
    path_pattern = os.path.join(my_dir, "%s*.whl" % fname_prefix)
    wheels = glob.glob(path_pattern)
    if not wheels:
        raise RuntimeError("Unable to find wheel at %r" % path_pattern)

    # If there are multiple wheels that match, load the last-modified one.
    # Alphabetical sorting isn't going to cut it since BAT 1.10 was released.
    def modtime(filename: str) -> float:
        return os.stat(filename).st_mtime

    wheels.sort(key=modtime)
    return wheels[-1]


def load_wheels():
    load_wheel("platformdirs", "platformdirs")

    import platformdirs

    cache_folder = platformdirs.user_cache_dir("Sublender", ensure_exists=True)
    deps_fodler = os.path.join(cache_folder, "dependencies")
    if not os.path.exists(deps_fodler):
        os.mkdir(deps_fodler)

    sys.path.append(deps_fodler)
    load_wheels_unpack("bcj", "pybcj", deps_fodler)
    load_wheels_unpack("psutil", "psutil", deps_fodler)
    load_wheels_unpack("pyppmd", "pyppmd", deps_fodler)
    load_wheels_unpack("pyzstd", "pyzstd", deps_fodler)
    load_wheels_unpack("brotli", "Brotli", deps_fodler)
    load_wheels_unpack("Cryptodome", "pycryptodomex", deps_fodler)
    load_wheels_unpack("texttable", "texttable", deps_fodler)
    load_wheels_unpack("inflate64", "inflate64", deps_fodler)
    load_wheels_unpack("multivolumefile", "multivolumefile", deps_fodler)

    load_wheel("py7zr", "py7zr")
    load_wheel("xmltodict", "xmltodict")


def load_wheels_unpack(module_name: str, fname_prefix: str, dep_unzip_folder: str):
    """Loads a wheel from 'fname_prefix*.whl', unless the named module can be imported.

    This allows us to use system-installed packages before falling back to the shipped wheels.
    This is useful for development, less so for deployment.
    """

    try:
        module = __import__(module_name)
    except ImportError as ex:
        log.debug("Unable to import %s directly, will try wheel: %s", module_name, ex)
    else:
        log.debug(
            "Was able to load %s from %s, no need to load wheel %s",
            module_name,
            module.__file__,
            fname_prefix,
        )
        return
    wheel_file = wheel_filename(fname_prefix)

    targetDir = os.path.join(dep_unzip_folder, module_name)
    if not os.path.exists(targetDir):
        with zipfile.ZipFile(wheel_file, "r") as whl:
            whl.extractall(dep_unzip_folder)
    module = __import__(module_name)
    log.debug("Loaded %s from %s", module_name, module.__file__)


if __name__ == "__main__":
    wheel = wheel_filename("xmltodict")
    print(f"Wheel: {wheel}")
