"""Non-destructive visual finishing pass for the existing portfolio house.

This script deliberately does not create, delete, move, rotate, or scale any
house/furniture object.  It only refines material response, render settings,
and the existing presentation lighting, then saves the currently open blend.
"""

import colorsys
import math
import os

import bpy
from mathutils import Vector


BLEND_PATH = "/Users/filippakarlsson/Desktop/filippa_house_reference_rebuilt.blend"
RENDER_PATH = "/Users/filippakarlsson/Desktop/filippa_house_reference_rebuilt.png"
FINISH_PREFIX = "FINISH__"


def principled(material):
    if not material or not material.use_nodes or not material.node_tree:
        return None
    return next(
        (node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED"),
        None,
    )


def set_input(shader, name, value):
    if shader and name in shader.inputs:
        shader.inputs[name].default_value = value


def set_color(material, rgba):
    rgba = tuple(rgba[:3]) + (rgba[3] if len(rgba) > 3 else 1.0,)
    material.diffuse_color = rgba
    shader = principled(material)
    set_input(shader, "Base Color", rgba)


def adjusted_color(rgba, saturation=1.0, value=1.0):
    r, g, b = rgba[:3]
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    r, g, b = colorsys.hsv_to_rgb(
        h,
        max(0.0, min(1.0, s * saturation)),
        max(0.0, min(1.0, v * value)),
    )
    return (r, g, b, rgba[3] if len(rgba) > 3 else 1.0)


def clear_finish_nodes(material):
    if not material.use_nodes or not material.node_tree:
        return
    for node in list(material.node_tree.nodes):
        if node.label == "HOUSE_FINISH":
            material.node_tree.nodes.remove(node)


def add_micro_bump(material, scale, detail, strength, distance):
    """Add restrained procedural surface variation without changing geometry."""
    shader = principled(material)
    if not shader:
        return
    clear_finish_nodes(material)
    nodes = material.node_tree.nodes
    links = material.node_tree.links

    texcoord = nodes.new("ShaderNodeTexCoord")
    texcoord.name = f"{FINISH_PREFIX}Texture Coordinates"
    texcoord.label = "HOUSE_FINISH"

    noise = nodes.new("ShaderNodeTexNoise")
    noise.name = f"{FINISH_PREFIX}Micro Surface"
    noise.label = "HOUSE_FINISH"
    noise.noise_dimensions = "3D"
    noise.inputs["Scale"].default_value = scale
    noise.inputs["Detail"].default_value = detail
    noise.inputs["Roughness"].default_value = 0.55

    bump = nodes.new("ShaderNodeBump")
    bump.name = f"{FINISH_PREFIX}Micro Bump"
    bump.label = "HOUSE_FINISH"
    bump.inputs["Strength"].default_value = strength
    bump.inputs["Distance"].default_value = distance

    links.new(texcoord.outputs["Generated"], noise.inputs["Vector"])
    links.new(noise.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], shader.inputs["Normal"])


def original_material(material):
    if material and material.name.startswith(FINISH_PREFIX):
        source_name = material.get("finish_source_material")
        if source_name and source_name in bpy.data.materials:
            return bpy.data.materials[source_name]
    return material


variant_cache = {}


