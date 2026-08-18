"""Build configured Blender rigs and Actions from extracted Warcraft III data."""

from __future__ import annotations

import bpy
from mathutils import Matrix, Quaternion, Vector

from .mdx import (
    CoordinateConverter,
    matrix_error,
    parse_matrix,
    source_world_matrices,
)


REQUIRED_ATTACHMENTS = {"origin", "chest", "overhead", "right_hand", "left_hand"}


def normalized_config(config: dict, source: dict) -> dict:
    if int(config.get("schema", 0)) != 1:
        raise ValueError("Unsupported rig configuration schema")
    if int(source.get("schema", 0)) != 2:
        raise ValueError("Unsupported MDX extraction schema")
    if config.get("hierarchy") != "nearestSelectedParent":
        raise ValueError("Unsupported rig hierarchy policy")

    reference = source["referencePose"]
    if reference["animation"] != config["source"]["referenceAnimation"]:
        raise ValueError("Extracted reference animation differs from the rig configuration")
    if int(reference["offsetMs"]) != int(config["source"]["referenceOffsetMs"]):
        raise ValueError("Extracted reference offset differs from the rig configuration")

    source_nodes = {node["name"].strip(): node for node in source["nodes"]}
    node_entries = config.get("nodes", [])
    if not node_entries:
        raise ValueError("Rig configuration has no selected nodes")

    source_to_target: dict[str, str] = {}
    deform_by_target: dict[str, bool] = {}
    for entry in node_entries:
        source_name = entry["source"].strip()
        target_name = entry.get("target", source_name).strip()
        if source_name not in source_nodes:
            raise ValueError(f"Configured source node does not exist: {source_name!r}")
        if source_name in source_to_target:
            raise ValueError(f"Configured source node is duplicated: {source_name!r}")
        if target_name in deform_by_target:
            raise ValueError(f"Configured target bone is duplicated: {target_name!r}")
        source_to_target[source_name] = target_name
        deform_by_target[target_name] = bool(entry.get("deform", True))

    max_joints = int(config["target"].get("maxJoints", 128))
    if len(source_to_target) > max_joints:
        raise ValueError(f"Configured rig exceeds the {max_joints}-joint limit")
    if not REQUIRED_ATTACHMENTS.issubset(deform_by_target):
        missing = sorted(REQUIRED_ATTACHMENTS - set(deform_by_target))
        raise ValueError(f"Rig configuration lacks Uldum attachments: {missing}")
    for attachment in REQUIRED_ATTACHMENTS:
        if deform_by_target[attachment]:
            raise ValueError(f"Attachment must be non-deforming: {attachment}")

    selected_sources = set(source_to_target)

    def nearest_selected_parent(source_name: str) -> str | None:
        parent = source_nodes[source_name].get("parent")
        parent = parent.strip() if parent else None
        visited = set()
        while parent is not None and parent not in selected_sources:
            if parent in visited:
                raise ValueError(f"Cycle while resolving selected parent for {source_name!r}")
            visited.add(parent)
            parent_node = source_nodes.get(parent)
            if parent_node is None:
                return None
            parent = parent_node.get("parent")
            parent = parent.strip() if parent else None
        return parent

    parent_by_target = {
        source_to_target[source_name]: (
            source_to_target[parent]
            if (parent := nearest_selected_parent(source_name)) is not None
            else None
        )
        for source_name in source_to_target
    }

    sequences = {item["name"]: item for item in source["animations"]}
    action_names = set()
    for action in config.get("actions", []):
        if action["source"] not in sequences:
            raise ValueError(f"Configured source animation does not exist: {action['source']!r}")
        if action["target"] in action_names:
            raise ValueError(f"Configured target Action is duplicated: {action['target']!r}")
        action_names.add(action["target"])

    root_bone = config["target"]["rootBone"]
    if root_bone not in deform_by_target:
        raise ValueError(f"Configured root bone is not selected: {root_bone!r}")

    return {
        "source_nodes": source_nodes,
        "source_to_target": source_to_target,
        "source_for_target": {target: source_name for source_name, target in source_to_target.items()},
        "deform_by_target": deform_by_target,
        "parent_by_target": parent_by_target,
        "sequences": sequences,
        "root_bone": root_bone,
    }


