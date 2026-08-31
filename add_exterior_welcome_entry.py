"""Add the user-marked WELCOME exterior door and descending staircase."""

import math
import os

import bpy
from mathutils import Vector


BLEND_PATH = "/Users/filippakarlsson/Desktop/filippa_house_reference_rebuilt.blend"
RENDER_PATH = "/Users/filippakarlsson/Desktop/filippa_house_reference_rebuilt.png"
COLLECTION_NAME = "EXTERIOR_WELCOME_ENTRY"
PREFIX = "EXTERIOR_ENTRY_"


def material(*names):
    for name in names:
        found = bpy.data.materials.get(name)
        if found:
            return found
    raise RuntimeError(f"Missing materials: {names}")


def collection():
    found = bpy.data.collections.get(COLLECTION_NAME)
    if found is None:
        found = bpy.data.collections.new(COLLECTION_NAME)
        bpy.context.scene.collection.children.link(found)
    return found


def move_to_collection(obj, target):
    for current in list(obj.users_collection):
        current.objects.unlink(obj)
    target.objects.link(obj)


def box(name, location, dimensions, mat, bevel=0.025):
    bpy.ops.mesh.primitive_cube_add(location=location)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    if bevel > 0:
        modifier = obj.modifiers.new("soft dollhouse edges", "BEVEL")
        modifier.width = bevel
        modifier.segments = 3
    move_to_collection(obj, collection())
    return obj


def sphere(name, location, radius, mat):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = (radius, radius, radius)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    bpy.ops.object.shade_smooth()
    move_to_collection(obj, collection())
    return obj


def cylinder_between(name, start, end, radius, mat):
    start = Vector(start)
    end = Vector(end)
    vector = end - start
    midpoint = (start + end) * 0.5
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=20,
        radius=radius,
        depth=vector.length,
        location=midpoint,
    )
    obj = bpy.context.object
    obj.name = name
    obj.rotation_euler = vector.to_track_quat("Z", "Y").to_euler()
    obj.data.materials.append(mat)
    bpy.ops.object.shade_smooth()
    bevel = obj.modifiers.new("rounded rail ends", "BEVEL")
    bevel.width = min(radius * 0.35, 0.015)
    bevel.segments = 3
    move_to_collection(obj, collection())
    return obj


def clear_previous():
    for obj in list(bpy.data.objects):
        if obj.name.startswith(PREFIX):
            bpy.data.objects.remove(obj, do_unlink=True)


def add_door():
    lavender = material(
        "FINISH__PLASTIC__door lavender",
        "FINISH__PAINTED__welcome lavender",
        "door lavender",
    )
    ivory = material("FINISH__STRUCTURE__ivory plaster", "ivory plaster")
    oak = material("FINISH__WOOD__light oak", "light oak")
    metal = material("FINISH__METAL__black metal", "black metal")

    # The right wall's outer face is x=3.91.  This door occupies the forward
    # portion of that side wall, exactly where the red outline was drawn.
    x = 3.955
    y = -0.88
    bottom = 2.06
    height = 1.34
    width = 0.94
    center_z = bottom + height * 0.5

    box(PREFIX + "DOOR_SHADOW_REVEAL", (3.925, y, center_z), (0.055, 1.10, 1.50), metal, 0.018)
    box(PREFIX + "DOOR_PANEL", (x, y, center_z), (0.085, width, height), lavender, 0.035)

    # Raised inset panels make it read as an actual door from the front/side view.
    for suffix, panel_z, panel_h in (("UPPER", center_z + 0.31, 0.43), ("LOWER", center_z - 0.31, 0.43)):
        box(
            PREFIX + f"DOOR_INSET_{suffix}",
            (x + 0.048, y, panel_z),
            (0.022, width - 0.20, panel_h),
            lavender,
            0.022,
        )

    # Warm white casing and a wooden threshold match the existing house trim.
    box(PREFIX + "DOOR_FRAME_FRONT", (x + 0.010, y - width * 0.5 - 0.055, center_z), (0.12, 0.11, height + 0.18), ivory, 0.025)
    box(PREFIX + "DOOR_FRAME_BACK", (x + 0.010, y + width * 0.5 + 0.055, center_z), (0.12, 0.11, height + 0.18), ivory, 0.025)
    box(PREFIX + "DOOR_FRAME_TOP", (x + 0.010, y, bottom + height + 0.055), (0.12, width + 0.22, 0.11), ivory, 0.025)
    box(PREFIX + "THRESHOLD", (4.04, y, bottom - 0.015), (0.28, width + 0.18, 0.10), oak, 0.025)

    sphere(PREFIX + "DOOR_HANDLE", (x + 0.095, y - 0.31, center_z), 0.055, metal)
    box(PREFIX + "DOOR_HANDLE_PLATE", (x + 0.061, y - 0.31, center_z), (0.025, 0.13, 0.25), metal, 0.018)


