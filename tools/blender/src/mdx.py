"""Warcraft III MDX animation evaluation and Blender conversion."""

from __future__ import annotations

import json
from pathlib import Path

from mathutils import Matrix, Quaternion, Vector


SUPPORTED_SOURCE_AXES = ("+X", "+Z")
SUPPORTED_TARGET_AXES = ("-Y", "+Z")


def load_json(path: str | Path) -> dict:
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def vector(values) -> Vector:
    return Vector(tuple(float(value) for value in values))


def quaternion_xyzw(values) -> Quaternion:
    x, y, z, w = (float(value) for value in values)
    result = Quaternion((w, x, y, z))
    result.normalize()
    return result


def shortest_slerp(first: Quaternion, second: Quaternion, factor: float) -> Quaternion:
    a = first.normalized()
    b = second.normalized()
    if a.dot(b) < 0.0:
        b = Quaternion(tuple(-value for value in b))
    return a.slerp(b, factor).normalized()


def squad(
    first: Quaternion,
    out_tangent: Quaternion,
    in_tangent: Quaternion,
    second: Quaternion,
    factor: float,
) -> Quaternion:
    outer = shortest_slerp(first, second, factor)
    inner = shortest_slerp(out_tangent, in_tangent, factor)
    return shortest_slerp(outer, inner, 2.0 * factor * (1.0 - factor))


def hermite(first, out_tangent, in_tangent, second, factor: float):
    squared = factor * factor
    f1 = squared * (2.0 * factor - 3.0) + 1.0
    f2 = squared * (factor - 2.0) + factor
    f3 = squared * (factor - 1.0)
    f4 = squared * (3.0 - 2.0 * factor)
    return first * f1 + out_tangent * f2 + in_tangent * f3 + second * f4


def entries_for_sequence(track: dict, sequence_start: int, sequence_end: int) -> list[dict]:
    if track.get("globalSequenceId") is not None:
        length = int(track.get("globalSequenceLength") or 0)
        if length <= 0:
            raise ValueError("Global-sequence track has no positive sequence length")
        return [
            entry
            for entry in track.get("entries", [])
            if 0 <= int(entry["time"]) <= length
        ]
    return [
        entry
        for entry in track.get("entries", [])
        if sequence_start <= int(entry["time"]) <= sequence_end
    ]


def track_interval(
    track: dict,
    time_ms: float,
    sequence_start: int,
    sequence_end: int,
) -> tuple[float, int, int]:
    if track.get("globalSequenceId") is None:
        return time_ms, sequence_start, sequence_end
    length = int(track.get("globalSequenceLength") or 0)
    if length <= 0:
        raise ValueError("Global-sequence track has no positive sequence length")
    return time_ms % length, 0, length


def evaluate_track(
    track: dict,
    time_ms: float,
    sequence_start: int,
    sequence_end: int,
    default,
    *,
    rotation: bool = False,
):
    time_ms, sequence_start, sequence_end = track_interval(
        track,
        time_ms,
        sequence_start,
        sequence_end,
    )
    entries = entries_for_sequence(track, sequence_start, sequence_end)
    if not entries:
        return default.copy()
    convert = quaternion_xyzw if rotation else vector
    if len(entries) == 1:
        return convert(entries[0]["value"])

    sequence_length = sequence_end - sequence_start
    if sequence_length <= 0:
        raise ValueError("Animation sequence must have positive duration")

    if time_ms < int(entries[0]["time"]) or time_ms >= int(entries[-1]["time"]):
        first_entry = entries[-1]
        second_entry = entries[0]
        first_time = int(first_entry["time"])
        second_time = int(second_entry["time"]) + sequence_length
        adjusted_time = time_ms + sequence_length if time_ms < first_time else time_ms
    else:
        second_index = next(
            index
            for index, entry in enumerate(entries)
            if int(entry["time"]) > time_ms
        )
        first_entry = entries[second_index - 1]
        second_entry = entries[second_index]
        first_time = int(first_entry["time"])
        second_time = int(second_entry["time"])
        adjusted_time = time_ms

    span = second_time - first_time
    factor = 0.0 if span == 0 else (adjusted_time - first_time) / span
    first_value = convert(first_entry["value"])
    second_value = convert(second_entry["value"])
    interpolation = track["interpolation"]
    if interpolation == "DontInterp":
        return first_value
    if interpolation == "Linear":
        if rotation:
            return shortest_slerp(first_value, second_value, factor)
        return first_value.lerp(second_value, factor)
    if interpolation == "Hermite":
        first_out = convert(first_entry["outTan"])
        second_in = convert(second_entry["inTan"])
        if rotation:
            return squad(first_value, first_out, second_in, second_value, factor)
        return hermite(first_value, first_out, second_in, second_value, factor)
    raise ValueError(f"Unsupported MDX interpolation: {interpolation!r}")


