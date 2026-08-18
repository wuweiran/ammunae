import com.hiveworkshop.wc3.gui.animedit.AnimationTimeEnvironmentImpl;
import com.hiveworkshop.wc3.mdl.AnimFlag;
import com.hiveworkshop.wc3.mdl.Animation;
import com.hiveworkshop.wc3.mdl.Bone;
import com.hiveworkshop.wc3.mdl.EditableModel;
import com.hiveworkshop.wc3.mdl.Geoset;
import com.hiveworkshop.wc3.mdl.GeosetVertex;
import com.hiveworkshop.wc3.mdl.GeosetVertexBoneLink;
import com.hiveworkshop.wc3.mdl.IdObject;
import com.hiveworkshop.wc3.mdl.Matrix;
import com.hiveworkshop.wc3.mdl.QuaternionRotation;
import com.hiveworkshop.wc3.mdl.Vertex;
import com.hiveworkshop.wc3.util.MathUtils;
import org.lwjgl.util.vector.Matrix4f;
import org.lwjgl.util.vector.Quaternion;
import org.lwjgl.util.vector.Vector3f;
import org.lwjgl.util.vector.Vector4f;

import java.io.File;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.IdentityHashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;

public final class MdxExtract {
    private MdxExtract() {
    }

    public static void main(String[] args) throws Exception {
        if (args.length < 4 || args.length > 5) {
            System.err.println(
                    "Usage: MdxExtract <source.mdx> <output.json> "
                            + "<reference-animation> <reference-offset-ms> [cross-check.mdl]");
            System.exit(2);
        }

        Locale.setDefault(Locale.ROOT);
        File source = new File(args[0]);
        Path output = Path.of(args[1]);
        String referenceAnimationName = args[2];
        int referenceOffsetMs = Integer.parseInt(args[3]);
        File mdlOutput = args.length == 5 ? new File(args[4]) : null;

        if (!source.isFile()) {
            throw new IllegalArgumentException("MDX source does not exist: " + source);
        }
        if (output.toFile().exists()) {
            throw new IllegalArgumentException("Refusing to overwrite output JSON: " + output);
        }
        if (mdlOutput != null && mdlOutput.exists()) {
            throw new IllegalArgumentException("Refusing to overwrite MDL cross-check: " + mdlOutput);
        }
        if (referenceOffsetMs < 0) {
            throw new IllegalArgumentException("Reference offset must be non-negative");
        }

        Path sourcePath = source.toPath().toAbsolutePath().normalize();
        if (output.toAbsolutePath().normalize().equals(sourcePath)
                || (mdlOutput != null && mdlOutput.toPath().toAbsolutePath().normalize().equals(sourcePath))) {
            throw new IllegalArgumentException("Output paths must differ from the source MDX");
        }

        Path outputParent = output.toAbsolutePath().getParent();
        if (outputParent != null) {
            Files.createDirectories(outputParent);
        }
        if (mdlOutput != null) {
            Path mdlParent = mdlOutput.toPath().toAbsolutePath().getParent();
            if (mdlParent != null) {
                Files.createDirectories(mdlParent);
            }
        }

        EditableModel model = EditableModel.read(source);
        if (model == null) {
            throw new IllegalStateException("Retera failed to read " + source);
        }
        model.updateIdObjectReferences();
        for (Geoset geoset : model.getGeosets()) {
            geoset.updateToObjects(model);
        }

        Animation referenceAnimation = findAnimation(model, referenceAnimationName);
        int referenceSourceTime = referenceAnimation.getStart() + referenceOffsetMs;
        if (referenceSourceTime > referenceAnimation.getEnd()) {
            throw new IllegalArgumentException(
                    "Reference source time " + referenceSourceTime
                            + " is outside animation interval ["
                            + referenceAnimation.getStart() + ", "
                            + referenceAnimation.getEnd() + "]");
        }

        AnimationTimeEnvironmentImpl environment = new AnimationTimeEnvironmentImpl();
        environment.setAnimation(referenceAnimation);
        // Retera's animation environment takes sequence-relative time and adds the
        // sequence start internally. Keep the absolute source time explicit in JSON.
        environment.setCurrentTime(referenceOffsetMs);

        IdentityHashMap<IdObject, Sample> referenceSamples = new IdentityHashMap<>();
        for (IdObject node : model.getIdObjects()) {
            sampleNode(node, environment, referenceSamples);
        }

        Map<String, Object> root = new LinkedHashMap<>();
        root.put("schema", 2);
        root.put("source", source.getCanonicalPath());
        root.put("name", model.getName());
        root.put("formatVersion", model.getFormatVersion());
        root.put("blendTime", model.getBlendTime());
        root.put("counts", mapOf(
                "animations", model.getAnimsSize(),
                "idObjects", model.getIdObjectsSize(),
                "geosets", model.getGeosetsSize(),
                "bones", model.countIdObjectsOfClass(Bone.class)));

        List<Object> animations = new ArrayList<>();
        for (Animation animation : model.getAnims()) {
            animations.add(mapOf(
                    "name", animation.getName(),
                    "start", animation.getStart(),
                    "end", animation.getEnd(),
                    "length", animation.length(),
                    "nonLooping", animation.isNonLooping(),
                    "moveSpeed", animation.getMoveSpeed(),
                    "rarity", animation.getRarity()));
        }
        root.put("animations", animations);
        root.put("globalSequences", new ArrayList<>(model.getGlobalSeqs()));
        root.put("referencePose", mapOf(
                "animation", referenceAnimation.getName(),
                "offsetMs", referenceOffsetMs,
                "sourceTimeMs", referenceSourceTime,
                "interval", listOf(referenceAnimation.getStart(), referenceAnimation.getEnd())));

        List<Object> nodes = new ArrayList<>();
        for (IdObject node : model.getIdObjects()) {
            Sample sample = referenceSamples.get(node);
            List<Object> tracks = new ArrayList<>();
            for (AnimFlag flag : node.getAnimFlags()) {
                List<Object> entries = new ArrayList<>();
                List<Integer> times = flag.getTimes();
                List values = flag.getValues();
                List inTans = flag.getInTans();
                List outTans = flag.getOutTans();
                for (int index = 0; index < times.size(); index++) {
                    Map<String, Object> entry = new LinkedHashMap<>();
                    entry.put("time", times.get(index));
                    entry.put("value", encodeValue(values.get(index)));
                    if (index < inTans.size()) {
                        entry.put("inTan", encodeValue(inTans.get(index)));
                    }
                    if (index < outTans.size()) {
                        entry.put("outTan", encodeValue(outTans.get(index)));
                    }
                    entries.add(entry);
                }
                Integer globalSequenceId = flag.hasGlobalSeq() ? flag.getGlobalSeqId() : null;
                Integer globalSequenceLength = globalSequenceId == null
                        ? null
                        : model.getGlobalSeq(globalSequenceId);
                tracks.add(mapOf(
                        "name", flag.getName(),
                        "typeId", flag.getTypeId(),
                        "interpolation", AnimFlag.getInterpType(flag.getInterpType()),
                        "globalSequenceId", globalSequenceId,
                        "globalSequenceLength", globalSequenceLength,
                        "entries", entries));
            }

            Map<String, Object> nodeJson = new LinkedHashMap<>();
            nodeJson.put("name", node.getName());
            nodeJson.put("class", node.getClass().getSimpleName());
            nodeJson.put("objectId", node.getObjectId());
            nodeJson.put("parentId", node.getParentId());
            nodeJson.put("parent", node.getParent() == null ? null : node.getParent().getName());
            nodeJson.put("pivot", vertex(node.getPivotPoint()));
            nodeJson.put("flags", new ArrayList<>(node.getFlags()));
            nodeJson.put("base", mapOf(
                    "localTranslation", vertex(Vertex.ORIGIN),
                    "localRotationXyzw", quaternion(AnimFlag.ROTATE_IDENTITY),
                    "localScale", vertex(AnimFlag.SCALE_IDENTITY),
                    "worldMatrix", matrix(identityWorld(node, new IdentityHashMap<>()))));
            nodeJson.put("reference", mapOf(
                    "localTranslation", vertex(sample.translation),
                    "localRotationXyzw", quaternion(sample.rotation),
                    "localScale", vertex(sample.scale),
                    "worldMatrix", matrix(sample.worldMatrix),
                    "worldPivot", worldPivot(sample.worldMatrix, node.getPivotPoint())));
            nodeJson.put("tracks", tracks);
            if (node instanceof Bone) {
                Bone bone = (Bone) node;
                nodeJson.put("boneGeosetId", bone.getGeosetId());
                nodeJson.put("boneGeosetAnimId", bone.getGeosetAnimId());
            }
            nodes.add(nodeJson);
        }
        root.put("nodes", nodes);

        double minX = Double.POSITIVE_INFINITY;
        double minY = Double.POSITIVE_INFINITY;
        double minZ = Double.POSITIVE_INFINITY;
        double maxX = Double.NEGATIVE_INFINITY;
        double maxY = Double.NEGATIVE_INFINITY;
        double maxZ = Double.NEGATIVE_INFINITY;
        double referenceMinX = Double.POSITIVE_INFINITY;
        double referenceMinY = Double.POSITIVE_INFINITY;
        double referenceMinZ = Double.POSITIVE_INFINITY;
        double referenceMaxX = Double.NEGATIVE_INFINITY;
        double referenceMaxY = Double.NEGATIVE_INFINITY;
        double referenceMaxZ = Double.NEGATIVE_INFINITY;
        int totalVertices = 0;
        int totalTriangles = 0;
        List<Object> geosets = new ArrayList<>();
        for (int geosetIndex = 0; geosetIndex < model.getGeosetsSize(); geosetIndex++) {
            Geoset geoset = model.getGeoset(geosetIndex);
            List<Object> vertices = new ArrayList<>();
            for (int vertexIndex = 0; vertexIndex < geoset.numVerteces(); vertexIndex++) {
                GeosetVertex sourceVertex = geoset.getVertex(vertexIndex);
                minX = Math.min(minX, sourceVertex.x);
                minY = Math.min(minY, sourceVertex.y);
                minZ = Math.min(minZ, sourceVertex.z);
                maxX = Math.max(maxX, sourceVertex.x);
                maxY = Math.max(maxY, sourceVertex.y);
                maxZ = Math.max(maxZ, sourceVertex.z);
                List<Object> links = new ArrayList<>();
                List<WeightedBone> weightedBones = new ArrayList<>();
                for (GeosetVertexBoneLink link : sourceVertex.getLinks()) {
                    links.add(mapOf("bone", link.getBone().getName(), "weight", (int) link.getWeight()));
                    weightedBones.add(new WeightedBone(link.getBone(), link.getWeight() / 255.0));
                }
                Matrix matrixRef = sourceVertex.getMatrixRef();
                List<Object> matrixBones = new ArrayList<>();
                if (matrixRef != null && matrixRef.getBones() != null) {
                    List<Bone> bones = matrixRef.getBones();
                    double matrixWeight = bones.isEmpty() ? 0.0 : 1.0 / bones.size();
                    for (Bone bone : bones) {
                        matrixBones.add(bone.getName());
                        if (weightedBones.isEmpty()) {
                            weightedBones.add(new WeightedBone(bone, matrixWeight));
                        }
                    }
                }
                Vertex referencePosition = skinVertex(sourceVertex, weightedBones, referenceSamples);
                referenceMinX = Math.min(referenceMinX, referencePosition.x);
                referenceMinY = Math.min(referenceMinY, referencePosition.y);
                referenceMinZ = Math.min(referenceMinZ, referencePosition.z);
                referenceMaxX = Math.max(referenceMaxX, referencePosition.x);
                referenceMaxY = Math.max(referenceMaxY, referencePosition.y);
                referenceMaxZ = Math.max(referenceMaxZ, referencePosition.z);
                vertices.add(mapOf(
                        "index", vertexIndex,
                        "position", vertex(sourceVertex),
                        "referencePosition", vertex(referencePosition),
                        "vertexGroup", sourceVertex.getVertexGroup(),
                        "links", links,
                        "matrixBones", matrixBones));
            }
            totalVertices += geoset.numVerteces();
            totalTriangles += geoset.numTriangles();
            geosets.add(mapOf(
                    "index", geosetIndex,
                    "name", geoset.getName(),
                    "materialId", geoset.getMaterialID(),
                    "vertexCount", geoset.numVerteces(),
                    "triangleCount", geoset.numTriangles(),
                    "vertices", vertices));
        }
        root.put("mesh", mapOf(
                "vertexCount", totalVertices,
                "triangleCount", totalTriangles,
                "bounds", bounds(minX, minY, minZ, maxX, maxY, maxZ),
                "referenceBounds", bounds(
                        referenceMinX, referenceMinY, referenceMinZ,
                        referenceMaxX, referenceMaxY, referenceMaxZ),
                "geosets", geosets));

        Path parent = output.toAbsolutePath().getParent();
        if (parent != null) {
            Files.createDirectories(parent);
        }
        Files.writeString(output, Json.write(root), StandardCharsets.UTF_8);
        if (mdlOutput != null) {
            model.printTo(mdlOutput, false);
        }

        Map<String, Object> summary = mapOf(
                "output", output.toAbsolutePath().toString(),
                "mdlCrossCheck", mdlOutput == null ? null : mdlOutput.getAbsolutePath(),
                "referenceAnimation", referenceAnimation.getName(),
                "referenceOffsetMs", referenceOffsetMs,
                "referenceSourceTimeMs", referenceSourceTime,
                "nodes", model.getIdObjectsSize(),
                "vertices", totalVertices,
                "triangles", totalTriangles);
        System.out.println(Json.write(summary));
    }

