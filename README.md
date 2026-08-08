# Ammunae

Ammunae facilitates the creation of **AI-generated, Uldum-compatible 3D models**, from an idea through a validated glTF or GLB asset.

The project defines the production pipeline, organizes useful artifacts, maintains reusable resources, and develops tools that make any stage of the process easier or more reliable.

Ammunae is at an early stage. Its contracts, workflows, and tools will be developed and refined as the production process is investigated.

## Scope

A model project begins with an **idea from the user**. It does not require an existing model, image, rig, animation, or other source asset, and the idea does not need to be saved as a formal document.

If the user has visual references, they may use them as part of the creative direction given to an external generation service; they are not a separate required input to Ammunae.

From that starting point, Ammunae covers the complete production process:

```text
Idea
→ concept art
→ generated 3D model
→ mesh and material preparation
→ rigging and skinning, when needed
→ animation creation or adoption, when needed
→ validation
→ Uldum-compatible glTF or GLB
```

Concept art, generated meshes, prompts, rigs, animations, and other files encountered after the idea are **production artifacts**. They may become the input to a later pipeline stage, but they are created, selected, imported, or reused within the process rather than being prerequisites for starting it.

A completed model project should produce a validated glTF or GLB model compatible with Uldum. Selected concept art, useful candidates, editable source assets, and other working files may be retained when they continue to have value. Ammunae does not require a complete production history.

Ammunae covers all model categories supported by Uldum's glTF contract. Individual paths through the pipeline may differ for static, skinned, and animated models.

## Responsibilities

Ammunae is responsible for facilitating the whole idea-to-model process. This includes:

- defining and documenting the production pipeline;
- identifying the inputs, outputs, decisions, and validation checks at each stage;
- prescribing a lightweight workspace for worlds, models, and useful production artifacts;
- providing reusable prompt fragments and generation guidance;
- investigating workflows for concept-art and 3D-model generation;
- supporting mesh cleanup, face reduction, orientation, scale, topology, UV, texture, and material preparation;
- defining compatibility contracts for models, skeletons, animations, attachments, and exports;
- maintaining reusable rigs, animations, templates, and other shared resources;
- supporting rigging, skinning, animation adoption, and retargeting;
- validating Uldum compatibility and enabling repeatable glTF export;
- building scripts, validators, integrations, templates, or any other tools that facilitate the process.

The project is not limited to a predetermined toolset. It may document and coordinate external software and online AI services, or add its own tools where doing so improves the workflow. Ammunae owns the process, organization, and compatibility requirements; it does not need to host every generation or authoring operation itself.

## Human Direction and Automation

For now, the pipeline is human-directed. AI and automation assist generation and transformation, while the user reviews results and makes creative and technical decisions.

This is the current operating model, not a permanent limit. Ammunae should progressively automate suitable stages and may eventually provide an agent that orchestrates much or all of the pipeline. Automation should grow from a documented and understood process rather than hide an undefined one.

## Worlds and Model Workspaces

Production assets are divided into **worlds**. A world groups models that share a visual language, such as concept-art direction, mesh design, materials, and texture style. It may also hold prompt fragments and resources useful across its models.

Each model has a folder inside its world, but Ammunae does not prescribe that folder's internal structure. Files should be kept when they remain useful, not merely to preserve a complete history. Failed or redundant candidates and model-specific prompts may be discarded.

When part of a prompt proves reusable, it should be extracted before the model-specific prompt is discarded:

- world-specific style guidance belongs to that world;
- world-agnostic guidance may be added to the repository in a location appropriate to the material that actually exists.

The detailed ownership rules and local layout are defined in [the workspace contract](docs/workspace.md).

## Repository and Asset Policy

Actual world workspaces live under `assets/` and remain outside Git. This includes each world's style material, shared resources, models, and production files. The sole tracked exception beneath `assets/` is `assets/template/`, which can be copied to start a world.

Git tracks only world-agnostic parts of Ammunae, including:

- project documentation and compatibility contracts;
- pipeline guidance and reusable prompt fragments;
- tools and scripts;
- workspace templates;
- reusable resources that are genuinely useful across worlds.

The repository's organization for world-agnostic work should grow from the pipeline and the material that actually exists. It should not create one folder per assumed stage in advance. Small related artifacts may stay together, while substantial areas may receive their own directories when justified. World-specific resources remain with their world even when they are shared by several models.

## Uldum Compatibility

[Uldum](model-format.md) is a unit-centric game engine inspired by Warcraft III, built with modern C++ and Vulkan. It uses glTF for models and skeletal animations.

Ammunae and Uldum are separate projects with a producer-consumer relationship:

```text
Ammunae produces compatible glTF or GLB models
Uldum consumes them
```

Uldum should not need to know:

- how a model was generated;
- which tools prepared it;
- where its rig or animations originated;
- which intermediate formats were used.

The Uldum model-format specification is Ammunae's engine-facing compatibility contract. Ammunae is specifically focused on producing models for Uldum rather than becoming a general-purpose asset pipeline.

## Shared Rigs and Animations

Ammunae should maintain reusable rigs and animation libraries where reuse proves valuable.

Different meshes can share animations when they follow a compatible skeleton contract. Mesh shape, topology, materials, and skin weights may differ; the relevant rig structure must remain compatible.

The exact contract—including bone naming and hierarchy, bind pose, root-motion policy, attachment points, and acceptable differences in scale or body proportions—will be investigated and documented within the project.

Animations may be:

- authored for an Ammunae rig;
- imported from an existing animation source;
- retargeted from another skeleton;
- extracted and adapted from Classic Warcraft III MDX models.

## Classic Warcraft III Animation Adoption

Classic Warcraft III unit animations are an important potential source for Ammunae's animation resources.

The intended work is:

```text
Classic MDX unit model
→ extract its skeletal animations
→ inspect and study the motion
→ adapt or retarget useful animations to an Ammunae rig
→ make them available to compatible generated models
```

Developing tools for extraction, inspection, conversion, adaptation, and retargeting is within Ammunae's scope.

The focus is skeletal model animation that can contribute to Ammunae's reusable animation pipeline. Directly reproducing Warcraft III-specific particles, ribbons, and other auxiliary presentation systems is not part of this initial scope.

## Boundaries

Ammunae is not:

- the Uldum engine or its runtime asset loader;
- a general-purpose asset pipeline unrelated to Uldum;
- a replacement for Blender, AI generation services, or other authoring tools;
- currently a one-click, fully automatic idea-to-model system.

These boundaries do not exclude integrating external tools, building Ammunae-specific tooling, or pursuing greater automation and agent orchestration in the future.