def _display_tail(
    name: str,
    heads: dict[str, Vector],
    parents: dict[str, str | None],
    hints: dict[str, str],
) -> Vector:
    preferred = hints.get(name)
    if preferred in heads and (heads[preferred] - heads[name]).length > 0.05:
        return heads[preferred].copy()
    children = [
        child
        for child, parent in parents.items()
        if parent == name and (heads[child] - heads[name]).length > 0.05
    ]
    if children:
        child = min(children, key=lambda value: (heads[value] - heads[name]).length)
        direction = heads[child] - heads[name]
        return heads[name] + direction.normalized() * min(direction.length, 5.0)
    parent = parents.get(name)
    if parent in heads and (heads[name] - heads[parent]).length > 0.05:
        direction = heads[name] - heads[parent]
        return heads[name] + direction.normalized() * min(
            2.5,
            max(0.7, direction.length * 0.25),
        )
    return heads[name] + Vector((0.0, 0.0, 1.5))


def _reference_world(
    source: dict,
    state: dict,
    converter: CoordinateConverter,
) -> tuple[dict[str, Matrix], float]:
    reference = source["referencePose"]
    sequence = state["sequences"][reference["animation"]]
    source_time = int(reference["sourceTimeMs"])
    calculated = source_world_matrices(
        state["source_nodes"],
        source_time,
        int(sequence["start"]),
        int(sequence["end"]),
    )
    maximum_error = 0.0
    for name, node in state["source_nodes"].items():
        expected = parse_matrix(node["reference"]["worldMatrix"])
        maximum_error = max(maximum_error, matrix_error(calculated[name], expected))
    if maximum_error > 1e-4:
        raise ValueError(f"MDX evaluator does not reproduce the extracted reference pose: {maximum_error}")
    selected = {
        target: converter.matrix(calculated[source_name])
        for target, source_name in state["source_for_target"].items()
    }
    return selected, maximum_error


def create_rig(source: dict, config: dict):
    state = normalized_config(config, source)
    converter = CoordinateConverter(source, config)
    reference_world, reference_error = _reference_world(source, state, converter)
    rig_name = config["rigObject"]

    if bpy.data.objects.get(rig_name) is not None:
        raise ValueError(f"Blender object already exists: {rig_name!r}")

    heads = {
        target: converter.point(state["source_nodes"][source_name]["reference"]["worldPivot"])
        for target, source_name in state["source_for_target"].items()
    }
    armature_data = bpy.data.armatures.new(f"{rig_name}_data")
    rig = bpy.data.objects.new(rig_name, armature_data)
    bpy.context.scene.collection.objects.link(rig)
    rig.matrix_world = Matrix.Identity(4)
    rig.show_in_front = True
    rig.display_type = "WIRE"
    rig["ammunae_rig"] = config["name"]
    rig["ammunae_source"] = str(source["source"])
    rig["ammunae_reference_animation"] = source["referencePose"]["animation"]
    rig["ammunae_reference_offset_ms"] = int(source["referencePose"]["offsetMs"])
    rig["ammunae_reference_source_time_ms"] = int(source["referencePose"]["sourceTimeMs"])
    rig["ammunae_forward"] = config["target"]["forward"]
    rig["ammunae_up"] = config["target"]["up"]
    rig["ammunae_scale"] = float(converter.scale)

    bpy.context.view_layer.objects.active = rig
    rig.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    edit_bones = {}
    hints = config.get("displayTailChildren", {})
    for target in state["source_for_target"]:
        bone = armature_data.edit_bones.new(target)
        bone.head = heads[target]
        bone.tail = _display_tail(target, heads, state["parent_by_target"], hints)
        bone.roll = 0.0
        bone.use_deform = state["deform_by_target"][target]
        edit_bones[target] = bone
    for target, parent in state["parent_by_target"].items():
        if parent is not None:
            edit_bones[target].parent = edit_bones[parent]
            edit_bones[target].use_connect = False
    bpy.ops.object.mode_set(mode="OBJECT")

    for target, source_name in state["source_for_target"].items():
        bone = armature_data.bones[target]
        node = state["source_nodes"][source_name]
        bone["ammunae_source_name"] = source_name
        bone["ammunae_source_object_id"] = int(node["objectId"])
        bone["ammunae_source_class"] = node["class"]
        bone["ammunae_reference_world_matrix"] = [
            value
            for row in reference_world[target]
            for value in row
        ]

    actual_parents = {
        bone.name: bone.parent.name if bone.parent else None
        for bone in armature_data.bones
    }
    if actual_parents != state["parent_by_target"]:
        raise RuntimeError("Constructed hierarchy differs from the configured hierarchy")

    return rig, state, converter, reference_world, reference_error


