"""Create a configured Warcraft III-derived Blender rig and Actions."""

from __future__ import annotations

import argparse
import json
import sys
import traceback
from pathlib import Path

import bpy

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from src.mdx import load_json  # noqa: E402
from src.rig import create_actions, create_rig  # noqa: E402


def blender_arguments() -> list[str]:
    return sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a reviewed Warcraft III-derived rig and Blender Actions."
    )
    parser.add_argument("--source", required=True, type=Path, help="JSON written by MdxExtract")
    parser.add_argument("--config", required=True, type=Path, help="Per-rig adoption configuration")
    parser.add_argument("--output", type=Path, help="New .blend file to write; omit to edit the open scene")
    parser.add_argument("--report", type=Path, help="Optional JSON summary path")
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument(
        "--replace",
        action="store_true",
        help="Remove same-named configured rig and Actions from the current scene",
    )
    return parser.parse_args(blender_arguments())


def remove_configured_data(config: dict) -> None:
    rig_name = config["rigObject"]
    rig = bpy.data.objects.get(rig_name)
    if rig is not None:
        rig_data = rig.data if rig.type == "ARMATURE" else None
        bpy.data.objects.remove(rig, do_unlink=True)
        if rig_data is not None and rig_data.users == 0:
            bpy.data.armatures.remove(rig_data)
    for item in config.get("actions", []):
        action = bpy.data.actions.get(item["target"])
        if action is not None:
            bpy.data.actions.remove(action)


def main() -> None:
    args = parse_args()
    if args.fps <= 0:
        raise ValueError("FPS must be positive")
    if not args.source.is_file():
        raise FileNotFoundError(args.source)
    if not args.config.is_file():
        raise FileNotFoundError(args.config)
    if args.output is not None:
        args.output = args.output.resolve()
        if args.output.suffix.lower() != ".blend":
            raise ValueError("Rig output must use the .blend extension")
        if args.output.exists():
            raise FileExistsError(f"Refusing to overwrite output file: {args.output}")
        if bpy.data.filepath and Path(bpy.data.filepath).resolve() == args.output:
            raise ValueError("Output must not be the currently open Blender file")
    if args.report is not None:
        args.report = args.report.resolve()
        if args.report.suffix.lower() != ".json":
            raise ValueError("Rig report must use the .json extension")
        if args.report.exists():
            raise FileExistsError(f"Refusing to overwrite report: {args.report}")
        if args.output is not None and args.report == args.output:
            raise ValueError("Rig output and report must use different paths")

    source = load_json(args.source)
    config = load_json(args.config)
    if args.replace:
        remove_configured_data(config)

    rig, state, converter, reference_world, reference_error = create_rig(source, config)
    actions = create_actions(
        rig,
        source,
        config,
        state,
        converter,
        reference_world,
        fps=args.fps,
    )

    result = {
        "source": str(args.source.resolve()),
        "config": str(args.config.resolve()),
        "rig": rig.name,
        "bones": len(rig.data.bones),
        "deformingBones": sum(bone.use_deform for bone in rig.data.bones),
        "attachments": [
            name
            for name in ("origin", "chest", "overhead", "right_hand", "left_hand")
            if name in rig.data.bones
        ],
        "scale": converter.scale,
        "referenceMatrixError": reference_error,
        "actions": actions,
    }

    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=str(args.output), check_existing=False)
        result["output"] = str(args.output)
    else:
        result["output"] = bpy.data.filepath or None

    if args.report is not None:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print("AMMUNAE_WARCRAFT3_RIG=" + json.dumps(result, separators=(",", ":")))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
