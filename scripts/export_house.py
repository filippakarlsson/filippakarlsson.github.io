"""Prepare the authored Blender house for the web and export one GLB.

The source .blend is opened read-only for this process. Semantic hitboxes and
runtime light anchors exist only in memory and in the exported GLB; the source
file is never saved or modified.
"""

import argparse
import os
import sys

import bpy


ROOMS = (
    ("BASEMENT", "Basement", (0.0, -1.72, 1.07), (7.45, 0.10, 1.62)),
    ("WELCOME", "Welcome", (0.0, -1.72, 2.85), (7.45, 0.10, 1.62)),
    ("PLAYROOM", "Playroom", (0.0, -1.72, 4.63), (7.45, 0.10, 1.62)),
    ("OFFICE", "Office", (0.0, -1.72, 6.41), (7.45, 0.10, 1.62)),
    ("STUDIO", "Studio", (0.0, -1.72, 8.19), (7.45, 0.10, 1.62)),
    ("ROOFTOP", "Rooftop", (0.0, -2.18, 9.76), (7.45, 0.10, 1.34)),
)


def parse_args():
    raw_args = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--output", required=True)
    return parser.parse_args(raw_args)


def hex_color(rgb):
    channels = [max(0, min(255, round(float(channel) * 255))) for channel in rgb]
    return "#" + "".join(f"{channel:02x}" for channel in channels)


def replace_runtime_lights_with_anchors():
    runtime_lights = []
    for obj in list(bpy.data.objects):
        if obj.type != "LIGHT":
            continue

        if "_HOVER_LIGHT" in obj.name or "_HOVER_ACCENT_LIGHT" in obj.name:
            properties = {key: obj[key] for key in obj.keys()}
            runtime_lights.append(
                {
                    "name": obj.name,
                    "matrix_world": obj.matrix_world.copy(),
                    "color": tuple(obj.data.color),
                    "properties": properties,
                }
            )

        # Global Blender render lights are deliberately replaced by a small,
        # predictable Three.js lighting rig. Room point lights become anchors.
        bpy.data.objects.remove(obj, do_unlink=True)

    for light in runtime_lights:
        anchor = bpy.data.objects.new(light["name"], None)
        bpy.context.scene.collection.objects.link(anchor)
        anchor.empty_display_type = "PLAIN_AXES"
        anchor.empty_display_size = 0.12
        anchor.matrix_world = light["matrix_world"]
        anchor["runtimeLight"] = "point"
        anchor["lightColor"] = hex_color(light["color"])

        for key, value in light["properties"].items():
            anchor[key] = value

        if "floor" in light["properties"]:
            anchor["roomId"] = str(light["properties"]["floor"]).lower()
        elif "hover_parent" in light["properties"]:
            anchor["roomId"] = str(light["properties"]["hover_parent"]).split("_")[0].lower()


def create_hitboxes():
    material = bpy.data.materials.get("WEB_HITBOX_MATERIAL") or bpy.data.materials.new("WEB_HITBOX_MATERIAL")
    material.diffuse_color = (1.0, 1.0, 1.0, 0.001)
    material.use_nodes = True
    principled = material.node_tree.nodes.get("Principled BSDF")
    if principled:
        principled.inputs["Base Color"].default_value = (1.0, 1.0, 1.0, 1.0)
        principled.inputs["Alpha"].default_value = 0.001
        principled.inputs["Roughness"].default_value = 1.0
    if hasattr(material, "surface_render_method"):
        material.surface_render_method = "DITHERED"

    for room_id, label, location, size in ROOMS:
        bpy.ops.mesh.primitive_cube_add(location=location)
        hitbox = bpy.context.object
        hitbox.name = f"HITBOX_{room_id}"
        hitbox.scale = tuple(dimension / 2 for dimension in size)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        hitbox.data.materials.append(material)
        hitbox["interaction"] = "room"
        hitbox["roomId"] = room_id.lower()
        hitbox["label"] = label


def material_is_transparent(material):
    if material is None or float(material.diffuse_color[3]) < 0.999:
        return True
    if not material.use_nodes or material.node_tree is None:
        return False

    for node in material.node_tree.nodes:
        if node.type != "BSDF_PRINCIPLED":
            continue
        alpha = node.inputs.get("Alpha")
        transmission = node.inputs.get("Transmission Weight") or node.inputs.get("Transmission")
        if alpha and float(alpha.default_value) < 0.999:
            return True
        if transmission and float(transmission.default_value) > 0.001:
            return True
    return False


def remove_duplicate_soft_bevels():
    """Remove accidental repeated copies of the same web-detail bevel.

    Re-running the Blender enhancement workflow can append modifiers named
    `Soft miniature edges.001`, `.002`, and so on. Stacking identical bevels
    grows a simple handrail into millions of triangles. Keep the authored base
    modifier and any separately named bevels, and remove only its duplicates in
    the temporary export scene.
    """
    removed = 0
    affected = 0
    for obj in bpy.data.objects:
        if obj.type != "MESH":
            continue
        duplicates = [
            modifier
            for modifier in obj.modifiers
            if modifier.type == "BEVEL" and modifier.name.startswith("Soft miniature edges.")
        ]
        if not duplicates:
            continue
        for modifier in duplicates:
            obj.modifiers.remove(modifier)
            removed += 1
        affected += 1
    print(f"WEB_BEVEL_CLEANUP_OK affected_objects={affected} removed_modifiers={removed}")


