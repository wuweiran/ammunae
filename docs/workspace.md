# Workspace Contract

This document defines where Ammunae production artifacts and reusable resources belong. It deliberately keeps model workspaces loose: the contract establishes ownership, not a mandatory layout for every tool's output.

## Ownership Rule

Keep an artifact at the narrowest level where it is useful:

1. **Model** — useful only while producing one model.
2. **World** — reusable by multiple models that share one visual language.
3. **Repository** — world-agnostic and useful across different worlds.

Do not move an artifact to a broader level merely because it might become reusable. Promote it when reuse is demonstrated or its broader value is clear.

## Local Asset Layout

Actual production assets live under the ignored `assets/` directory:

```text
assets/
  <world>/
    style/
    shared/
    models/
      <model>/
```

Create a world by copying `assets/template/` to `assets/<world>/`. Create a model by adding a folder directly under that world's `models/` directory.

### World

A **world** groups models that should share a coherent visual language. This may include:

- concept-art direction;
- shape and silhouette language;
- mesh detail and topology conventions;
- material and texture style;
- proportions, color language, or recurring motifs;
- generation guidance that helps produce that consistency.

A world is an asset-production boundary, not necessarily a gameplay map, story setting, or Uldum package. Use one when its models should look as though they belong together.

Everything inside an actual world is local and ignored by Git.

### `style/`

Use `style/` for material that defines or demonstrates the world's visual language. Examples include reference images, style explorations, concise guidance, and reusable prompt fragments.

No internal structure or particular file format is required. Organize it further only when real content makes that useful.

### `shared/`

Use `shared/` for concrete resources used by more than one model in the world. A shared rig, animation, mesh part, texture, or material may belong here.

Do not create categories in advance. A resource may remain in a model folder until a second model actually uses it. Model-specific modifications of a shared resource stay with the model unless those modifications also become shared.

### `models/<model>/`

Every model gets one folder directly under `models/`. Do not divide models into mandatory gameplay or technical categories.

A model folder may loosely contain any files that remain useful, including:

- selected concept art;
- useful alternative concepts or generated candidates;
- generated 3D files;
- editable authoring files;
- meshes, materials, and textures;
- model-specific rigs and animations;
- exported glTF or GLB files and external textures;
- validation output;
- tool-specific intermediate files.

Ammunae does not require subdirectories, a README, a brief, a manifest, a prompt log, or a narrative production record. External tools may create their own structure, and users may add organization when a model becomes complicated enough to need it.

The absence of a mandatory layout does not prohibit useful local organization. It prevents Ammunae from prescribing one before the real pipeline demonstrates a need.

## Artifact Retention

Retain files because they have continuing value, not solely to preserve history.

Normally retain:

- the selected concept art;
- the selected generated model;
- alternatives that may still influence or replace the selected result;
- editable source files needed for further work;
- reusable world resources;
- deliverable glTF or GLB files and required sidecars;
- validation output while it is useful for diagnosing or confirming the asset.

Normally discard:

- failed or redundant generation candidates;
- temporary conversion files that can be reproduced easily;
- model-specific prompts after they no longer help;
- records maintained only for completeness.

This is guidance rather than a deletion requirement. A user may retain anything that still helps the work.

## Prompt Lifecycle

Prompts used to make one particular model are transient working material. They do not need to become part of the model workspace or production history.

A typical lifecycle is:

```text
idea + reusable guidance
→ compose a model-specific prompt
→ generate candidates with an external service
→ select useful results
→ extract any newly reusable guidance
→ discard the model-specific prompt when no longer useful
```

Place extracted guidance according to its reuse:

- guidance that expresses one world's visual style belongs in that world's `style/` directory;
- a technique that applies across worlds may be added to the repository in a location appropriate to the material that actually exists;
- wording useful only for one model need not be retained.

Promote the reusable principle, not necessarily the complete original prompt.

## Promotion Between Levels

Artifacts may move outward as their reuse becomes clear:

```text
model → world → repository
```

### Model to world

Move or copy a resource from `models/<model>/` to `shared/` when multiple models in the same world use it. Put reusable visual or generation guidance in `style/` instead.

### World to repository

Promote a resource from a world into Git only when it is useful across worlds and does not depend on that world's visual identity. Choose its repository location based on its actual form and relationships rather than requiring a directory for every presumed pipeline stage.

A resource may remain world-specific indefinitely. Reuse within one world does not make it world-agnostic.

## Repository Layout

The tracked repository contains Ammunae itself rather than actual world workspaces. Its structure should grow from concrete documentation, tools, and reusable resources as the pipeline is defined and exercised.

Pipeline position is one useful way to organize related work, but it does not imply one directory per stage. For example, if concept-art and model-generation guidance amount to only a few closely related prompts, keeping them together may be clearer than creating separate top-level areas. A stage or concern should receive its own directory only when the amount or kind of material makes that separation useful.

Project-wide contracts and explanations live under `docs/`. The copyable world scaffold lives at `assets/template/`, next to the ignored world workspaces it creates. Other repository directories should be introduced when there is real content to place in them.

## Git Boundary

Everything directly beneath the top-level `assets/` directory is ignored except `assets/template/`. Therefore Git tracks the copyable world scaffold but does not track:

- actual worlds;
- world style guidance and prompt fragments;
- world-shared rigs or animations;
- model concept art and generated files;
- exports and other production artifacts.

Copying `assets/template/` to another name beneath `assets/` creates a fully ignored world workspace. This keeps the template close to the workspaces it creates while preventing large, generated, tool-specific, or world-specific files from entering Git accidentally.
