# Blender Tools

These scripts run in Blender 5.1 and do not require Blender MCP. They can run in background mode or from Blender's scripting workspace. Arguments passed after Blender's `--` separator belong to the script.

## Audit a model

`audit_model.py` writes structural diagnostics without modifying or saving the scene:

```powershell
blender model.blend --background --python tools\blender\audit_model.py -- `
  --output C:\work\model-audit.json `
  --object Model `
  --merge-distance 0.000001
```

Omit `--object` to audit every mesh in the scene. A merge-distance probe operates only on an in-memory `bmesh` copy. The report covers transforms, bounds, triangles, connected components, manifold status, UVs, color attributes, shape keys, materials, textures, modifiers, armatures, and vertex-group influence counts. It complements visual inspection; it does not decide whether a model looks correct.

## Normalize a generated model

`normalize_model.py` rotates one unrigged mesh to Blender `-Y` forward and `+Z` up, centers and grounds its base, uniformly scales it, bakes it to an identity object transform, and writes a new Blender file:

```powershell
blender imported-model.blend --background --python tools\blender\normalize_model.py -- `
  --object Model `
  --source-forward=-Y `
  --source-up=+Z `
  --height 64 `
  --output C:\work\normalized.blend `
  --report C:\work\normalization.json
```

The source forward and up directions must be stated explicitly. The current operation supports any perpendicular signed cardinal axes and rejects an ambiguous scene instead of guessing. It must run before parenting, constraints, modifiers, skinning, or shape keys are added. It preserves mesh topology, UVs, and material assignments and refuses to overwrite either the open source or an existing output.

Material cleanup, topology repair, skinning, and visual acceptance are separate pipeline operations.

## Adopt a Warcraft III rig

See [the Warcraft III tool documentation](../warcraft3/README.md) for MDX extraction, per-rig configuration, and `adopt_warcraft3_rig.py` usage.

## Regression tests

The tests use Blender itself and contain only synthetic geometry and animation data:

```powershell
blender --background --python tools\blender\test\test_mdx.py
blender --background --python tools\blender\test\test_rig.py
```

The audit and normalization integration tests create files under a temporary directory; they do not use production assets.
