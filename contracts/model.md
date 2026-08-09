# Ammunae Model Contract

This is the single model contract for Ammunae. It combines:

- the output requirements imposed by Uldum's model loader and runtime; and
- the authoring and interchange rules Ammunae uses to make rigs and animations reusable.

It applies to static, skinned, and animated models. Some clauses are conditional: a static prop does not need a skeleton, and a specialized building does not need animations or attachment points that its gameplay never uses.

## Contract Language

- **Required** means the applicable model must satisfy the rule.
- **Recommended** means the rule should be followed unless the model has a concrete reason not to.
- **Supported** and **unsupported** describe current Uldum runtime behavior.

## Output Format

All output models must use **glTF 2.0**, as either `.gltf` or `.glb`.

A model may contain:

| Component | glTF field | Requirement |
|---|---|---|
| Meshes | `meshes[]` | At least one mesh is required. |
| Skeleton | `skins[0]` | Required only for skinned models. Uldum uses the first skin only. |
| Animations | `animations[]` | Required only when the model needs animation. |
| Materials | `materials[]` | Optional; assigned per primitive. |

## Coordinates, Orientation, and Scale

The authoring and runtime coordinate contract is:

| Space | Forward | Up |
|---|---|---|
| Blender authoring | `-Y` | `+Z` |
| Exported glTF | `+Z` | `+Y` |
| Uldum game space | Facing angle `0` points toward `+X` | `+Z` |

Blender models should therefore be authored facing `-Y` and exported using the standard glTF Y-up conversion. Uldum applies a `-90°` X rotation when rendering a non-native glTF model.

Uldum game coordinates use `X = right`, `Y = forward`, and `Z = up`.

### Scale

Models should be authored near their intended Uldum scale. Useful reference measurements are:

| Measurement | Typical value |
|---|---:|
| Terrain tile | 128 game units |
| Unit collision radius | 20 game units |
| Unit height | Approximately 64 game units |

A unit definition may apply `transform.scale`, but correctly scaled source assets are recommended so that shared rigs, attachments, animation, and previews remain predictable.

### Node Transforms

Uldum supports node translation, rotation, and scale, as either TRS properties or a node matrix. Transforms are composed through the node hierarchy.

- Static mesh node transforms are baked into vertices at load time.
- Normals use the inverse-transpose, so non-uniform static node scale does not skew lighting.
- Skinned vertices remain in bind-pose space; the skeleton owns their placement.
- Blender object transforms do not have to be applied before export. Exported node transforms are honored.

## Geometry

### Primitive Type

Only `TRIANGLES` primitives are supported. Uldum warns about and skips primitives using any other topology.

Indexed and non-indexed triangle primitives are supported. Each primitive is drawn separately with its own material.

### Vertex Attributes

Uldum supports the following attributes:

| Attribute | Use | Requirement |
|---|---|---|
| `POSITION` | Vertex position | Required for every mesh primitive. |
| `NORMAL` | Vertex normal | Supported. |
| `TEXCOORD_0` | First UV set | Required when the material uses a texture. |
| `JOINTS_0` | Four joint indices | Required for a skinned primitive. |
| `WEIGHTS_0` | Four joint weights | Required for a skinned primitive. |

A primitive is treated as skinned only when the model has a skin and the primitive provides both `JOINTS_0` and `WEIGHTS_0`.

The following geometry features are unsupported:

- primitive types other than `TRIANGLES`;
- additional UV sets such as `TEXCOORD_1`;
- additional joint or weight sets;
- vertex colors (`COLOR_0`);
- tangent attributes;
- morph targets;
- Draco mesh compression.

Uldum warns for unsupported primitive types, additional UV sets, and additional joint/weight sets. Only the first supported sets are used.

## Materials and Textures

Materials are assigned per primitive on both static and skinned models.

### Supported Material Data

Uldum supports:

- `pbrMetallicRoughness.baseColorTexture` as the primitive's diffuse texture;
- `pbrMetallicRoughness.baseColorFactor` as a per-instance color multiplier or as a flat color when no texture is present;
- `alphaMode: OPAQUE`;
- `alphaMode: MASK` and `alphaCutoff` on static models;
- `doubleSided` on static models.

Static masked materials affect both visible rendering and shadow shape. Static double-sided materials disable back-face culling for both the visible and shadow passes.

