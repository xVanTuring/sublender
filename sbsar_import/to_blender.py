import asyncio

import bpy

from .helper_class import EvalDelegate
from .to_dict import load_sbsar_to_dict_async
from .. import preference, parser, globalvar, consts, property_group


async def load_sbsars_async(report=None):
    preferences = preference.get_preferences()
    sb_materials = []
    sbs_package_set = set()

    for material in bpy.data.materials:
        # filter material
        m_sublender = material.sublender
        if (
                (m_sublender is not None)
                and (m_sublender.graph_url != "")
                and (m_sublender.package_path != "")
        ):
            m_sublender.package_loaded = False
            sb_materials.append(material)
            sbs_package_set.add(m_sublender.package_path)
    load_queue = []
    for fp in sbs_package_set:
        load_queue.append(load_sbsar_to_dict_async(fp, report))
    await asyncio.gather(*load_queue)
    for material in sb_materials:
        m_sublender = material.sublender
        await gen_clss_from_material_async(
            material, preferences.enable_visible_if, False, report
        )
        m_sublender.package_loaded = True


async def gen_clss_from_material_async(
        target_material, enable_visible_if, force_reload=False, report=None
):
    m_sublender = target_material.sublender
    if force_reload:
        await load_sbsar_to_dict_async(m_sublender.package_path)
    sbs_package = globalvar.sbsar_dict.get(m_sublender.package_path)

    if sbs_package is not None:
        sbs_graph: parser.sbsarlite.SbsarGraphData | None = None
        for graph in sbs_package.graphs:
            if graph.pkgUrl == m_sublender.graph_url:
                sbs_graph = graph
        assert sbs_graph is not None
        clss_name, _ = property_group.ensure_graph_property_group(sbs_graph, m_sublender.graph_url)
        m_sublender.package_missing = False
        if enable_visible_if:
            globalvar.eval_delegate_map[
                target_material.name
            ] = EvalDelegate(target_material.name, clss_name)
        graph_setting = getattr(target_material, clss_name)
        setattr(graph_setting, consts.SBS_CONFIGURED, True)
        if report is not None:
            report({"INFO"}, "Graph {0} is loaded".format(m_sublender.graph_url))
    else:
        m_sublender.package_missing = True
        if report is not None:
            report(
                {"WARNING"},
                "Package is missing or corrupted: {0}".format(m_sublender.package_path),
            )
