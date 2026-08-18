# Tools

Ammunae tracks world-agnostic operations after they have been exercised in real model production.

## Available tools

- [Blender tools](blender/README.md)
  - read-only model structure and topology audit;
  - orientation, placement, and scale normalization;
  - creation of configured Warcraft III-derived rigs and Blender Actions.
- [Warcraft III rig adoption](warcraft3/README.md)
  - MDX extraction through a local Retera Model Studio installation;
  - explicit per-rig node, attachment, reference-pose, and Action mappings.

The tools do not contain production models, textures, converted Warcraft assets, or world-shared rigs. Those remain in ignored `assets/<world>/` workspaces. External dependencies such as Blender and Retera Model Studio are installed separately and are not committed.

These operations deliberately do not automate visual acceptance, skin weighting, or arbitrary mesh repair. A human may run them directly or use them with Agent assistance, then perform the applicable visual checks from the [model pipeline](../docs/model-pipeline.md).