def local_matrix(node: dict, time_ms: float, sequence_start: int, sequence_end: int) -> Matrix:
    tracks = {track["name"]: track for track in node.get("tracks", [])}
    translation = (
        evaluate_track(
            tracks["Translation"],
            time_ms,
            sequence_start,
            sequence_end,
            Vector((0.0, 0.0, 0.0)),
        )
        if "Translation" in tracks
        else Vector((0.0, 0.0, 0.0))
    )
    rotation = (
        evaluate_track(
            tracks["Rotation"],
            time_ms,
            sequence_start,
            sequence_end,
            Quaternion((1.0, 0.0, 0.0, 0.0)),
            rotation=True,
        )
        if "Rotation" in tracks
        else Quaternion((1.0, 0.0, 0.0, 0.0))
    )
    scaling = (
        evaluate_track(
            tracks["Scaling"],
            time_ms,
            sequence_start,
            sequence_end,
            Vector((1.0, 1.0, 1.0)),
        )
        if "Scaling" in tracks
        else Vector((1.0, 1.0, 1.0))
    )
    pivot = vector(node["pivot"])
    return (
        Matrix.Translation(translation)
        @ Matrix.Translation(pivot)
        @ rotation.to_matrix().to_4x4()
        @ Matrix.Diagonal((*scaling, 1.0))
        @ Matrix.Translation(-pivot)
    )


def source_world_matrices(
    nodes: dict[str, dict],
    time_ms: float,
    sequence_start: int,
    sequence_end: int,
) -> dict[str, Matrix]:
    cache: dict[str, Matrix] = {}
    visiting: set[str] = set()

    def resolve(name: str) -> Matrix:
        if name in cache:
            return cache[name]
        if name in visiting:
            raise ValueError(f"Cycle in source hierarchy at {name!r}")
        if name not in nodes:
            raise ValueError(f"Source hierarchy references missing node {name!r}")
        visiting.add(name)
        node = nodes[name]
        local = local_matrix(node, time_ms, sequence_start, sequence_end)
        parent = node.get("parent")
        parent = parent.strip() if parent else None
        world = resolve(parent) @ local if parent else local
        visiting.remove(name)
        cache[name] = world
        return world

    for name in nodes:
        resolve(name)
    return cache


def matrix_error(first: Matrix, second: Matrix) -> float:
    return max(
        abs(float(first[row][column] - second[row][column]))
        for row in range(4)
        for column in range(4)
    )


class CoordinateConverter:
    """Convert the validated Warcraft +X/+Z convention to Blender -Y/+Z."""

    def __init__(self, source: dict, config: dict):
        source_axes = (config["source"]["forward"], config["source"]["up"])
        target_axes = (config["target"]["forward"], config["target"]["up"])
        if source_axes != SUPPORTED_SOURCE_AXES or target_axes != SUPPORTED_TARGET_AXES:
            raise ValueError(
                "The current converter supports Warcraft +X/+Z to Blender -Y/+Z only; "
                f"got {source_axes} to {target_axes}"
            )
        reference_bounds = source["mesh"]["referenceBounds"]
        source_height = float(reference_bounds["dimensions"][2])
        if source_height <= 0.0:
            raise ValueError("Reference mesh height must be positive")
        self.source_min_z = float(reference_bounds["min"][2])
        self.scale = float(config["target"]["height"]) / source_height
        self.axis = Matrix(
            (
                (0.0, 1.0, 0.0, 0.0),
                (-1.0, 0.0, 0.0, 0.0),
                (0.0, 0.0, 1.0, 0.0),
                (0.0, 0.0, 0.0, 1.0),
            )
        )
        self.axis_inverse = self.axis.inverted()

    def point(self, point) -> Vector:
        x, y, z = (float(value) for value in point)
        return Vector(
            (
                y * self.scale,
                -x * self.scale,
                (z - self.source_min_z) * self.scale,
            )
        )

    def matrix(self, source_matrix: Matrix) -> Matrix:
        converted = self.axis @ source_matrix @ self.axis_inverse
        converted.translation *= self.scale
        return converted


def parse_matrix(values) -> Matrix:
    return Matrix(tuple(tuple(float(value) for value in row) for row in values))
