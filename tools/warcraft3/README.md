# Warcraft III Rig Adoption

These tools extract a Classic Warcraft III MDX model into structured JSON and adopt a reviewed subset of its skeleton and animations as a Blender rig.

## Dependencies

`MdxExtract.java` uses the model classes distributed with [Retera Model Studio](https://github.com/Retera/ReterasModelStudio). It was tested with Retera Model Studio 4.6c. Ammunae does not copy or redistribute Retera's JAR files; provide the path to a local installation.

A Java compiler is required. On Windows:

```powershell
$retera = "C:\path\to\ReteraModelStudio_4.6c"
New-Item -ItemType Directory -Force build\mdx-extract | Out-Null
javac -cp "$retera\lib\*" -d build\mdx-extract tools\warcraft3\MdxExtract.java
```

## Extract an MDX model

The reference offset is relative to the beginning of the named animation. For Footman's `Stand - 1`, the sequence starts at 167 ms and the validated reference offset is 167 ms, so the absolute source time is 334 ms.

```powershell
java -cp "build\mdx-extract;$retera\lib\*" MdxExtract `
  C:\wc3-extracted\Units\Human\Footman\Footman.mdx `
  C:\work\footman-source.json `
  "Stand - 1" `
  167 `
  C:\work\footman-cross-check.mdl
```

The optional final argument writes an MDL copy for cross-checking. The JSON contains:

- animation names and sequence intervals;
- an explicit reference animation, relative offset, and absolute source time;
- node names, hierarchy, pivots, flags, animation tracks, and global-sequence lengths;
- reference-pose local and world transforms;
- geosets, vertices, source weights, and reference-pose bounds.

The JSON is a production intermediate and normally remains in the ignored model or world workspace.

## Rig configuration

A rig configuration selects and names the source nodes that form a reusable Ammunae rig. This selection is explicit because MDX node names and helper roles do not reliably reveal anatomy.

[`rigs/footman.json`](rigs/footman.json) is the configuration validated during the first production run. A configuration defines:

- the exact reference animation and sequence-relative offset;
- source and Blender coordinate conventions and target height;
- source nodes, target names, and deform status;
- hierarchy reduction through the nearest selected source parent;
- display-tail hints used only to make Blender bones readable;
- root-motion filtering;
- source animation to Uldum Action mappings and looping behavior.

To adopt a different Warcraft III model, create another reviewed configuration. Do not modify the general converter to encode that model's anatomy, and do not infer attachment or equipment ownership from suffixes alone.

## Create the Blender rig and Actions

Run the Blender entry point after extracting the source:

```powershell
& "C:\Program Files\Blender Foundation\Blender 5.1\blender.exe" `
  --background `
  --python tools\blender\adopt_warcraft3_rig.py `
  -- `
  --source C:\work\footman-source.json `
  --config tools\warcraft3\rigs\footman.json `
  --output C:\work\footman-rig.blend
```

The converter creates the configured rig and Actions only. It does not skin, parent, or otherwise modify a generated mesh. Review the rig and animations visually in Blender before using them as a shared world resource.
