"""Normalize one unrigged Blender mesh to Ammunae orientation and scale."""

from __future__ import annotations

import argparse
import json
import math
import sys
import traceback
from pathlib import Path

import bpy
from mathutils import Matrix, Vector


AXIS_VECTORS = {
    "+X": Vector((1.0, 0.0, 0.0)),
    "-X": Vector((-1.0, 0.0, 0.0)),
    "+Y": Vector((0.0, 1.0, 0.0)),
    "-Y": Vector((0.0, -1.0, 0.0)),
    "+Z": Vector((0.0, 0.0, 1.0)),
    "-Z": Vector((0.0, 0.0, -1.0)),
}
TARGET_FORWARD = Vector((0.0, -1.0, 0.0))
TARGET_UP = Vector((0.0, 0.0, 1.0))


def blender_arguments() -> list[str]:
    return sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Orient, ground, center, and uniformly scale an unrigged mesh."
    )
    parser.add_argument("--object", help="Mesh object; optional only when the scene has one mesh")
    parser.add_argument("--source-forward", required=True, choices=sorted(AXIS_VECTORS))
    parser.add_argument("--source-up", required=True, choices=sorted(AXIS_VECTORS))
    parser.add_argument("--height", type=float, default=64.0)
    parser.add_argument("--output", required=True, type=Path, help="New .blend output path")
    parser.add_argument("--report", type=Path, help="Optional JSON report")
    return parser.parse_args(blender_arguments())


def rounded(values) -> list[float]:
    return [round(float(value), 6) for value in values]


def choose_mesh(name: str | None):
    if name:
        obj = bpy.data.objects.get(name)
        if obj is None or obj.type != "MESH":
            raise ValueError(f"Mesh object does not exist: {name!r}")
        return obj
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    if len(meshes) != 1:
        raise ValueError("--object is required unless the scene contains exactly one mesh")
    return meshes[0]


def validate_axes(forward: Vector, up: Vector) -> None:
    if abs(forward.dot(up)) > 1e-6:
        raise ValueError("Source forward and up axes must be perpendicular")


def basis(forward: Vector, up: Vector) -> Matrix:
    right = forward.cross(up)
    if right.length <= 1e-6:
        raise ValueError("Forward and up axes cannot be parallel")
    right.normalize()
    return Matrix((right, forward, up)).transposed()


def source_to_target_rotation(source_forward: Vector, source_up: Vector) -> Matrix:
    return basis(TARGET_FORWARD, TARGET_UP) @ basis(source_forward, source_up).inverted()


def bounds(points: list[Vector]) -> tuple[Vector, Vector]:
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
    return low, high


def topology_signature(mesh) -> dict:
    return {
        "vertices": len(mesh.vertices),
        "edges": len(mesh.edges),
        "polygons": len(mesh.polygons),
        "loops": len(mesh.loops),
        "faces": [list(polygon.vertices) for polygon in mesh.polygons],
        "uvLayers": {
            layer.name: [rounded(item.uv) for item in layer.data]
            for layer in mesh.uv_layers
        },
        "materials": [material.name if material else None for material in mesh.materials],
    }