def material_variant(source, category):
    source = original_material(source)
    if not source:
        return None
    key = (source.name, category)
    if key in variant_cache:
        return variant_cache[key]

    name = f"{FINISH_PREFIX}{category.upper()}__{source.name}"
    material = bpy.data.materials.get(name)
    if material is None:
        material = source.copy()
        material.name = name
    material["finish_source_material"] = source.name
    material["finish_category"] = category
    material.use_nodes = True
    material.diffuse_color = source.diffuse_color
    shader = principled(material)

    # Reset the key Principled controls before applying the category response.
    set_input(shader, "Metallic", 0.0)
    set_input(shader, "Coat Weight", 0.0)
    set_input(shader, "Sheen Weight", 0.0)
    set_input(shader, "Subsurface Weight", 0.0)
    set_input(shader, "Transmission Weight", 0.0)
    set_input(shader, "Alpha", 1.0)
    clear_finish_nodes(material)

    if category == "wall":
        set_color(material, adjusted_color(source.diffuse_color, 1.16, 0.86))
        set_input(shader, "Roughness", 0.80)
        set_input(shader, "Specular IOR Level", 0.34)
        add_micro_bump(material, 9.0, 3.2, 0.10, 0.030)
    elif category == "painted":
        set_color(material, adjusted_color(source.diffuse_color, 1.10, 0.91))
        set_input(shader, "Roughness", 0.52)
        set_input(shader, "Coat Weight", 0.10)
        set_input(shader, "Coat Roughness", 0.28)
    elif category == "structure":
        set_color(material, adjusted_color(source.diffuse_color, 1.02, 0.94))
        set_input(shader, "Roughness", 0.64)
        set_input(shader, "Coat Weight", 0.04)
        add_micro_bump(material, 11.0, 2.0, 0.045, 0.018)
    elif category == "fabric":
        set_color(material, adjusted_color(source.diffuse_color, 1.10, 0.90))
        set_input(shader, "Roughness", 0.84)
        set_input(shader, "Sheen Weight", 0.16)
        set_input(shader, "Sheen Roughness", 0.55)
        add_micro_bump(material, 52.0, 2.3, 0.16, 0.010)
    elif category == "wood":
        set_color(material, adjusted_color(source.diffuse_color, 1.12, 0.88))
        set_input(shader, "Roughness", 0.42)
        set_input(shader, "Coat Weight", 0.07)
        set_input(shader, "Coat Roughness", 0.30)
        add_micro_bump(material, 5.0, 3.0, 0.075, 0.022)
    elif category == "plastic":
        set_color(material, adjusted_color(source.diffuse_color, 1.13, 0.91))
        set_input(shader, "Roughness", 0.38)
        set_input(shader, "Coat Weight", 0.16)
        set_input(shader, "Coat Roughness", 0.24)
    elif category == "ceramic":
        set_color(material, adjusted_color(source.diffuse_color, 1.06, 0.93))
        set_input(shader, "Roughness", 0.31)
        set_input(shader, "Coat Weight", 0.20)
        set_input(shader, "Coat Roughness", 0.20)
    elif category == "paper":
        set_color(material, adjusted_color(source.diffuse_color, 1.08, 0.93))
        set_input(shader, "Roughness", 0.78)
        set_input(shader, "Specular IOR Level", 0.28)
    elif category == "plant":
        set_color(material, adjusted_color(source.diffuse_color, 1.16, 0.84))
        set_input(shader, "Roughness", 0.53)
        set_input(shader, "Sheen Weight", 0.08)
        set_input(shader, "Subsurface Weight", 0.025)
    elif category == "metal":
        set_color(material, adjusted_color(source.diffuse_color, 1.00, 0.76))
        set_input(shader, "Metallic", 0.78)
        set_input(shader, "Roughness", 0.27)
    elif category == "mirror":
        set_color(material, adjusted_color(source.diffuse_color, 0.85, 0.88))
        set_input(shader, "Metallic", 0.95)
        set_input(shader, "Roughness", 0.12)
    elif category == "glass":
        set_color(material, adjusted_color(source.diffuse_color, 0.90, 0.88))
        set_input(shader, "Roughness", 0.14)
        set_input(shader, "IOR", 1.45)
        set_input(shader, "Transmission Weight", 0.70)
        set_input(shader, "Alpha", 0.38)
        material.diffuse_color = (*material.diffuse_color[:3], 0.38)
        material.surface_render_method = "DITHERED"
    elif category == "roof":
        set_color(material, adjusted_color(source.diffuse_color, 1.18, 0.84))
        set_input(shader, "Roughness", 0.49)
        set_input(shader, "Coat Weight", 0.05)
        add_micro_bump(material, 14.0, 3.0, 0.09, 0.022)
    elif category == "soil":
        set_color(material, adjusted_color(source.diffuse_color, 1.08, 0.72))
        set_input(shader, "Roughness", 0.96)
        add_micro_bump(material, 18.0, 3.0, 0.20, 0.025)
    elif category == "screen":
        set_color(material, adjusted_color(source.diffuse_color, 1.0, 0.70))
        set_input(shader, "Roughness", 0.16)
        set_input(shader, "Coat Weight", 0.25)
        set_input(shader, "Coat Roughness", 0.18)
    else:
        set_input(shader, "Roughness", 0.48)

    variant_cache[key] = material
    return material


