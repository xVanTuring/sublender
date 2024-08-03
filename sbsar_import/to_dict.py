import asyncio
import os

from .. import parser, globalvar


async def load_sbsar_to_dict_async(
        filepath: str, report=None
) -> parser.SbsarPackageData:
    basename = os.path.basename(filepath)

    if report is not None:
        report({"INFO"}, f"Parsing sbsar {basename}")
    loop = asyncio.get_event_loop()
    sbs_package = await loop.run_in_executor(None, parse_sbsar_package, filepath)
    globalvar.sbsar_dict[filepath] = sbs_package
    if report is not None:
        report({"INFO"}, f"Package {basename} is parsed")
    return sbs_package


async def load_sbsar_to_dict_with_path_async(filepath: str, report=None):
    return filepath, await load_sbsar_to_dict_async(filepath, report)


def parse_sbsar_package(filepath: str) -> parser.sbsarlite.SbsarPackageData | None:
    if not os.path.exists(filepath):
        return None
    return parser.sbsarlite.parse_doc(filepath)