def main() -> None:
    args = parse_args()
    if args.height <= 0.0:
        raise ValueError("Target height must be positive")
    output = args.output.resolve()
    if output.suffix.lower() != ".blend":
        raise ValueError("Normalized output must use the .blend extension")
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite output: {output}")
    if bpy.data.filepath and Path(bpy.data.filepath).resolve() == output:
        raise ValueError("Output must differ from the currently open Blender file")
    if args.report is not None:
        args.report = args.report.resolve()
        if args.report.suffix.lower() != ".json":
            raise ValueError("Normalization report must use the .json extension")
        if args.report.exists():
            raise FileExistsError(f"Refusing to overwrite report: {args.report}")
        if args.report == output:
            raise ValueError("Normalized output and report must use different paths")

    obj = choose_mesh(args.object)
    if obj.parent is not None:
        raise ValueError("Normalize the mesh before parenting it")
    if obj.children:
        raise ValueError("Normalize the mesh before parenting other objects to it")
    if obj.constraints:
        raise ValueError("Object constraints must be resolved before normalization")
    if obj.modifiers:
        raise ValueError("Object modifiers must be resolved before normalization")
    if obj.data.shape_keys is not None:
        raise ValueError("Shape-key meshes are not supported by the normalization tool")
    if obj.data.users > 1:
        obj.data = obj.data.copy()

    source_forward = AXIS_VECTORS[args.source_forward]
    source_up = AXIS_VECTORS[args.source_up]
    validate_axes(source_forward, source_up)
    rotation = source_to_target_rotation(source_forward, source_up)
    mesh = obj.data
    before_signature = topology_signature(mesh)
    source_world_points = [obj.matrix_world @ vertex.co for vertex in mesh.vertices]
    if not source_world_points:
        raise ValueError("Cannot normalize an empty mesh")
    rotated_points = [rotation @ point for point in source_world_points]
    before_low, before_high = bounds(rotated_points)
    before_dimensions = before_high - before_low
    if before_dimensions.z <= 0.0:
        raise ValueError("Rotated mesh has no positive height")

    base_center = Vector(
        (
            (before_low.x + before_high.x) * 0.5,
            (before_low.y + before_high.y) * 0.5,
            before_low.z,
        )
    )
    scale_factor = args.height / before_dimensions.z
    normalization = (
        Matrix.Scale(scale_factor, 4)
        @ Matrix.Translation(-base_center)
        @ rotation.to_4x4()
        @ obj.matrix_world
    )
    # Mesh.transform updates geometric normals as it bakes the complete object-space
    # transformation. Directly assigning vertex coordinates would leave custom normals
    # in their old orientation.
    mesh.transform(normalization)
    obj.matrix_world = Matrix.Identity(4)
    mesh.update()

    after_signature = topology_signature(mesh)
    if before_signature != after_signature:
        raise RuntimeError("Normalization changed topology, UVs, or material assignments")
    normalized_points = [vertex.co.copy() for vertex in mesh.vertices]
    after_low, after_high = bounds(normalized_points)
    after_dimensions = after_high - after_low
    epsilon = 1e-5
    checks = {
        "height": abs(after_dimensions.z - args.height) <= epsilon,
        "grounded": abs(after_low.z) <= epsilon,
        "centeredX": abs((after_low.x + after_high.x) * 0.5) <= epsilon,
        "centeredY": abs((after_low.y + after_high.y) * 0.5) <= epsilon,
        "identityTransform": max(
            abs(float(obj.matrix_world[row][column]) - (1.0 if row == column else 0.0))
            for row in range(4)
            for column in range(4)
        ) <= epsilon,
        "topologyUvMaterialsPreserved": before_signature == after_signature,
        "finiteCoordinates": all(math.isfinite(float(value)) for point in normalized_points for value in point),
    }
    if not all(checks.values()):
        raise RuntimeError("Normalization verification failed: " + json.dumps(checks, sort_keys=True))

    obj["ammunae_forward"] = "-Y"
    obj["ammunae_up"] = "+Z"
    obj["ammunae_height"] = float(args.height)
    obj["ammunae_normalization_scale"] = float(scale_factor)
    report = {
        "input": bpy.data.filepath or None,
        "output": str(output),
        "object": obj.name,
        "sourceForward": args.source_forward,
        "sourceUp": args.source_up,
        "targetForward": "-Y",
        "targetUp": "+Z",
        "targetHeight": args.height,
        "scaleFactor": scale_factor,
        "sourceRotatedBounds": {
            "min": rounded(before_low),
            "max": rounded(before_high),
            "dimensions": rounded(before_dimensions),
        },
        "normalizedBounds": {
            "min": rounded(after_low),
            "max": rounded(after_high),
            "dimensions": rounded(after_dimensions),
        },
        "checks": checks,
    }

    output.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(output), check_existing=False)
    if args.report is not None:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("AMMUNAE_MODEL_NORMALIZATION=" + json.dumps(report, separators=(",", ":")))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