On skinned models, Uldum reads `alphaMode` and `doubleSided` but currently renders the primitive as opaque with back-face culling. A skinned model must not depend on masked transparency or double-sided rendering for its intended appearance.

`alphaMode: BLEND` is unsupported as true transparency and degrades to opaque rendering with a warning.

### Unsupported Shading Data

Uldum does not currently use:

- metallic or roughness values;
- normal maps;
- occlusion maps;
- emissive maps or factors;
- `KHR_materials_*` extensions;
- `KHR_materials_pbrSpecularGlossiness`.

The current model shader uses diffuse color or texture with Lambert lighting, ambient light, shadows, and point lights rather than full PBR shading.

### Texture Formats

KTX2 with Basis Universal is the recommended shipping texture format.

The model loader also accepts PNG, JPEG, BMP, TGA, and HDR images. Textures may be embedded in a buffer view or referenced by an external URI. KTX2 may be embedded through `KHR_texture_basisu`, embedded as image data, or referenced as an external `.ktx2` file.

When a `.gltf` or `.glb` relies on external textures, those files are part of the model deliverable and must remain available at the referenced paths.

## Skinning and Skeletons

A skinned model must satisfy all of the following:

- use `skins[0]`; additional skins are ignored with a warning;
- contain no more than **128 joints**;
- use no more than **four joint influences per vertex**;
- provide `JOINTS_0` and `WEIGHTS_0` on every skinned primitive;
- provide inverse bind matrices for the skin's joints;
- express joint parentage through the glTF node hierarchy.

Uldum determines each joint's parent by walking the node tree.

An unskinned mesh parented to a bone, such as a weapon attached to a hand, is automatically converted by Uldum to a skinned mesh with full weight on that parent bone.

## Reusable Rigs

Ammunae may use several reusable rigs. Different rigs are expected for different body structures and for adopting different groups of Warcraft III animations.

A reusable rig is one concrete skeleton definition. Models may directly share animation through that rig only when they use the same:

- joint names and joint semantics;
- joint hierarchy and parentage;
- rest and bind pose;
- local bone axes;
- scale convention.

Renaming a joint, changing its parent, changing the rest pose, or using incompatible local axes produces a different rig for direct animation-sharing purposes.

The following may differ without changing the rig:

- mesh shape and proportions, within what the skinning and animation can tolerate;
- mesh topology;
- materials and textures;
- skin weights.

Ammunae does not require one universal rig or custom rig-identification metadata in glTF or filenames.

### Retargeting

An animation authored for a different skeleton cannot be treated as directly compatible. This includes an animation extracted from a Warcraft III model whose skeleton differs from the target Ammunae rig.

Such an animation must be mapped and retargeted to the target rig. The retargeted result must satisfy the target rig's joint semantics, hierarchy, rest pose, local axes, and scale convention before it is shared with other models using that rig.

### In-Place Animation

Shared movement and action animations must be **in place**. They must not use root translation or rotation to move or turn the model through the game world. Uldum gameplay controls world position and facing.

Motion within the pose remains valid—for example, vertical body movement during a jump-like action—provided the animation does not take ownership of world locomotion or facing.

## Attachment Points

Uldum attaches effects and projectiles by looking up a named bone and reading its animated world-space transform. If a requested name does not exist, Uldum falls back to the model origin.

The standard attachment bones are:

| Name | Intended location | Typical use |
|---|---|---|
| `origin` | Feet or model base | Ground effects and appearance effects |
| `chest` | Center of torso or main body | Hits, buffs, and body effects |
| `overhead` | Above the model | Status icons and overhead effects |
| `right_hand` | Right hand or primary action point | Weapons, projectiles, and trails |
| `left_hand` | Left hand or secondary action point | Off-hand weapons and effects |

Every **moving combat unit**, including flying and non-humanoid units, must provide all five standard attachment bones. For a body without literal hands, `right_hand` and `left_hand` must be placed at stable primary and secondary action points with equivalent gameplay meaning.

Other models must provide every attachment bone referenced by their intended gameplay use. They do not need irrelevant hand, chest, or overhead attachments solely to complete the standard set.

A map may reference other bone names. Such names are model- or project-specific and do not replace the standard moving-combat-unit set.

## Animation Contract

### Completeness Principle