    private static Animation findAnimation(EditableModel model, String name) {
        for (Animation animation : model.getAnims()) {
            if (name.equals(animation.getName())) {
                return animation;
            }
        }
        throw new IllegalArgumentException("Reference animation was not found: " + name);
    }

    private static Map<String, Object> bounds(
            double minX, double minY, double minZ,
            double maxX, double maxY, double maxZ) {
        return mapOf(
                "min", listOf(minX, minY, minZ),
                "max", listOf(maxX, maxY, maxZ),
                "dimensions", listOf(maxX - minX, maxY - minY, maxZ - minZ));
    }

    private static Sample sampleNode(
            IdObject node,
            AnimationTimeEnvironmentImpl environment,
            IdentityHashMap<IdObject, Sample> samples) {
        Sample existing = samples.get(node);
        if (existing != null) {
            return existing;
        }
        Vertex translation = node.getRenderTranslation(environment);
        QuaternionRotation rotation = node.getRenderRotation(environment);
        Vertex scale = node.getRenderScale(environment);
        if (translation == null) translation = Vertex.ORIGIN;
        if (rotation == null) rotation = AnimFlag.ROTATE_IDENTITY;
        if (scale == null) scale = AnimFlag.SCALE_IDENTITY;

        Matrix4f local = new Matrix4f();
        Quaternion lwjglRotation = new Quaternion(
                (float) rotation.a,
                (float) rotation.b,
                (float) rotation.c,
                (float) rotation.d);
        Vector3f lwjglTranslation = new Vector3f(
                (float) translation.x,
                (float) translation.y,
                (float) translation.z);
        Vector3f lwjglScale = new Vector3f(
                (float) scale.x,
                (float) scale.y,
                (float) scale.z);
        Vertex pivot = node.getPivotPoint();
        Vector3f lwjglPivot = new Vector3f((float) pivot.x, (float) pivot.y, (float) pivot.z);
        MathUtils.fromRotationTranslationScaleOrigin(
                lwjglRotation, lwjglTranslation, lwjglScale, local, lwjglPivot);

        Matrix4f world = new Matrix4f();
        if (node.getParent() == null) {
            world.load(local);
        } else {
            Sample parent = sampleNode((IdObject) node.getParent(), environment, samples);
            Matrix4f.mul(parent.worldMatrix, local, world);
        }
        Sample sample = new Sample(translation, rotation, scale, world);
        samples.put(node, sample);
        return sample;
    }

