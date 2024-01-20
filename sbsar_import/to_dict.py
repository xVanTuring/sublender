import asyncio
import os

from .. import parser, globalvar


async def load_sbsar_to_dict_async(
        filepath: str, report=None
) -> parser.SbsarPackageData:
    if report is not None:
        print("Parsing sbsar {0}".format(filepath))
        report({"INFO"}, "Parsing sbsar {0}".format(filepath))
    loop = asyncio.get_event_loop()
    sbs_package = await loop.run_in_executor(None, parse_sbsar_package, filepath)
    globalvar.sbsar_dict[filepath] = sbs_package
    if report is not None:
        report({"INFO"}, "Package {0} is parsed".format(filepath))
        print("Package {0} is parsed".format(filepath))
    return sbs_package


def parse_sbsar_package(filepath: str) -> parser.sbsarlite.SbsarPackageData | None:
    if not os.path.exists(filepath):
        return None
    return parser.sbsarlite.parse_doc(filepath)