A reusable model should contain as complete and useful an animation set as practical. It should not contain meaningless or redundant clips merely to satisfy a checklist.

In practice, the initial animation set is determined by the corresponding Warcraft III source model whose motions are being adopted. Useful source motions should be preserved and adapted to Uldum's clip names and semantics. Motions that do not apply to the new model should be omitted. Further clips may be authored or adopted when a real reuse need appears.

The recognized clip names below describe Uldum capabilities, not a mandatory bundle for every model. Missing clips use the bind pose and do not crash the engine.

### Supported Animation Data

Uldum supports animation channels targeting:

- translation;
- rotation;
- scale.

Animation samplers should use `LINEAR` interpolation. Uldum plays all animation as linear; `STEP` and `CUBICSPLINE` generate warnings and do not retain their authored interpolation behavior.

Morph-target animation is unsupported. Animation on an unskinned model is dropped with a warning.

### Recognized Clips

Uldum matches animation names case-sensitively.

| Clip | Runtime meaning | Playback |
|---|---|---|
| `birth` | Visible creation or appearance where the model role supports it | One-shot |
| `idle` | Standing, resting, hovering, or ground-item presentation | Looping |
| `walk` | Ground movement, combat chase, or airborne locomotion | Looping |
| `attack` | Normal attack wind-up and backswing | One-shot per attack |
| `spell` | Ability cast point and backswing | One-shot per cast |
| `hit` | Idle normal-attack reaction or destructible damage response | One-shot |
| `death` | Death, destruction, or removal presentation | One-shot; holds the final frame |

`birth` playback is supported for buildings, destructibles, and ground items. A visible appearance animation is recommended for other spawned animated assets when their runtime use supports it.

There is no separate `fly` state. A flying model uses `walk` for its airborne locomotion loop and `idle` for hover or glide.

### Runtime State Behavior

- State transitions use a `0.15` second crossfade.
- Animation runs at render framerate rather than simulation tick rate.
- The `attack` clip is scaled to the unit's `attack_cooldown`.
- The unit definition's `animation.dmg_pt` fraction identifies the visual contact point within the attack clip; gameplay damage timing remains authoritative.
- The `spell` clip uses cast-point and backswing scaling. The unit definition's `animation.cast_pt` fraction identifies the visual cast point; gameplay cast timing remains authoritative.
- `hit` plays only for an otherwise-idle widget hit by a normal attack. Walking, attacking, casting, and dying take priority. Spells, damage-over-time, and splash damage do not trigger it.
- `death` holds its last frame after completing.

### Clip Variations

A clip may have random alternatives using contiguous numeric suffixes beginning with `_2`:

```text
attack
attack_2
attack_3
```

The suffixes must be contiguous. If `attack_2` is absent, `attack_3` is not considered part of the variation set.

- Non-looping states choose a variation on each entry.
- Looping states choose again when the clip loops.
- Variation selection is cosmetic and client-local.
- Variants share the base state's damage-point or cast-point fraction, so their important action should occur at approximately the same normalized time.

### Ground Items

Ground items use:

- `birth` when created or dropped at runtime;
- `idle` while lying on the ground;
- `death` when destroyed on the ground.

Preplaced items begin in `idle` and do not replay `birth` when a map loads. Picking an item up into an inventory is immediate and does not play `death`. Carried items are hidden. Item clips named `walk`, `attack`, `spell`, or `hit` are ignored.

## Unsupported glTF Features

The following features must not be relied upon by an Ammunae model:

- non-triangle primitives;
- additional UV or joint/weight sets;
- vertex colors and tangents;
- morph targets and morph animation;
- non-linear animation interpolation;
- animations on unskinned models;
- skins beyond `skins[0]`;
- unsupported PBR material inputs and material extensions;
- true alpha blending;
- Draco compression;
- `KHR_lights_punctual`;
- camera nodes.

Uldum walks all model nodes regardless of glTF scene roots, so scene selection must not be used to hide content from the loader.

## Uldum Asset Reference

A Uldum type definition references a model through its `model` field, for example:

```json
{
  "footman": {
    "model": "models/units/footman.glb"
  }
}
```

Uldum searches relative to the map's asset directory first and then falls back to the engine asset directory. If loading fails, Uldum displays a procedural placeholder model rather than crashing.
