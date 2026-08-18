# Model Pipeline

This document defines the working steps for producing a new Uldum model with Ammunae. A step may be performed by a human, an Agent, or a human with Agent assistance. The pipeline defines **what is done**, not who must do it.

The only formal input is an **idea**. Concept art, prompts, generated meshes, rigs, animations, Blender files, and reports are artifacts produced or selected while following the pipeline.

This pipeline assumes that every model has animation. Even models such as trees should have a rig and at least basic motion. Closely related steps may be combined when one tool performs both, but the stated outputs and acceptance checks still apply. The steps do not imply a mandatory directory for every stage.

The normative output requirements are in the [model contract](../contracts/model.md). The workspace and retention rules are in the [workspace contract](workspace.md).

## Pipeline Overview

```text
Idea + world style
→ choose an existing rig or a Warcraft III rig to adopt
→ generate concept art for that rig and its authoring pose
→ generate a textured 3D model
→ preserve the generated source and create the Blender source
→ inspect the generated model
→ normalize orientation, scale, and placement
→ prepare topology, materials, and textures
→ add the rig and animations
→ align the mesh to the rig
→ skin the mesh
→ test and repair deformation
→ set the final Blender hierarchy and attachments
→ validate and export glTF/GLB
→ test the exported model in Uldum
→ retain useful artifacts and promote reusable resources
```

## 1. Choose an Existing Rig or Adopt a Warcraft III Rig

### Inputs

- the model idea;
- reusable rigs and their animations under `assets/<world>/shared/`;
- Classic Warcraft III MDX models that could supply a new rig and animation set.

### Procedure

1. Determine the broad body structure and movement family implied by the idea, such as humanoid infantry, quadruped, flying creature, or animated tree.
2. Inspect existing world-shared rigs together with their animations and visible reference models. Prefer an existing rig when its structure, proportions, equipment ownership, and motions can support the idea through a new skin.
3. If no existing rig fits, inspect candidate Classic Warcraft III models and their animations as complete models. Select one whose body structure and motion best fit the idea, then adopt its skeleton, reference pose, and useful animations as the basis for another reusable rig.
4. Do not author a new skeleton independently. A rig used by this pipeline is either an existing reusable rig or one adopted from a Classic Warcraft III model.
5. For an existing reusable rig, preserve its bone names and semantics, hierarchy, rest pose, local axes, and scale convention. Uldum runtime compatibility alone does not make two authoring rigs animation-compatible.
6. Identify the rig's exact authoring/reference pose. For a Warcraft III source, use Retera Model Studio to display the source model in that pose. An animation pose such as `Stand - 1` may be used, and Retera Model Studio can also display an A-pose when a clearer rigging pose is preferred.
7. Frame the complete source model consistently and capture a screenshot that clearly shows its pose, silhouette, body proportions, and equipment. This screenshot is the proportion and pose reference for concept generation.
8. Confirm visible limb and equipment ownership from the posed reference model rather than inferring it from bone-name suffixes alone.
9. Record the selected rig, its source, its available animation set, the reference screenshot, and the pose and proportion constraints that concept and model generation must follow.

### Output

- the selected existing rig or Warcraft III rig to adopt;
- the rig's exact authoring/reference pose and proportion constraints;
- a screenshot of the complete source model in that pose;
- its available animation set and visible bone ownership.

### Accept when

The selected rig can plausibly support the model idea as a new skin without changing the rig's established structure or rest data.

## 2. Generate Concept Art

### Inputs

- the model idea;
- the selected rig and its authoring/reference pose;
- the reference screenshot captured in Step 1;
- reusable visual direction from `assets/<world>/style/`;
- useful references supplied for this model.

### Procedure

1. Read the world's reusable style guidance, the model idea, and the selected rig's proportion and pose constraints.
2. Upload the Step 1 screenshot of the posed source model to an online multi-modal image-generation service such as Gemini or ChatGPT image generation. Use the screenshot as the explicit pose and proportion reference rather than describing those constraints only in text.
3. Compose a temporary image-generation prompt containing:
   - the model's role and defining features;
   - the world's shape, color, material, and texture language;
   - an instruction to preserve the uploaded reference's pose and body proportions;
   - all required equipment;
   - a full-body, uncropped composition;
   - a simple background that clearly separates the silhouette.