def batch_static_meshes():
    """Join compatible opaque meshes by material before export.

    This keeps every vertex, UV and normal intact, but turns hundreds of tiny
    Blender objects into a small number of web render batches. Interactive
    hitboxes, animated lamp parts, glass and modified meshes stay separate.
    """
    animated_names = set()
    for obj in bpy.data.objects:
        if obj.get("runtimeLight") != "point":
            continue
        for key in ("shade_object", "outer_shade_object"):
            value = obj.get(key)
            if isinstance(value, str):
                animated_names.add(value)

    # Bake the same evaluated geometry that glTF's `export_apply` would create,
    # but do it before batching so bevels and curve geometry can be joined too.
    convertible = []
    for obj in list(bpy.context.scene.objects):
        if obj.type not in {"MESH", "CURVE", "SURFACE", "FONT"} or obj.hide_render:
            continue
        if obj.name in animated_names or obj.get("interaction") or obj.get("runtimeLight"):
            continue
        if obj.animation_data or obj.data.animation_data or obj.constraints:
            continue
        if obj.type == "MESH" and obj.data.shape_keys:
            continue
        if len(obj.material_slots) != 1 or obj.name not in bpy.context.view_layer.objects:
            continue
        convertible.append(obj)

    bpy.ops.object.select_all(action="DESELECT")
    for obj in convertible:
        obj.select_set(True)
    if convertible:
        bpy.context.view_layer.objects.active = convertible[0]
        bpy.ops.object.convert(target="MESH")

    groups = {}
    source_count = 0
    for obj in list(bpy.context.scene.objects):
        if obj.type != "MESH" or obj.hide_render:
            continue
        source_count += 1
        if obj.name in animated_names or obj.get("interaction") or obj.get("runtimeLight"):
            continue
        if obj.animation_data or obj.data.animation_data or obj.data.shape_keys:
            continue
        if obj.constraints or len(obj.material_slots) != 1:
            continue

        material = obj.material_slots[0].material
        if material_is_transparent(material):
            continue
        groups.setdefault(material, []).append(obj)

    bpy.ops.object.select_all(action="DESELECT")
    batch_count = 0
    joined_source_count = 0
    for material, objects in groups.items():
        live_objects = [obj for obj in objects if obj.name in bpy.context.view_layer.objects]
        if len(live_objects) < 2:
            continue

        # A child may be a semantic empty or an excluded lamp mesh. Preserve
        # its exact world transform before its static parent is joined.
        for obj in live_objects:
            for child in list(obj.children):
                world_matrix = child.matrix_world.copy()
                child.parent = None
                child.matrix_world = world_matrix

        bpy.ops.object.select_all(action="DESELECT")
        for obj in live_objects:
            obj.select_set(True)
        active = live_objects[0]
        bpy.context.view_layer.objects.active = active
        bpy.ops.object.join()
        batch_count += 1
        joined_source_count += len(live_objects)
        active.name = f"WEB_BATCH_{batch_count:03d}_{material.name[:36]}"

    final_count = sum(1 for obj in bpy.context.scene.objects if obj.type == "MESH" and not obj.hide_render)
    print(
        "WEB_BATCH_OK "
        f"source_meshes={source_count} final_meshes={final_count} "
        f"batches={batch_count} joined_sources={joined_source_count}"
    )


def validate_scene():
    missing = []
    for room_id, _label, _location, _size in ROOMS:
        for required_name in (
            f"{room_id}_HOVER_LIGHT",
            f"{room_id}_LAMP_BULB",
            f"HITBOX_{room_id}",
        ):
            if bpy.data.objects.get(required_name) is None:
                missing.append(required_name)

    if missing:
        raise RuntimeError("Scene is missing required web objects: " + ", ".join(missing))


def main():
    args = parse_args()
    source = os.path.abspath(args.source)
    output = os.path.abspath(args.output)

    if not os.path.isfile(source):
        raise FileNotFoundError(source)

    bpy.ops.wm.open_mainfile(filepath=source)
    remove_duplicate_soft_bevels()
    replace_runtime_lights_with_anchors()
    create_hitboxes()
    validate_scene()
    batch_static_meshes()

    os.makedirs(os.path.dirname(output), exist_ok=True)
    bpy.ops.export_scene.gltf(
        filepath=output,
        export_format="GLB",
        export_apply=True,
        export_animations=False,
        export_cameras=True,
        export_extras=True,
        export_lights=False,
        export_materials="EXPORT",
        export_meshopt_compression_enable=True,
        export_meshopt_extension="EXT_meshopt_compression",
        export_normals=True,
        export_tangents=False,
        export_texcoords=True,
        export_yup=True,
        use_renderable=True,
    )

    hitbox_count = sum(1 for obj in bpy.data.objects if obj.name.startswith("HITBOX_"))
    anchor_count = sum(1 for obj in bpy.data.objects if obj.get("runtimeLight") == "point")
    print(f"WEB_EXPORT_OK output={output} hitboxes={hitbox_count} light_anchors={anchor_count}")


if __name__ == "__main__":
    main()
