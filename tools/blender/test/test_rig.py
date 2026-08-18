"""Synthetic regression checks for configured rig and Action creation."""

from __future__ import annotations

import math
import sys
from pathlib import Path

import bpy
from mathutils import Matrix

BLENDER_TOOLS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BLENDER_TOOLS))

from src.rig import create_actions, create_rig  # noqa: E402


def identity():
    return [
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 1.0, 0.0, 0.0],
        [0.0, 0.0, 1.0, 0.0],
        [0.0, 0.0, 0.0, 1.0],
    ]


def node(name, parent, pivot, object_id, tracks=None):
    return {
        "name": name,
        "class": "Helper",
        "objectId": object_id,
        "parentId": -1,
        "parent": parent,
        "pivot": list(pivot),
        "flags": [],
        "base": {
            "localTranslation": [0.0, 0.0, 0.0],
            "localRotationXyzw": [0.0, 0.0, 0.0, 1.0],
            "localScale": [1.0, 1.0, 1.0],
            "worldMatrix": identity(),
        },
        "reference": {
            "localTranslation": [0.0, 0.0, 0.0],
            "localRotationXyzw": [0.0, 0.0, 0.0, 1.0],
            "localScale": [1.0, 1.0, 1.0],
            "worldMatrix": identity(),
            "worldPivot": list(pivot),
        },
        "tracks": tracks or [],
    }


def main() -> None:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    translation = {
        "name": "Translation",
        "typeId": 0,
        "interpolation": "Linear",
        "globalSequenceId": None,
        "globalSequenceLength": None,
        "entries": [
            {"time": 0, "value": [0.0, 0.0, 0.0]},
            {"time": 1000, "value": [10.0, 0.0, 2.0]},
        ],
    }
    rotation = {
        "name": "Rotation",
        "typeId": 2,
        "interpolation": "Linear",
        "globalSequenceId": None,
        "globalSequenceLength": None,
        "entries": [
            {"time": 0, "value": [0.0, 0.0, 0.0, 1.0]},
            {
                "time": 1000,
                "value": [0.0, 0.0, math.sin(math.pi / 4.0), math.cos(math.pi / 4.0)],
            },
        ],
    }
    nodes = [
        node("Root", None, (0.0, 0.0, 0.0), 0, [translation]),
        node("Omitted Helper", "Root", (0.0, 0.0, 2.0), 1),
        node("Child", "Omitted Helper", (0.0, 0.0, 5.0), 2, [rotation]),
        node("Origin Ref", "Root", (0.0, 0.0, 0.0), 3),
        node("Chest Ref", "Child", (0.0, 0.0, 5.0), 4),
        node("Overhead Ref", "Child", (0.0, 0.0, 10.0), 5),
        node("Right Ref", "Child", (1.0, 0.0, 5.0), 6),
        node("Left Ref", "Child", (-1.0, 0.0, 5.0), 7),
    ]
    source = {
        "schema": 2,
        "source": "synthetic.mdx",
        "name": "Synthetic",
        "animations": [
            {
                "name": "Stand",
                "start": 0,
                "end": 1000,
                "length": 1000,
                "nonLooping": False,
                "moveSpeed": 0.0,
                "rarity": 0.0,
            }
        ],
        "globalSequences": [],
        "referencePose": {
            "animation": "Stand",
            "offsetMs": 0,
            "sourceTimeMs": 0,
            "interval": [0, 1000],
        },
        "nodes": nodes,
        "mesh": {
            "referenceBounds": {
                "min": [-1.0, -1.0, 0.0],
                "max": [1.0, 1.0, 10.0],
                "dimensions": [2.0, 2.0, 10.0],
            }
        },
    }
    config = {
        "schema": 1,
        "name": "synthetic",
        "rigObject": "synthetic_rig",
        "hierarchy": "nearestSelectedParent",
        "source": {
            "referenceAnimation": "Stand",
            "referenceOffsetMs": 0,
            "forward": "+X",
            "up": "+Z",
        },
        "target": {
            "forward": "-Y",
            "up": "+Z",
            "height": 64.0,
            "rootBone": "Root",
            "maxJoints": 128,
        },
        "nodes": [
            {"source": "Root", "deform": True},
            {"source": "Child", "deform": True},
            {"source": "Origin Ref", "target": "origin", "deform": False},
            {"source": "Chest Ref", "target": "chest", "deform": False},
            {"source": "Overhead Ref", "target": "overhead", "deform": False},
            {"source": "Right Ref", "target": "right_hand", "deform": False},
            {"source": "Left Ref", "target": "left_hand", "deform": False},
        ],
        "displayTailChildren": {"Root": "Child"},
        "inPlace": {
            "lockPlanarTranslation": True,
            "removeFacingYaw": True,
            "preserveVerticalTranslation": True,
        },
        "actions": [
            {
                "source": "Stand",
                "target": "idle",
                "loop": True,
                "phaseFromReference": True,
            }
        ],
    }

    rig, state, converter, reference_world, reference_error = create_rig(source, config)
    reports = create_actions(
        rig,
        source,
        config,
        state,
        converter,
        reference_world,
        fps=10,
    )
    assert reference_error <= 1e-6
    assert len(rig.data.bones) == 7
    assert rig.data.bones["Child"].parent.name == "Root"
    assert rig.data.bones["chest"].parent.name == "Child"
    for attachment in ("origin", "chest", "overhead", "right_hand", "left_hand"):
        assert not rig.data.bones[attachment].use_deform
    action = bpy.data.actions["idle"]
    assert reports["idle"]["samples"] == 11
    assert len(action.layers[0].strips[0].channelbags[0].fcurves) == 70
    assert all(
        point.interpolation == "LINEAR"
        for curve in action.layers[0].strips[0].channelbags[0].fcurves
        for point in curve.keyframe_points
    )
    bpy.context.scene.frame_set(1)
    bpy.context.view_layer.update()
    reference_basis_error = max(
        abs(float(bone.matrix_basis[row][column]) - (1.0 if row == column else 0.0))
        for bone in rig.pose.bones
        for row in range(4)
        for column in range(4)
    )
    assert reference_basis_error <= 1e-5
    assert rig.matrix_world == Matrix.Identity(4)
    assert not any(obj.type == "MESH" for obj in bpy.data.objects)
    print("AMMUNAE_TEST_RIG=passed")


if __name__ == "__main__":
    main()