4. Generate concept candidates from the screenshot and prompt.
5. Compare the candidates for:
   - fidelity to the idea and world style;
   - readable silhouette;
   - visible and complete limbs and equipment;
   - preservation of the screenshot's pose and proportions;
   - suitability as input to image-to-3D generation.
6. If a candidate's pose or major proportions cannot plausibly fit the rig, reject or regenerate it instead of deferring the mismatch to Blender.
7. Select one concept and keep it in `assets/<world>/models/<model>/`. Keep additional candidates only if they still help.
8. Extract any newly discovered reusable style principle into the world's `style/` material. The complete model-specific prompt may be discarded when it is no longer useful.

### Output

One selected full-body concept image that defines the design in proportions and a pose compatible with the selected rig.

### Accept when

- the design belongs visually to the world;
- every required body part and piece of equipment is visible;
- its major proportions and pose can fit the selected rig;
- the image is clear enough for 3D generation.

### Potential improvements

- Compare concept and model generation from an A-pose screenshot with generation from a source animation pose such as `Stand - 1` to determine which reduces later alignment and skinning work.
- Capture front, side, and back views of the same posed source in Retera Model Studio, upload all three to the image-generation service, and test whether it can produce consistent three-view concept art that improves proportion preservation during 3D generation.

## 3. Generate the Textured 3D Model

### Inputs

- the selected concept image;
- the selected rig's authoring pose and proportion constraints;
- any service-specific generation guidance that has proven reusable.

### Procedure

1. Upload the selected concept image to Tripo and select its legacy 2.5 model. This was the validated generation path and allowed the generated model to be downloaded without a paid export.
2. Configure generation to produce:
   - the complete model rather than a cropped bust;
   - the same pose and proportions as the concept;
   - all required weapons, shields, clothing, and accessories;
   - a textured result;
   - a target of approximately 1,000 triangles for an RTS unit.
3. Generate the model, inspect Tripo's preview, and download the selected result as GLB.
4. Generate additional candidates only when the current result has an anatomical, design, or structural problem that is cheaper to regenerate than repair. Reserve Blender repair for local technical defects.
5. Inspect candidates in Tripo's preview or another 3D viewer for:
   - silhouette from gameplay distance;
   - front, side, back, and top appearance;
   - complete limbs and equipment;
   - plausible thickness and volume;
   - texture quality and UV continuity;
   - pose fidelity;
   - obvious holes, fused limbs, or missing surfaces;
   - potentially useful separate surfaces for armor and equipment.
6. Select the candidate with the best visible design and repairable structure. Do not prefer a candidate only because its mesh statistics look cleaner, and do not require perfect topology at this stage. Reject a model whose basic anatomy or silhouette is incompatible with the target rig.

### Output

One selected textured GLB or glTF source model.

### Accept when

- the design matches the selected concept closely enough;
- the model is complete from all important views;
- its body structure and pose can be aligned to the target rig;
- the remaining defects appear repairable in Blender.

## 4. Preserve the Generated Source and Create the Blender Source

### Inputs

The selected generated GLB or glTF.

### Procedure

1. Store the downloaded source in `assets/<world>/models/<model>/`.
2. Treat this file as immutable. Never overwrite it with a normalized, rigged, or exported version.
3. Import the source into Blender.
4. Create or choose one canonical editable `.blend` file for the model.
5. Before a difficult or destructive operation, copy the canonical `.blend` to one clearly named backup.
6. Avoid creating a new `.blend` for every speculative stage. Use the canonical file for accepted work and explicit backups for meaningful rollback points.
7. Save only after the current operation has been visually accepted.

### Output

- an untouched generated source model;
- one canonical Blender authoring file;
- useful explicit backups where needed.

### Accept when

The original generated file can still be recovered byte-for-byte and the Blender source is ready for editing.

## 5. Inspect the Model in Blender

### Inputs

The imported source model in the canonical Blender file.

### Procedure

Inspect and record:

1. object names and types;
2. mesh and object transforms;
3. bounding box, visible height, and ground contact;
4. current forward and up directions;
5. vertex, edge, and triangle counts;
6. disconnected components;
7. coincident but separate surfaces;
8. non-manifold edges and actual holes;
9. UV maps, materials, textures, and custom normals;
10. existing armatures, skins, vertex groups, animations, and shape keys;
11. likely rigid surfaces such as weapons and shields;
12. unsupported glTF features that must be removed before export.

