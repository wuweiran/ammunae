# Ammunae

Ammunae facilitates the creation of **AI-generated, Uldum-compatible 3D models**, from an idea through a validated glTF or GLB asset.

The project defines the production pipeline, organizes its artifacts and records, maintains reusable resources, and develops tools that make any stage of the process easier or more reliable.

Ammunae is at an early stage. Its contracts, workflows, and tools will be developed and refined as the production process is investigated.

## Scope

A model project begins with an **idea from the user**. It does not require an existing model, image, rig, animation, or other source asset.

The idea should first be captured as a model brief that expresses the intended subject, appearance, function, and relevant constraints. If the user has visual references, they may use them as part of the creative direction given to an external generation service; they are not a separate required input to Ammunae.

From that starting point, Ammunae covers the complete production process:

```text
Idea
→ model brief
→ concept art
→ generated 3D model
→ mesh and material preparation
→ rigging and skinning, when needed
→ animation creation or adoption, when needed
→ validation
→ Uldum-compatible glTF or GLB
```

Concept art, generated meshes, prompts, rigs, animations, and other files encountered after the idea are **production artifacts**. They may become the input to a later pipeline stage, but they are created, selected, imported, or reused within the process rather than being prerequisites for starting it.

A completed model project should produce:

- a validated glTF or GLB model compatible with Uldum;
- the important prompts, settings, decisions, and validation results needed to understand, revisit, or improve its production;
- organized working artifacts worth retaining, such as concept art and editable source files.

Ammunae covers all model categories supported by Uldum's glTF contract. Individual paths through the pipeline may differ for static, skinned, and animated models.

## Responsibilities

Ammunae is responsible for facilitating the whole idea-to-model process. This includes:

- defining and documenting the production pipeline;
- identifying the inputs, outputs, decisions, and validation checks at each stage;
- prescribing a consistent workspace for each model and its production artifacts;
- preserving important AI prompts, generation settings, tool or service information, selected results, and consequential decisions;
- providing reusable prompt templates and generation guidance;
- investigating workflows for concept-art and 3D-model generation;
- supporting mesh cleanup, face reduction, orientation, scale, topology, UV, texture, and material preparation;
- defining compatibility contracts for models, skeletons, animations, attachments, and exports;
- maintaining reusable rigs, animations, templates, and other shared resources;
- supporting rigging, skinning, animation adoption, and retargeting;
- validating Uldum compatibility and enabling repeatable glTF export;
- building scripts, validators, integrations, templates, or any other tools that facilitate the process.

The project is not limited to a predetermined toolset. It may document and coordinate external software and online AI services, or add its own tools where doing so improves the workflow. Ammunae owns the process, organization, records, and compatibility requirements; it does not need to host every generation or authoring operation itself.

## Human Direction and Automation

For now, the pipeline is human-directed. AI and automation assist generation and transformation, while the user reviews results and makes creative and technical decisions.

This is the current operating model, not a permanent limit. Ammunae should progressively automate suitable stages and may eventually provide an agent that orchestrates much or all of the pipeline. Automation should grow from a documented and understood process rather than hide an undefined one.

## Project Workspaces and Production Records

Ammunae should define a standard on-disk workspace for every model project. The structure should provide clear places for artifacts such as:

- the model brief and notes;
- prompts and generation records;
- concept art;
- generated 3D candidates;
- editable mesh and material source files;
- textures;
- rigs and skinning work;
- animations;
- exported models;
- validation reports.

These artifacts are part of the model's production history even when they are not shipped to Uldum. In particular, selected concept art and important prompts should be retained because they capture intent and explain later choices.

The exact workspace layout, file conventions, and production-record format will be defined with the pipeline documentation.

## Repository and Asset Policy

Git should track the parts of Ammunae that benefit from versioning and sharing, including:

- project documentation and compatibility contracts;
- pipeline guidance;
- reusable prompt templates;
- tools and scripts;
- workspace scaffolding, manifests, and README files;
- reusable shared assets when appropriate, including canonical rigs and animation libraries.

Per-model generated and working assets should normally remain outside Git because they may be numerous, large, tool-specific, or easy to regenerate. Ammunae should still provide tracked folder scaffolding and instructions so those local assets follow a consistent organization.

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

Ammunae should maintain reusable rigs and animation libraries.

Different meshes can share animations when they follow a compatible skeleton contract. Mesh shape, topology, materials, and skin weights may differ; the relevant rig structure must remain compatible.

The exact contract—including bone naming and hierarchy, bind pose, root-motion policy, attachment points, and acceptable differences in scale or body proportions—will be investigated and documented within the project.

Animations may be:

- authored for an Ammunae rig;
- imported from an existing animation source;
- retargeted from another skeleton;
- extracted and adapted from Classic Warcraft III MDX models.

## Classic Warcraft III Animation Adoption

Classic Warcraft III unit animations are an important potential source for Ammunae's animation library.

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