def add_staircase():
    lavender = material(
        "FINISH__PAINTED__welcome lavender",
        "FINISH__PLASTIC__welcome lavender",
        "welcome lavender",
    )
    ivory = material("FINISH__STRUCTURE__ivory plaster", "ivory plaster")
    metal = material("FINISH__METAL__black metal", "black metal")

    y = -0.88
    width = 1.06
    landing_top = 2.06
    ground = bpy.data.objects.get("GROUND")
    ground_top = (
        ground.location.z + ground.dimensions.z * 0.5
        if ground is not None
        else -0.49
    )

    # A compact landing outside the door, then thirteen closed steps descending
    # outward (+X), matching the red stair profile without touching the house.
    box(PREFIX + "LANDING", (4.22, y, landing_top - 0.08), (0.58, 1.24, 0.16), lavender, 0.028)
    support_top = landing_top - 0.16
    support_height = support_top - ground_top
    support_z = (support_top + ground_top) * 0.5
    box(PREFIX + "LANDING_SUPPORT_FRONT", (4.22, y - 0.49, support_z), (0.13, 0.13, support_height), ivory, 0.025)
    box(PREFIX + "LANDING_SUPPORT_BACK", (4.22, y + 0.49, support_z), (0.13, 0.13, support_height), ivory, 0.025)

    step_count = 13
    run = 0.18
    first_x = 4.55
    tread_depth = 0.26
    tread_thickness = 0.13
    pad_thickness = 0.14
    pad_top = ground_top + pad_thickness
    # Thirteen equal rises connect the landing exactly to the ground pad.
    rise = (landing_top - pad_top) / step_count
    first_top = landing_top - rise

    tread_tops = []
    tread_centers = []
    for index in range(step_count):
        top = first_top - index * rise
        x = first_x + index * run
        tread_tops.append(top)
        tread_centers.append(x)
        box(
            PREFIX + f"STAIR_TREAD_{index:02d}",
            (x, y, top - tread_thickness * 0.5),
            (tread_depth, width, tread_thickness),
            lavender,
            0.022,
        )
        box(
            PREFIX + f"STAIR_RISER_{index:02d}",
            (x - tread_depth * 0.5 + 0.022, y, top + rise * 0.5),
            (0.055, width, rise),
            ivory,
            0.016,
        )

    # A small grounding pad prevents the last stair from appearing to float.
    last_x = tread_centers[-1]
    last_top = tread_tops[-1]
    box(
        PREFIX + "GROUND_PAD",
        (last_x + 0.16, y, ground_top + pad_thickness * 0.5),
        (0.52, 1.28, pad_thickness),
        ivory,
        0.025,
    )

    # Rail posts follow the stair profile.  Both sides are modeled so the entry
    # remains convincing when the Blender view is orbited.
    post_indices = [0, 3, 6, 9, 12]
    rail_height = 0.63
    for side_index, rail_y in enumerate((y - width * 0.5, y + width * 0.5)):
        side = "FRONT" if side_index == 0 else "BACK"
        rail_points = [(4.13, rail_y, landing_top + rail_height)]
        cylinder_between(
            PREFIX + f"LANDING_POST_{side}",
            (4.13, rail_y, landing_top),
            (4.13, rail_y, landing_top + rail_height),
            0.032,
            metal,
        )
        for index in post_indices:
            x = tread_centers[index]
            top = tread_tops[index]
            cylinder_between(
                PREFIX + f"RAIL_POST_{side}_{index:02d}",
                (x, rail_y, top),
                (x, rail_y, top + rail_height),
                0.032,
                metal,
            )
            rail_points.append((x, rail_y, top + rail_height))
        for index, (start, end) in enumerate(zip(rail_points, rail_points[1:])):
            cylinder_between(
                PREFIX + f"HANDRAIL_{side}_{index:02d}",
                start,
                end,
                0.042,
                metal,
            )


def adjust_camera_to_include_entry():
    camera = bpy.context.scene.camera
    if not camera or camera.data.type != "ORTHO":
        return
    # Store the original once so rerunning this pass cannot drift the camera.
    if "entry_original_location" not in camera:
        camera["entry_original_location"] = list(camera.location)
        camera["entry_original_ortho_scale"] = float(camera.data.ortho_scale)
    original = Vector(camera["entry_original_location"])
    camera.location = original
    camera.data.ortho_scale = 17.2
    local_right = camera.matrix_world.to_quaternion() @ Vector((1.0, 0.0, 0.0))
    camera.location += local_right * 1.10


def main():
    if os.path.realpath(bpy.data.filepath) != os.path.realpath(BLEND_PATH):
        raise RuntimeError(f"Wrong source blend: {bpy.data.filepath}")
    clear_previous()
    add_door()
    add_staircase()
    adjust_camera_to_include_entry()

    # Preserve the deterministic hover default.
    for obj in bpy.context.scene.objects:
        if obj.type == "LIGHT" and "HOVER" in obj.name:
            obj.data.energy = 0.0

    scene = bpy.context.scene
    scene["exterior_welcome_entry_pass"] = "door-stairs-v1"
    scene.render.filepath = RENDER_PATH
    scene.render.resolution_percentage = 100
    scene.eevee.taa_render_samples = 160
    bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
    bpy.ops.render.render(write_still=True)
    bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
    print("Created exterior door and staircase in", BLEND_PATH)


if __name__ == "__main__":
    main()
