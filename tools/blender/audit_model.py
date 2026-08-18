"""Write a read-only structural audit of Blender mesh objects."""

from __future__ import annotations

import argparse
import json
import sys
import traceback
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector


def blender_arguments() -> list[str]:
    return sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit Blender model structure without editing it.")
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument(
        "--object",
        action="append",
        dest="objects",
        help="Mesh object to audit; repeat as needed. Defaults to every scene mesh.",
    )
    parser.add_argument(
        "--merge-distance",
        action="append",
        dest="merge_distances",
        type=float,
        default=[],
        help="Probe merge-by-distance on an in-memory mesh copy; repeat as needed.",
    )
    return parser.parse_args(blender_arguments())


def rounded(values) -> list[float]:
    return [round(float(value), 6) for value in values]


def world_bounds(obj) -> dict | None:
    points = [obj.matrix_world @ vertex.co for vertex in obj.data.vertices]
    if not points:
        return None
    low = Vector(
        (
            min(point.x for point in points),
            min(point.y for point in points),
            min(point.z for point in points),
        )
    )
    high = Vector(
        (
            max(point.x for point in points),
            max(point.y for point in points),
            max(point.z for point in points),
        )
    )
    return {"min": rounded(low), "max": rounded(high), "dimensions": rounded(high - low)}


def topology_stats(bm) -> dict:
    bm.verts.ensure_lookup_table()
    seen = set()
    components = []
    for start in bm.verts:
        if start.index in seen:
            continue
        stack = [start]
        seen.add(start.index)
        count = 0
        while stack:
            vertex = stack.pop()
            count += 1
            for edge in vertex.link_edges:
                other = edge.other_vert(vertex)
                if other.index not in seen:
                    seen.add(other.index)
                    stack.append(other)
        components.append(count)
    components.sort(reverse=True)
    return {
        "vertices": len(bm.verts),
        "edges": len(bm.edges),
        "faces": len(bm.faces),
        "components": len(components),
        "largestComponentVertices": components[:30],
        "looseVertices": sum(1 for vertex in bm.verts if not vertex.link_edges),
        "boundaryEdges": sum(1 for edge in bm.edges if edge.is_boundary),
        "nonManifoldEdges": sum(1 for edge in bm.edges if not edge.is_manifold),
    }


def probe_topology(mesh, distances: list[float]) -> tuple[dict, dict[str, dict]]:
    base = bmesh.new()
    try:
        base.from_mesh(mesh)
        original = topology_stats(base)
        probes = {}
        for distance in distances:
            if distance <= 0.0:
                raise ValueError("Merge probe distances must be positive")
            candidate = base.copy()
            try:
                bmesh.ops.remove_doubles(candidate, verts=list(candidate.verts), dist=distance)
                probes[str(distance)] = topology_stats(candidate)
            finally:
                candidate.free()
        return original, probes
    finally:
        base.free()


def material_report(material) -> dict | None:
    if material is None:
        return None
    images = []
    if material.use_nodes and material.node_tree:
        for node in material.node_tree.nodes:
            image = getattr(node, "image", None)
            if image is not None:
                images.append(
                    {
                        "name": image.name,
                        "filepath": bpy.path.abspath(image.filepath),
                        "source": image.source,
                        "packed": image.packed_file is not None,
                        "size": list(image.size),
                    }
                )
    return {
        "name": material.name,
        "useNodes": material.use_nodes,
        "surfaceRenderMethod": getattr(material, "surface_render_method", None),
        "doubleSided": not material.use_backface_culling,
        "images": images,
    }


def audit_object(obj, distances: list[float]) -> dict:
    mesh = obj.data
    mesh.calc_loop_triangles()
    original, probes = probe_topology(mesh, distances)
    max_influences = 0
    unweighted = 0
    if obj.vertex_groups:
        for vertex in mesh.vertices:
            influences = sum(membership.weight > 0.0 for membership in vertex.groups)
            max_influences = max(max_influences, influences)
            unweighted += influences == 0
    unsupported = []
    if len(mesh.uv_layers) > 1:
        unsupported.append("additional UV sets")
    if mesh.color_attributes:
        unsupported.append("vertex colors")
    if mesh.shape_keys:
        unsupported.append("morph targets")
    if any(len(polygon.vertices) != 3 for polygon in mesh.polygons):
        unsupported.append("non-triangle authoring faces")

    return {
        "name": obj.name,
        "mesh": mesh.name,
        "location": rounded(obj.location),
        "rotationEulerDegrees": rounded(value * 57.29577951308232 for value in obj.rotation_euler),
        "scale": rounded(obj.scale),
        "matrixWorld": [rounded(row) for row in obj.matrix_world],
        "parent": obj.parent.name if obj.parent else None,
        "worldBounds": world_bounds(obj),
        "triangles": len(mesh.loop_triangles),
        "ngons": sum(len(polygon.vertices) > 4 for polygon in mesh.polygons),
        "topology": original,
        "mergeByDistanceProbes": probes,
        "uvLayers": [layer.name for layer in mesh.uv_layers],
        "colorAttributes": [attribute.name for attribute in mesh.color_attributes],
        "shapeKeys": list(mesh.shape_keys.key_blocks.keys()) if mesh.shape_keys else [],
        "materials": [material_report(slot.material) for slot in obj.material_slots],
        "modifiers": [
            {
                "name": modifier.name,
                "type": modifier.type,
                "object": getattr(getattr(modifier, "object", None), "name", None),
            }
            for modifier in obj.modifiers
        ],
        "vertexGroups": [group.name for group in obj.vertex_groups],
        "maxVertexInfluences": max_influences,
        "unweightedVertices": unweighted if obj.vertex_groups else None,
        "unsupportedOrReviewRequired": unsupported,
    }


def main() -> None:
    args = parse_args()
    output = args.output.resolve()
    if output.suffix.lower() != ".json":
        raise ValueError("Audit output must use the .json extension")
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite audit report: {output}")

    scene_meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    if args.objects:
        selected = []
        for name in args.objects:
            obj = bpy.data.objects.get(name)
            if obj is None or obj.type != "MESH":
                raise ValueError(f"Mesh object does not exist: {name!r}")
            selected.append(obj)
    else:
        selected = scene_meshes
    if not selected:
        raise ValueError("The scene contains no mesh objects to audit")

    report = {
        "blendFile": bpy.data.filepath or None,
        "scene": bpy.context.scene.name,
        "frame": bpy.context.scene.frame_current,
        "unitSettings": {
            "system": bpy.context.scene.unit_settings.system,
            "scaleLength": bpy.context.scene.unit_settings.scale_length,
            "lengthUnit": bpy.context.scene.unit_settings.length_unit,
        },
        "armatures": [obj.name for obj in bpy.context.scene.objects if obj.type == "ARMATURE"],
        "objects": [audit_object(obj, args.merge_distances) for obj in selected],
        "note": "Structural diagnostics complement but do not replace visual inspection.",
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("AMMUNAE_MODEL_AUDIT=" + json.dumps(report, separators=(",", ":")))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
