"""Create a synthetic Blender scene for audit and normalization tests."""

from __future__ import annotations

import sys
from pathlib import Path

import bpy
from mathutils import Matrix


def arguments():
    return sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []


def main() -> None:
    if len(arguments()) != 1:
        raise ValueError("Expected one output .blend path")
    output = Path(arguments()[0]).resolve()
    if output.exists():
        raise FileExistsError(output)

    bpy.ops.wm.read_factory_settings(use_empty=True)
    mesh = bpy.data.meshes.new("synthetic_mesh_data")
    mesh.from_pydata(
        [
            (0.0, 0.0, 0.0),
            (2.0, 0.0, 0.0),
            (0.0, 0.0, 1.0),
            (4.0, 0.0, 0.0),
            (5.0, 0.0, 0.0),
            (4.0, 0.0, 1.0),
        ],
        [],
        [(0, 1, 2), (3, 4, 5)],
    )
    mesh.update(calc_edges=True)
    uv = mesh.uv_layers.new(name="UVMap")
    for loop in uv.data:
        loop.uv = (float(loop.uv.x), float(loop.uv.y))
    material = bpy.data.materials.new("synthetic_material")
    mesh.materials.append(material)

    obj = bpy.data.objects.new("synthetic_model", mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.matrix_world = Matrix(
        (
            (0.0, -2.0, 0.0, 7.0),
            (2.0, 0.0, 0.0, -3.0),
            (0.0, 0.0, 2.0, 5.0),
            (0.0, 0.0, 0.0, 1.0),
        )
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(output), check_existing=False)
    print(f"AMMUNAE_TEST_FIXTURE={output}")


if __name__ == "__main__":
    main()