def desired_pose_matrices(
    source_world: dict[str, Matrix],
    state: dict,
    converter: CoordinateConverter,
    reference_world: dict[str, Matrix],
    rest_matrices: dict[str, Matrix],
) -> dict[str, Matrix]:
    return {
        name: (
            converter.matrix(source_world[state["source_for_target"][name]])
            @ reference_world[name].inverted_safe()
            @ rest_matrices[name]
        )
        for name in state["source_for_target"]
    }


def filter_root_motion(
    desired: dict[str, Matrix],
    rest_matrices: dict[str, Matrix],
    root_name: str,
    policy: dict,
) -> dict[str, Matrix]:
    if not policy.get("lockPlanarTranslation") and not policy.get("removeFacingYaw"):
        return desired
    rest = rest_matrices[root_name]
    delta = desired[root_name] @ rest.inverted_safe()
    location, rotation, scaling = delta.decompose()
    if policy.get("removeFacingYaw"):
        swing, _twist = rotation.to_swing_twist("Z")
        rotation = swing.normalized()
    x = 0.0 if policy.get("lockPlanarTranslation") else location.x
    y = 0.0 if policy.get("lockPlanarTranslation") else location.y
    z = location.z if policy.get("preserveVerticalTranslation", True) else 0.0
    filtered_delta = (
        Matrix.Translation(Vector((x, y, z)))
        @ rotation.to_matrix().to_4x4()
        @ Matrix.Diagonal((*scaling, 1.0))
    )
    result = dict(desired)
    result[root_name] = filtered_delta @ rest
    return result


def basis_for(
    name: str,
    desired: dict[str, Matrix],
    rest_matrices: dict[str, Matrix],
    parent_names: dict[str, str | None],
) -> Matrix:
    parent = parent_names[name]
    rest = rest_matrices[name]
    if parent is None:
        return rest.inverted_safe() @ desired[name]
    rest_relative = rest_matrices[parent].inverted_safe() @ rest
    return (
        rest_relative.inverted_safe()
        @ desired[parent].inverted_safe()
        @ desired[name]
    )


def _sample_times(
    sequence: dict,
    fps: int,
    loop: bool,
    phase_from_reference: bool,
    reference_source_time: int,
) -> tuple[list[float], list[float]]:
    start = int(sequence["start"])
    end = int(sequence["end"])
    length = end - start
    if length <= 0:
        raise ValueError(f"Animation has non-positive duration: {sequence['name']!r}")
    sample_count = int(round(length * fps / 1000.0)) + 1
    frames = [float(index + 1) for index in range(sample_count)]
    if phase_from_reference:
        if not loop:
            raise ValueError("Reference-phased Action must loop")
        times = []
        offset = reference_source_time - start
        for index in range(sample_count):
            if index == sample_count - 1:
                times.append(float(reference_source_time))
            else:
                elapsed = length * index / (sample_count - 1)
                times.append(float(start + ((offset + elapsed) % length)))
    else:
        times = [start + (length * index / (sample_count - 1)) for index in range(sample_count)]
        if loop:
            times[-1] = float(start)
    return frames, times


