"""Verify synthetic outputs from the Blender audit and normalization tools."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import bpy


def arguments():
    return sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []


def main() -> None:
    if len(arguments()) != 2:
        raise ValueError("Expected audit JSON and normalized .blend paths")
    audit_path = Path(arguments()[0])
    normalized_path = Path(arguments()[1])
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    item = audit["objects"][0]
    assert item["name"] == "synthetic_model"
    assert item["triangles"] == 2
    assert item["topology"]["components"] == 2
    assert item["topology"]["boundaryEdges"] == 6
    assert item["uvLayers"] == ["UVMap"]
    assert item["materials"][0]["name"] == "synthetic_material"

    bpy.ops.wm.open_mainfile(filepath=str(normalized_path))
    obj = bpy.data.objects["synthetic_model"]
    points = [obj.matrix_world @ vertex.co for vertex in obj.data.vertices]
    low = [min(point[index] for point in points) for index in range(3)]
    high = [max(point[index] for point in points) for index in range(3)]
    assert abs(low[2]) <= 1e-5
    assert abs((low[0] + high[0]) * 0.5) <= 1e-5
    assert abs((low[1] + high[1]) * 0.5) <= 1e-5
    assert abs((high[2] - low[2]) - 10.0) <= 1e-5
    assert obj.get("ammunae_forward") == "-Y"
    assert obj.get("ammunae_up") == "+Z"
    assert len(obj.data.vertices) == 6
    assert len(obj.data.polygons) == 2
    assert [layer.name for layer in obj.data.uv_layers] == ["UVMap"]
    assert [material.name for material in obj.data.materials] == ["synthetic_material"]
    print("AMMUNAE_TEST_TOOLS=passed")


if __name__ == "__main__":
    main()