    private static Matrix4f identityWorld(IdObject node, IdentityHashMap<IdObject, Matrix4f> cache) {
        Matrix4f existing = cache.get(node);
        if (existing != null) return existing;
        Matrix4f local = new Matrix4f();
        local.setIdentity();
        Matrix4f world = new Matrix4f();
        if (node.getParent() == null) {
            world.load(local);
        } else {
            Matrix4f.mul(identityWorld((IdObject) node.getParent(), cache), local, world);
        }
        cache.put(node, world);
        return world;
    }

    private static List<Object> vertex(Vertex value) {
        return listOf(value.x, value.y, value.z);
    }

    private static List<Object> quaternion(QuaternionRotation value) {
        return listOf(value.a, value.b, value.c, value.d);
    }

    private static List<Object> matrix(Matrix4f value) {
        return listOf(
                listOf(value.m00, value.m10, value.m20, value.m30),
                listOf(value.m01, value.m11, value.m21, value.m31),
                listOf(value.m02, value.m12, value.m22, value.m32),
                listOf(value.m03, value.m13, value.m23, value.m33));
    }

    private static List<Object> worldPivot(Matrix4f matrix, Vertex pivot) {
        Vector4f source = new Vector4f((float) pivot.x, (float) pivot.y, (float) pivot.z, 1.0f);
        Vector4f result = Matrix4f.transform(matrix, source, null);
        return listOf(result.x, result.y, result.z);
    }