def object_category(obj, source_material):
    name = obj.name.upper()
    mat_name = source_material.name.lower()

    if "HOVER_BULB_MATERIAL" in source_material.name or "HOVER_SHADE_MATERIAL" in source_material.name:
        return None
    if "WINDOW_GLASS" in name or mat_name == "window glass":
        return "glass"
    if "MIRROR_GLASS" in name or mat_name == "mirror silver":
        return "mirror"
    if mat_name == "screen" or "_SCREEN" in name:
        return "screen"
    if name.startswith("ROOF_") or mat_name.startswith("roof "):
        return "roof"
    if "POTTING SOIL" in mat_name or "_SOIL" in name:
        return "soil"
    if "LEAF" in name or "STEM" in name or mat_name.startswith("leaf "):
        return "plant"

    wall_tokens = ("BACK_WALL", "GABLE_WALL", "LEFT_FRAME")
    if any(token in name for token in wall_tokens) or name == "ROOFTOP_BACK":
        return "wall"
    if "STAIR_" in name or "STAIR_DIVIDER" in name:
        return "painted"

    soft_tokens = (
        "SOFA",
        "CUSHION",
        "BEANBAG",
        "ARMCHAIR",
        "RUG",
        "COAT_BODY",
        "COAT_SLEEVE",
        "COAT_SHOULDER",
    )
    if any(token in name for token in soft_tokens):
        return "fabric"

    paper_tokens = (
        "BOOK",
        "NOTE",
        "CARD",
        "POSTER",
        "SIGN",
        "ART_",
        "BINDER",
        "NOTEBOOK",
        "TOOLBOARD",
    )
    if any(token in name for token in paper_tokens):
        return "paper"

    ceramic_tokens = ("_POT", "_VASE", "_MUG", "_JAR", "_CUP", "_BOWL")
    if any(token in name for token in ceramic_tokens):
        return "ceramic"

    if mat_name in {"warm oak", "light oak", "dark walnut"}:
        return "wood"
    if mat_name == "black metal" or any(token in name for token in ("RAIL", "CANOPY", "CORD")):
        return "metal"
    if mat_name == "ivory plaster" or any(
        token in name
        for token in ("_FLOOR", "TOP_BEAM", "RIGHT_FRAME", "FOUNDATION", "ROOF_WHITE", "ROOF_TRIM")
    ):
        return "structure"
    if mat_name in {
        "attic blue",
        "chair yellow",
        "door lavender",
        "office mustard",
        "playroom coral",
        "soft pink",
        "studio sage",
        "welcome lavender",
    }:
        return "plastic"
    if mat_name == "paper":
        return "paper"
    return "default"


def refine_material_assignments():
    counts = {}
    for obj in bpy.context.scene.objects:
        if obj.type != "MESH":
            continue
        for slot in obj.material_slots:
            source = original_material(slot.material)
            if not source:
                continue
            category = object_category(obj, source)
            if category is None:
                continue
            slot.material = material_variant(source, category)
            counts[category] = counts.get(category, 0) + 1
    print("FINISH material assignments:", sorted(counts.items()))


def refine_bevels():
    """Keep existing soft-form bevels; standardize only hard-surface edge highlights."""
    soft_tokens = ("SOFA", "CUSHION", "BEANBAG", "ARMCHAIR", "LEAF", "PLANT", "LAMP_GLOBE")
    adjusted = 0
    added = 0
    for obj in bpy.context.scene.objects:
        if obj.type != "MESH" or any(token in obj.name.upper() for token in soft_tokens):
            continue
        bevels = [modifier for modifier in obj.modifiers if modifier.type == "BEVEL"]
        for bevel in bevels:
            # Preserve intentionally broad profiles; only tame small hard-edge bevels.
            if bevel.width <= 0.065:
                bevel.width = max(0.010, min(0.030, bevel.width))
                bevel.segments = max(3, min(4, bevel.segments))
                adjusted += 1
        if not bevels and min(obj.dimensions) > 0.035 and max(obj.dimensions) > 0.18:
            bevel = obj.modifiers.new("subtle edge highlights", "BEVEL")
            bevel.width = 0.012
            bevel.segments = 3
            bevel.limit_method = "ANGLE"
            added += 1
    print(f"FINISH bevels adjusted={adjusted}, added={added}")