def create_actions(
    rig,
    source: dict,
    config: dict,
    state: dict,
    converter: CoordinateConverter,
    reference_world: dict[str, Matrix],
    *,
    fps: int,
) -> dict[str, dict]:
    nodes = state["source_nodes"]
    bone_names = [bone.name for bone in rig.data.bones]
    rest_matrices = {name: rig.data.bones[name].matrix_local.copy() for name in bone_names}
    parent_names = {
        name: rig.data.bones[name].parent.name if rig.data.bones[name].parent else None
        for name in bone_names
    }
    reference_source_time = int(source["referencePose"]["sourceTimeMs"])
    action_reports = {}
    rig.animation_data_create()
    bpy.context.scene.render.fps = fps
    bpy.context.scene.render.fps_base = 1.0

    for action_config in config.get("actions", []):
        action_name = action_config["target"]
        if bpy.data.actions.get(action_name) is not None:
            raise ValueError(f"Blender Action already exists: {action_name!r}")
        sequence = state["sequences"][action_config["source"]]
        loop = bool(action_config.get("loop", not bool(sequence.get("nonLooping", False))))
        frames, times = _sample_times(
            sequence,
            fps,
            loop,
            bool(action_config.get("phaseFromReference", False)),
            reference_source_time,
        )
        action = bpy.data.actions.new(action_name)
        action.use_fake_user = True
        action.use_frame_range = True
        action.frame_start = frames[0]
        action.frame_end = frames[-1]
        action.use_cyclic = loop
        action["ammunae_source_clip"] = action_config["source"]
        action["ammunae_source_start_ms"] = int(sequence["start"])
        action["ammunae_source_end_ms"] = int(sequence["end"])
        action["ammunae_source_reference_ms"] = reference_source_time
        action["ammunae_sample_rate"] = fps
        action["ammunae_looping"] = loop
        action["ammunae_in_place_policy"] = json_policy(config.get("inPlace", {}))
        slot = action.slots.new("OBJECT", rig.name)
        action.layers.new("Base")
        action.layers[0].strips.new(type="KEYFRAME")
        rig.animation_data.action = action
        rig.animation_data.action_slot = slot

        previous_quaternions: dict[str, Quaternion] = {}
        maximum_reconstruction_error = 0.0
        for frame, time_ms in zip(frames, times):
            source_world = source_world_matrices(
                nodes,
                time_ms,
                int(sequence["start"]),
                int(sequence["end"]),
            )
            desired = desired_pose_matrices(
                source_world,
                state,
                converter,
                reference_world,
                rest_matrices,
            )
            desired = filter_root_motion(
                desired,
                rest_matrices,
                state["root_bone"],
                config.get("inPlace", {}),
            )
            for bone_name in bone_names:
                pose_bone = rig.pose.bones[bone_name]
                basis = basis_for(bone_name, desired, rest_matrices, parent_names)
                location, rotation, scaling = basis.decompose()
                rotation.normalize()
                previous = previous_quaternions.get(bone_name)
                if previous is not None and previous.dot(rotation) < 0.0:
                    rotation = Quaternion(tuple(-value for value in rotation))
                previous_quaternions[bone_name] = rotation.copy()
                pose_bone.rotation_mode = "QUATERNION"
                pose_bone.location = location
                pose_bone.rotation_quaternion = rotation
                pose_bone.scale = scaling
                pose_bone.keyframe_insert("location", frame=frame, group=bone_name)
                pose_bone.keyframe_insert("rotation_quaternion", frame=frame, group=bone_name)
                pose_bone.keyframe_insert("scale", frame=frame, group=bone_name)
            bpy.context.scene.frame_set(int(round(frame)))
            bpy.context.view_layer.update()
            for bone_name in bone_names:
                maximum_reconstruction_error = max(
                    maximum_reconstruction_error,
                    matrix_error(rig.pose.bones[bone_name].matrix, desired[bone_name]),
                )
        if maximum_reconstruction_error > 3e-4:
            raise RuntimeError(
                f"Action {action_name!r} pose reconstruction failed: "
                f"{maximum_reconstruction_error}"
            )

        channelbag = action.layers[0].strips[0].channelbags[0]
        for fcurve in channelbag.fcurves:
            for keyframe in fcurve.keyframe_points:
                keyframe.interpolation = "LINEAR"
        action_reports[action_name] = {
            "source": action_config["source"],
            "loop": loop,
            "frames": [frames[0], frames[-1]],
            "samples": len(frames),
            "fcurves": len(channelbag.fcurves),
            "maximumPoseReconstructionError": maximum_reconstruction_error,
        }

    if config.get("actions"):
        first_name = config["actions"][0]["target"]
        first_action = bpy.data.actions[first_name]
        rig.animation_data.action = first_action
        rig.animation_data.action_slot = first_action.slots[0]
        bpy.context.scene.frame_start = int(first_action.frame_start)
        bpy.context.scene.frame_end = int(first_action.frame_end)
        bpy.context.scene.frame_set(int(first_action.frame_start))
        bpy.context.view_layer.update()

    return action_reports


def json_policy(policy: dict) -> str:
    enabled = []
    if policy.get("lockPlanarTranslation"):
        enabled.append("planar translation locked")
    if policy.get("removeFacingYaw"):
        enabled.append("facing yaw removed")
    if policy.get("preserveVerticalTranslation"):
        enabled.append("vertical translation preserved")
    return "; ".join(enabled) if enabled else "unchanged"
