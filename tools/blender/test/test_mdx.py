"""Synthetic regression checks for the reusable MDX evaluator."""

from __future__ import annotations

import math
import sys
from pathlib import Path

from mathutils import Matrix, Quaternion, Vector

BLENDER_TOOLS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BLENDER_TOOLS))

from src.mdx import (  # noqa: E402
    evaluate_track,
    local_matrix,
    matrix_error,
    source_world_matrices,
)
from src.rig import filter_root_motion  # noqa: E402


def close(first, second, tolerance=1e-6):
    return (first - second).length <= tolerance


def main() -> None:
    # Keys outside the active sequence must not affect evaluation inside it.
    track = {
        "name": "Translation",
        "interpolation": "Linear",
        "globalSequenceId": None,
        "entries": [
            {"time": 0, "value": [100.0, 0.0, 0.0]},
            {"time": 100, "value": [0.0, 0.0, 0.0]},
            {"time": 200, "value": [10.0, 0.0, 0.0]},
            {"time": 300, "value": [200.0, 0.0, 0.0]},
        ],
    }
    value = evaluate_track(track, 150, 100, 200, Vector((0.0, 0.0, 0.0)))
    assert close(value, Vector((5.0, 0.0, 0.0)))

    held = {
        "name": "Translation",
        "interpolation": "Linear",
        "globalSequenceId": None,
        "entries": [{"time": 120, "value": [3.0, 4.0, 5.0]}],
    }
    assert close(
        evaluate_track(held, 180, 100, 200, Vector((0.0, 0.0, 0.0))),
        Vector((3.0, 4.0, 5.0)),
    )

    hermite_track = {
        "name": "Translation",
        "interpolation": "Hermite",
        "globalSequenceId": None,
        "entries": [
            {
                "time": 100,
                "value": [0.0, 0.0, 0.0],
                "outTan": [0.0, 0.0, 0.0],
                "inTan": [0.0, 0.0, 0.0],
            },
            {
                "time": 200,
                "value": [10.0, 0.0, 0.0],
                "outTan": [10.0, 0.0, 0.0],
                "inTan": [10.0, 0.0, 0.0],
            },
        ],
    }
    assert close(
        evaluate_track(hermite_track, 150, 100, 200, Vector((0.0, 0.0, 0.0))),
        Vector((3.75, 0.0, 0.0)),
    )

    rotation_track = {
        "name": "Rotation",
        "interpolation": "Linear",
        "globalSequenceId": None,
        "entries": [
            {"time": 100, "value": [0.0, 0.0, 0.0, 1.0]},
            {"time": 200, "value": [0.0, 0.0, -1.0, 0.0]},
        ],
    }
    rotation = evaluate_track(
        rotation_track,
        150,
        100,
        200,
        Quaternion((1.0, 0.0, 0.0, 0.0)),
        rotation=True,
    )
    assert math.isclose(rotation.magnitude, 1.0, rel_tol=0.0, abs_tol=1e-6)

    # Pivot composition and hierarchy must produce the expected child world position.
    nodes = {
        "root": {
            "name": "root",
            "parent": None,
            "pivot": [0.0, 0.0, 0.0],
            "tracks": [held],
        },
        "child": {
            "name": "child",
            "parent": "root",
            "pivot": [1.0, 0.0, 0.0],
            "tracks": [rotation_track],
        },
    }
    worlds = source_world_matrices(nodes, 150, 100, 200)
    assert close(worlds["root"].translation, Vector((3.0, 4.0, 5.0)))
    local = local_matrix(nodes["child"], 150, 100, 200)
    assert matrix_error(worlds["child"], worlds["root"] @ local) <= 1e-6

    # Root filtering operates on the animation delta, so the reference pose remains unchanged.
    rest = Matrix.Translation(Vector((4.0, -2.0, 7.0)))
    filtered_reference = filter_root_motion(
        {"root": rest.copy()},
        {"root": rest.copy()},
        "root",
        {
            "lockPlanarTranslation": True,
            "removeFacingYaw": True,
            "preserveVerticalTranslation": True,
        },
    )
    assert matrix_error(filtered_reference["root"], rest) <= 1e-6
    moved = Matrix.Translation(Vector((8.0, 3.0, 9.0))) @ Matrix.Rotation(math.radians(35.0), 4, "Z")
    filtered_moved = filter_root_motion(
        {"root": moved @ rest},
        {"root": rest.copy()},
        "root",
        {
            "lockPlanarTranslation": True,
            "removeFacingYaw": True,
            "preserveVerticalTranslation": True,
        },
    )
    delta = filtered_moved["root"] @ rest.inverted_safe()
    assert abs(delta.translation.x) <= 1e-6
    assert abs(delta.translation.y) <= 1e-6
    assert abs(delta.translation.z - 9.0) <= 1e-6

    global_track = {
        "name": "Translation",
        "interpolation": "Linear",
        "globalSequenceId": 0,
        "globalSequenceLength": 100,
        "entries": [
            {"time": 0, "value": [0.0, 0.0, 0.0]},
            {"time": 100, "value": [10.0, 0.0, 0.0]},
        ],
    }
    assert close(
        evaluate_track(global_track, 250, 100, 200, Vector((0.0, 0.0, 0.0))),
        Vector((5.0, 0.0, 0.0)),
    )
    try:
        evaluate_track(
            {**global_track, "globalSequenceLength": None},
            150,
            100,
            200,
            Vector((0.0, 0.0, 0.0)),
        )
    except ValueError as error:
        assert "Global-sequence" in str(error)
    else:
        raise AssertionError("Invalid global-sequence track was accepted unexpectedly")

    print("AMMUNAE_TEST_MDX=passed")


if __name__ == "__main__":
    main()