    private static Vertex skinVertex(
            GeosetVertex sourceVertex,
            List<WeightedBone> weightedBones,
            IdentityHashMap<IdObject, Sample> samples) {
        if (weightedBones.isEmpty()) {
            return new Vertex(sourceVertex);
        }
        double x = 0.0;
        double y = 0.0;
        double z = 0.0;
        double totalWeight = 0.0;
        for (WeightedBone weightedBone : weightedBones) {
            Sample sample = samples.get(weightedBone.bone);
            if (sample == null || weightedBone.weight <= 0.0) continue;
            Vector4f source = new Vector4f(
                    (float) sourceVertex.x,
                    (float) sourceVertex.y,
                    (float) sourceVertex.z,
                    1.0f);
            Vector4f result = Matrix4f.transform(sample.worldMatrix, source, null);
            x += result.x * weightedBone.weight;
            y += result.y * weightedBone.weight;
            z += result.z * weightedBone.weight;
            totalWeight += weightedBone.weight;
        }
        if (totalWeight <= 0.0) {
            return new Vertex(sourceVertex);
        }
        return new Vertex(x / totalWeight, y / totalWeight, z / totalWeight);
    }

    private static Object encodeValue(Object value) {
        if (value == null || value instanceof Number || value instanceof Boolean || value instanceof String) {
            return value;
        }
        if (value instanceof Vertex) {
            return vertex((Vertex) value);
        }
        if (value instanceof QuaternionRotation) {
            return quaternion((QuaternionRotation) value);
        }
        return value.toString();
    }