Run the parameterized [Blender model audit](../tools/blender/README.md#audit-a-model) to collect the structural measurements without changing the scene. Use both its numerical report and visual inspection because they answer different questions. Treat coincident patches as separate surfaces until their intended deformation ownership is understood, then choose only the preparation operations that the model actually needs.

### Output

A concrete list of required model-preparation operations.

### Accept when

The model's orientation, scale, topology, materials, existing rigging state, and meaningful surface boundaries are understood well enough to edit safely.

## 6. Normalize Orientation, Scale, and Placement

### Inputs

- the inspected Blender source;
- the target Uldum scale;
- the selected rig.

### Procedure

Use the generalized [Blender normalization tool](../tools/blender/README.md#normalize-a-generated-model) for the whole-model orientation, grounding, centering, and scale operation when the model is still unrigged. Supply the observed source axes explicitly rather than asking the tool to guess them.

1. Rotate the model to Ammunae's Blender authoring convention:

   ```text
   Forward: -Y
   Up:      +Z
   ```
2. Move the feet or model base to the ground plane.
3. Place the model origin at an appropriate stable location, normally the center of the feet or model base.
4. Scale the model near its intended Uldum size. Useful references are:

   ```text
   Terrain tile:             128 units
   Typical collision radius: 20 units
   Typical unit height:      approximately 64 units
   ```
5. Compare the model directly with the target rig rather than using only a bounding-box target. Use a predictable authoring scale instead of relying on runtime scale to conceal a mismatch with shared rigs and animations.
6. Adjust the whole model's translation, rotation, and scale before moving local vertices.
7. Apply or preserve Blender object transforms deliberately. Keep mesh and rig transforms predictable and mutually compatible.
8. Verify the result from front, side, and gameplay views.

### Output

A correctly oriented, grounded, and approximately scaled model.

### Accept when

- the model faces `-Y` in Blender;
- its up direction is `+Z`;
- its base rests on the ground;
- its dimensions are appropriate for Uldum and the target rig.

## 7. Prepare Topology, Materials, and Textures

### Inputs

The normalized model and the findings from inspection.

### Procedure

1. Repair actual malformed geometry that affects rendering or deformation:
   - holes;
   - invalid faces;
   - inverted normals;
   - accidental duplicate geometry;
   - severe intersections that cannot deform correctly.
2. Preserve meaningful separate surfaces for:
   - armor panels;
   - body parts that only touch visually;
   - weapons and shields;
   - independently moving accessories.
3. Do not globally merge coincident vertices merely to make the model manifold.
4. Join a seam only when both surfaces should truly share topology and deformation. To close a purely visual gap between independent patches, co-locate the applicable boundary vertices without merging them.
5. Preserve or repair the primary UV set and visible normals.
6. Reduce geometry only when required by performance or visual quality.
7. Ensure exported primitives are triangles.
8. Simplify materials to data supported by Uldum:
   - diffuse/base color texture or factor;
   - opaque rendering for skinned materials.
9. Preserve the working source texture. Convert shipping textures to KTX2 when the delivery workflow requires it.

### Output

Geometry, UVs, normals, materials, and textures ready for rigging.

### Accept when

- the model renders correctly;
- meaningful surface boundaries remain intact;
- no topology operation has changed the visible model unintentionally;
- the material does not depend on unsupported runtime behavior.

## 8. Add the Rig and Animations

### Inputs

- the prepared mesh;
- the rig selected in Step 1;
- its existing animation set;
- its exact authoring/reference pose.

### Procedure

1. Add the selected armature and its animation set to the Blender file:
   - link or copy the existing reusable rig and Actions; or
   - use the tracked [Warcraft III extraction and rig-adoption tools](../tools/warcraft3/README.md) with the reviewed per-rig configuration to reconstruct the selected skeleton and Actions from its hierarchy, pivots, and MDX tracks.
2. Keep the rig's bone names, hierarchy, rest pose, local axes, and scale unchanged. Do not replace it with a newly authored skeleton.
3. For a moving combat unit, provide these five non-deforming attachment bones:

   ```text
   origin
   chest
   overhead
   right_hand
   left_hand
   ```
4. If using existing Actions from the same rig, copy or link them without retargeting.
5. If converting a Warcraft III MDX animation source:
   - evaluate tracks only within the active sequence;
   - do not interpolate across sequence gaps;
   - convert a sequence-relative reference timestamp to its correct absolute source time before evaluating the reference pose;
   - use the source's actual pivots and hierarchy;
   - convert source coordinates and scale to Blender;
   - calculate animation deltas from the exact reference pose;
   - convert source-world transforms to target pose-bone transforms;
   - remove planar root movement and facing yaw while preserving vertical and body-local motion;
   - create Blender Actions with linear interpolation.
6. Name Actions using Uldum's case-sensitive runtime names. Use contiguous suffixes for variants:

   ```text
   idle
   idle_2
   walk
   attack
   attack_2
   death
   ```
7. Confirm that the first/reference animation pose reproduces the rig's intended reference pose before fitting the mesh.

### Output

A target armature with the intended attachments and a useful set of correctly named, in-place Blender Actions.

### Accept when

- the rig satisfies the model contract;
- the Action names are correct;
- the animations play on the rig without taking ownership of world movement or facing;
- the reference pose is known exactly.

### Potential improvements

- Test a normalization pass that aligns the contact moments of attack or cast variants while preserving each source motion's character.

## 9. Align the Mesh to the Rig

### Inputs

- the prepared mesh;
- the target armature in its reference pose.

### Procedure

1. Display the armature in front of the mesh.
2. Put the armature in its rest/reference pose and the mesh in its undeformed state.
3. Compare these pivots from several views:
   - pelvis and hips;
   - knees and ankles;
   - shoulders and elbows;
   - wrists and hands;
   - neck and head.
4. Correct any remaining whole-model translation, rotation, or scale mismatch.
5. When using a validated reusable rig, fit the mesh to the rig instead of changing the rig's rest data and invalidating its existing animations.
6. Move complete anatomical mesh sections to fit the corresponding rig sections. Include every downstream surface that should move, but exclude unrelated torso, armor, and opposite-limb surfaces.
7. For a limb with the correct length but wrong direction:
   - keep the joint pivot fixed;
   - select the complete downstream assembly;
   - rotate it rigidly around the joint;
   - include held equipment in the hand assembly.
8. Do not scale a limb to fix a directional mismatch when its length already matches the rig.
9. Use small local vertex edits only after the large sections align.
10. Close visible gaps carefully. Avoid merging independent surfaces unless they should become one deforming surface.
11. Review the result visually rather than accepting a transform only because it matches a calculated direction.
12. Play `idle` and confirm that the rig sits approximately inside the mesh.

### Output

A mesh that approximately fits the rig in the common reference pose.

### Accept when

- major mesh joints align with rig pivots;
- no limb has an obvious directional or length mismatch;
- the neutral animation does not visibly stretch the model;
- weapons and shields remain coherent with their hands.

## 10. Skin the Mesh

### Inputs

- the aligned mesh;
- the target armature.

### Procedure

1. Create one mesh vertex group for each deforming bone. The vertex-group name must exactly match the bone name.
2. Confirm each bone's visible anatomical or equipment ownership on the posed model; do not rely on left/right suffixes alone.
3. Assign weights by anatomical and mechanical ownership rather than surface proximity:
   - torso surfaces to torso bones;
   - each arm only to bones on that arm;
   - each leg only to bones on that leg;
   - armor to the body section it should follow;
   - weapons and shields rigidly to their controlling hand or equipment bone.
4. Assign rigid equipment weight `1.0` to one controlling bone wherever practical and remove all other deform-bone influences.
5. Use gradual blends only around real joints such as shoulders, elbows, hips, and knees.
6. Keep no more than four influences per vertex.
7. Remove cross-side and cross-limb influences before normalizing. Normalization redistributes existing weights; it does not correct anatomical ownership.
8. Normalize the remaining valid weights after incorrect groups have been removed.
9. Use Weight Paint for broad regions and Edit Mode's Vertex Groups panel for exact selected vertices.
10. Pause on an extreme animation frame while painting to see the deformation update immediately. The weights remain global, not frame-specific.
11. Do not replace accepted manual weights with proximity transfer or automatic weights.

### Output

An anatomically weighted mesh using the target rig's deform bones.

### Accept when

- every deforming surface follows the intended body section;
- rigid equipment remains rigid;
- no vertex has more than four influences;
- no limb or torso surface is weighted to an unrelated limb.

### Potential improvements

- Test whether Blender's automatic weights provide a useful starting point for a clean model generated in a rig-friendly pose. Any result must still pass the same anatomical ownership and deformation checks before acceptance.

## 11. Test and Repair Deformation

### Inputs

The rigged and skinned model with all intended Actions.

### Procedure

1. Inspect the model in the reference or `idle` pose.
2. Inspect at least one extreme frame of `walk`; extreme frames often reveal cross-limb contamination that is invisible in `idle`.
3. Inspect the wind-up, contact, and recovery portions of every `attack` variant.
4. Play the complete `death` animation.
5. Inspect every additional Action intended for export.
6. Look for:
   - stretched or collapsed limbs;
   - torso or armor pulled by an arm or leg;
   - limbs adhering to one another;
   - gaps between surfaces;
   - equipment bending or separating from the hand;
   - joint-volume collapse;
   - triangle inversion;
   - animation-loop discontinuity;
   - residual root locomotion or facing rotation.
7. Classify the failure before editing:

   ```text
   Wrong neutral pose                 → align mesh to rig
   Correct neutral pose, sticks moving → repair weights
   Weapon or shield bends             → make equipment weights rigid
   Entire motion is wrong             → repair animation conversion/reference pose
   Seam after rotating a limb         → correct the geometry selection or local seam
   ```
8. Repair one anatomical area at a time using the simplest change that addresses the observed failure.
9. Replay `idle`, `walk`, and `attack` after each accepted repair.
10. Use numerical checks for contract properties, but require visual review for deformation quality; correct matrices, normalized weights, valid influence counts, and stable bounds do not prove that deformation looks correct.
11. Save the canonical Blender file only after the visible result is accepted.

### Output

A model that deforms acceptably in all intended animations.

### Accept when

- all exported clips pass visual review;
- no unrelated surfaces adhere to moving limbs;
- equipment remains attached and rigid;
- the animation loops and root behavior are correct.

## 12. Set the Final Blender Hierarchy and Attachments

### Inputs

The accepted prepared model and its armature.

### Procedure

1. Object-parent the mesh to the armature while preserving the mesh's world transform.
2. Confirm this hierarchy in the Outliner. Use indentation, not row order, to identify the parent-child relationship:

   ```text
   <armature>
   └── <mesh>
   ```
3. Separately ensure the mesh has an Armature modifier targeting the same armature. Object parenting and deformation through an Armature modifier are distinct relationships, and both must be correct.
4. Do not invoke automatic weights during parenting when vertex groups already exist.
5. Confirm the standard attachment bones exist and follow sensible animated positions:
   - `origin`;
   - `chest`;
   - `overhead`;
   - `right_hand`;
   - `left_hand`.
6. Replay the animations after parenting to ensure placement and weights remain unchanged.
7. Confirm that no authoring-only helper object is part of the export hierarchy.
8. Save the canonical Blender file.

### Output

A clean Blender object hierarchy ready for export.

### Accept when

- the mesh is a direct child of the intended armature;
- the Armature modifier targets that armature;
- world placement and weights are unchanged;
- attachment points are present where required;
- no rejected or diagnostic object is part of the export hierarchy.

## 13. Validate the Model

### Inputs

The accepted Blender source ready for export.

### Procedure

Check applicable rules from the [model contract](../contracts/model.md) after important accepted operations and again before export. Use reports or fingerprints when they improve repeatability; they do not require a separate stage-named Blender file. Contract validation complements visual review rather than replacing it:

1. geometry exports as triangle primitives;
2. orientation and scale follow the authoring convention;
3. textures use the primary UV set;
4. materials use supported runtime data;
5. the model has one intended skin;
6. the skeleton has no more than 128 joints;
7. each vertex has no more than four influences;
8. skinned primitives provide `JOINTS_0` and `WEIGHTS_0`;
9. inverse bind matrices and hierarchy are valid;
10. moving combat units provide all five standard attachment bones;
11. Actions use recognized case-sensitive names;
12. animation interpolation is linear for export;
13. shared animations are in place;
14. the model does not rely on morph targets, Draco, true alpha blending, or unsupported PBR inputs;
15. the original generated source remains unchanged;
16. no unintended rig, Action, UV, material, topology, or weight changes occurred during the final repairs.

### Output

A model that satisfies the applicable authoring and Uldum runtime contracts.

### Accept when

All required checks pass and visible deformation has already been accepted.

## 14. Export glTF/GLB

### Inputs

The validated Blender source.

### Procedure

1. Select or otherwise restrict export to the intended mesh and armature hierarchy.
2. Export with Blender's glTF 2.0 exporter.
3. Include:
   - the mesh and materials;
   - the armature and skin;
   - all intended Actions with their exact names;
   - required textures or sidecars.
4. Use Blender's standard glTF Y-up conversion. A model authored facing `-Y` in Blender should export facing `+Z` in glTF.
5. Do not export helper, diagnostic, backup, or rejected objects.
6. Do not enable unsupported Draco compression.
7. Prefer `.glb` for a self-contained model when practical.
8. If exporting `.gltf`, keep every referenced texture and buffer at the expected relative path.
9. Run the model validator against the exported file rather than assuming Blender export success proves compatibility.

### Output

A validated Uldum-compatible `.glb` or `.gltf` deliverable. The exported model is the deliverable; the Blender file remains its editable source.

### Accept when

The exported file contains the intended geometry, skin, materials, textures, attachments, and animations with no contract violation. It must still pass Step 15 because successful Blender export does not prove Uldum loader and runtime behavior.

## 15. Test the Exported Model in Uldum

### Inputs

- the exported glTF/GLB and required sidecars;
- a Uldum type definition that references the model.

### Procedure

1. Put the exported model and its sidecars under the applicable Uldum asset directory.
2. Reference it from a real Uldum type definition through the `model` field.
3. Load the map or test scene in Uldum.
4. Confirm:
   - the model loads instead of showing the procedural placeholder;
   - orientation, scale, and ground placement are correct;
   - materials and textures render correctly;
   - `idle`, `walk`, `attack`, and other clips play under runtime state control;
   - crossfades do not reveal hidden weight errors;
   - weapons and shields remain attached;
   - attachment bones give sensible effect and projectile positions;
   - root motion does not fight gameplay movement or facing;
   - attack and cast contact moments align with configured gameplay timing.
5. Treat Uldum runtime behavior as the final authority on loader compatibility and state behavior. If a problem appears, repair it in the pipeline step that owns the authoring defect rather than compensating for it in Uldum:

   ```text
   Wrong scale or facing       → Normalize orientation, scale, and placement
   Missing texture             → Prepare materials/textures or fix export sidecars
   Missing animation           → Add animations or fix Action/export naming
   Sticking or stretching      → Skin/test deformation
   Weapon detaches             → Repair equipment weights/hierarchy
   Loader warning or failure   → Validate/export again
   ```
6. Re-export and retest until the asset works in its intended Uldum context.

### Output

A model proven to work in Uldum.

### Accept when

The model loads, renders, animates, and behaves correctly in the actual engine state machine.

## 16. Retain Useful Artifacts and Promote Reusable Resources

### Inputs

The completed model workspace and the knowledge gained while producing it.

### Procedure

1. Normally retain in `assets/<world>/models/<model>/`:
   - the selected concept art;
   - the untouched selected generated model;
   - the canonical Blender source;
   - explicit useful backups;
   - the exported glTF/GLB and required sidecars;
   - validation reports that still help maintenance.
2. Delete obsolete diagnostics, temporary prompts, rejected candidates, and easily reproduced intermediates when they no longer help.
3. Move a resource into `assets/<world>/shared/` only after multiple assets actually use it. Candidates include:
   - a rig;
   - converted animation Actions;
   - materials and textures;
   - reusable mesh parts.
4. Put reusable visual and prompt guidance in `assets/<world>/style/`.
5. Promote world-agnostic knowledge or deterministic tooling into the repository when broader value is demonstrated. Examples include:
   - contracts and pipeline guidance;
   - MDX evaluation and conversion;
   - exporters, validators, and normalizers;
   - topology inspection and restoration;
   - reusable prompt principles.

### Output

A maintainable model workspace plus reusable resources stored at the narrowest level where they are actually useful.

### Accept when

The model can be edited and exported again, while reusable knowledge has been retained without preserving unnecessary production history.