def point_at(obj, target):
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def area_light(name, location, target, energy, size, color):
    obj = bpy.data.objects.get(name)
    if obj is None:
        data = bpy.data.lights.new(name=name, type="AREA")
        obj = bpy.data.objects.new(name, data)
        bpy.context.scene.collection.objects.link(obj)
    obj.location = location
    point_at(obj, target)
    obj.data.energy = energy
    obj.data.shape = "DISK"
    obj.data.size = size
    obj.data.color = color
    obj.data.use_shadow = True
    return obj


def refine_lighting_and_rendering():
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"

    # Blender 5.2 Eevee: more stable soft shadows, screen-space ray tracing,
    # and substantially higher GI quality than the original quick preview.
    eevee = scene.eevee
    eevee.taa_render_samples = 160
    eevee.use_shadows = True
    eevee.shadow_ray_count = 4
    eevee.shadow_step_count = 12
    eevee.shadow_resolution_scale = 1.0
    eevee.use_fast_gi = True
    eevee.fast_gi_method = "GLOBAL_ILLUMINATION"
    eevee.fast_gi_quality = 0.72
    eevee.fast_gi_step_count = 24
    eevee.fast_gi_ray_count = 4
    eevee.fast_gi_distance = 12.0
    eevee.fast_gi_bias = 0.04
    eevee.gi_diffuse_bounces = 3
    eevee.direct_light_intensity = 1.0
    eevee.indirect_light_intensity = 0.82
    eevee.use_raytracing = True
    eevee.ray_tracing_method = "SCREEN"
    eevee.ray_tracing_options.use_denoise = True
    eevee.ray_tracing_options.denoise_spatial = True
    eevee.ray_tracing_options.denoise_temporal = True
    eevee.ray_tracing_options.denoise_bilateral = True
    eevee.ray_tracing_options.screen_trace_quality = 0.75
    eevee.ray_tracing_options.trace_max_roughness = 0.65

    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.view_settings.exposure = -0.12
    scene.view_settings.gamma = 1.0

    world = scene.world
    if world and world.use_nodes:
        background = world.node_tree.nodes.get("Background")
        if background:
            background.inputs["Color"].default_value = (0.82, 0.85, 0.90, 1.0)
            background.inputs["Strength"].default_value = 0.22

    lighting = {
        "KEY_SOFT": (760.0, 7.5, (1.0, 0.91, 0.80)),
        "FILL_SOFT": (175.0, 6.5, (0.72, 0.82, 1.0)),
        "TOP_SOFT": (235.0, 5.5, (1.0, 0.78, 0.62)),
    }
    for name, (energy, size, color) in lighting.items():
        obj = bpy.data.objects.get(name)
        if obj and obj.type == "LIGHT":
            obj.data.energy = energy
            obj.data.size = size
            obj.data.color = color
            obj.data.use_shadow = True

    area_light(
        "FINISH_RIM_SOFT",
        (4.5, 4.0, 11.5),
        (0.0, 0.0, 6.3),
        300.0,
        5.0,
        (0.68, 0.78, 1.0),
    )

    # Keep the interactive state deterministic: every room starts dark and the
    # installed hover controller remains the sole owner of these light groups.
    for obj in scene.objects:
        if obj.type == "LIGHT":
            obj.data.use_shadow = True
            if "HOVER" in obj.name:
                obj.data.energy = 0.0
                if obj.data.type == "POINT":
                    # Match the visible fixture rather than suggesting a broad,
                    # invisible room-center light source.
                    obj.data.shadow_soft_size = (
                        0.20 if obj.name.endswith("_HOVER_LIGHT") else 0.10
                    )
                    obj.data.use_soft_falloff = True

    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.filepath = RENDER_PATH
    scene["visual_finish_pass"] = "2026-08-20-material-lighting-v1"


def main():
    if os.path.realpath(bpy.data.filepath) != os.path.realpath(BLEND_PATH):
        raise RuntimeError(f"Wrong source blend: {bpy.data.filepath}")
    refine_material_assignments()
    refine_bevels()
    refine_lighting_and_rendering()
    bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
    bpy.context.scene.render.filepath = RENDER_PATH
    bpy.ops.render.render(write_still=True)
    # Reassert the saved-off state after render and save it once more.
    for obj in bpy.context.scene.objects:
        if obj.type == "LIGHT" and "HOVER" in obj.name:
            obj.data.energy = 0.0
    bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
    print("FINISH complete:", BLEND_PATH)
    print("FINISH render:", RENDER_PATH)


if __name__ == "__main__":
    main()