    private static Map<String, Object> mapOf(Object... values) {
        LinkedHashMap<String, Object> map = new LinkedHashMap<>();
        for (int index = 0; index < values.length; index += 2) {
            map.put((String) values[index], values[index + 1]);
        }
        return map;
    }

    private static List<Object> listOf(Object... values) {
        ArrayList<Object> list = new ArrayList<>();
        for (Object value : values) list.add(value);
        return list;
    }

    private static final class WeightedBone {
        final Bone bone;
        final double weight;

        WeightedBone(Bone bone, double weight) {
            this.bone = bone;
            this.weight = weight;
        }
    }

    private static final class Sample {
        final Vertex translation;
        final QuaternionRotation rotation;
        final Vertex scale;
        final Matrix4f worldMatrix;

        Sample(Vertex translation, QuaternionRotation rotation, Vertex scale, Matrix4f worldMatrix) {
            this.translation = translation;
            this.rotation = rotation;
            this.scale = scale;
            this.worldMatrix = worldMatrix;
        }
    }

    private static final class Json {
        static String write(Object value) {
            StringBuilder builder = new StringBuilder();
            append(builder, value, 0);
            builder.append('\n');
            return builder.toString();
        }

        private static void append(StringBuilder builder, Object value, int indent) {
            if (value == null) {
                builder.append("null");
            } else if (value instanceof String) {
                quote(builder, (String) value);
            } else if (value instanceof Boolean || value instanceof Byte
                    || value instanceof Short || value instanceof Integer || value instanceof Long) {
                builder.append(value);
            } else if (value instanceof Number) {
                double number = ((Number) value).doubleValue();
                if (Double.isFinite(number)) builder.append(String.format(Locale.ROOT, "%.9g", number));
                else builder.append("null");
            } else if (value instanceof Map) {
                Map<?, ?> map = (Map<?, ?>) value;
                builder.append("{");
                boolean first = true;
                for (Map.Entry<?, ?> entry : map.entrySet()) {
                    if (!first) builder.append(",");
                    builder.append("\n");
                    spaces(builder, indent + 2);
                    quote(builder, String.valueOf(entry.getKey()));
                    builder.append(": ");
                    append(builder, entry.getValue(), indent + 2);
                    first = false;
                }
                if (!map.isEmpty()) {
                    builder.append("\n");
                    spaces(builder, indent);
                }
                builder.append("}");
            } else if (value instanceof Iterable) {
                builder.append("[");
                boolean first = true;
                for (Object element : (Iterable<?>) value) {
                    if (!first) builder.append(",");
                    builder.append("\n");
                    spaces(builder, indent + 2);
                    append(builder, element, indent + 2);
                    first = false;
                }
                if (!first) {
                    builder.append("\n");
                    spaces(builder, indent);
                }
                builder.append("]");
            } else {
                quote(builder, String.valueOf(value));
            }
        }

        private static void quote(StringBuilder builder, String value) {
            builder.append('"');
            for (int index = 0; index < value.length(); index++) {
                char character = value.charAt(index);
                switch (character) {
                    case '"': builder.append("\\\""); break;
                    case '\\': builder.append("\\\\"); break;
                    case '\b': builder.append("\\b"); break;
                    case '\f': builder.append("\\f"); break;
                    case '\n': builder.append("\\n"); break;
                    case '\r': builder.append("\\r"); break;
                    case '\t': builder.append("\\t"); break;
                    default:
                        if (character < 0x20) {
                            builder.append(String.format(Locale.ROOT, "\\u%04x", (int) character));
                        } else {
                            builder.append(character);
                        }
                }
            }
            builder.append('"');
        }

        private static void spaces(StringBuilder builder, int count) {
            for (int index = 0; index < count; index++) builder.append(' ');
        }
    }
}
