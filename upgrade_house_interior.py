"""Professional house-only refinement pass for the existing portfolio house.

This script deliberately preserves the camera, ground, grass/background, room
shells, floor heights, color zoning, and hover-light object names.  It edits
the existing Blender file in place and adds only export-friendly mesh detail.
"""

import math
import os

import bpy
from mathutils import Matrix, Vector


BLEND_PATH = "/Users/filippakarlsson/Desktop/filippa_house_reference_rebuilt.blend"
RENDER_PATH = "/Users/filippakarlsson/Desktop/filippa_house_reference_rebuilt.png"
COLLECTION_NAME = "HOUSE_QUALITY_UPGRADE"
PREFIX = "HOUSE_UPGRADE_"

FLOOR_INDEX = {
    "BASEMENT": 1,
    "WELCOME": 2,
    "PLAYROOM": 3,
    "OFFICE": 4,
    "STUDIO": 5,
    "ROOFTOP": 6,
}


def principled(mat):
    if not mat or not mat.use_nodes:
        return None
    return next((n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)


def set_input(shader, name, value):
    if shader and name in shader.inputs:
        shader.inputs[name].default_value = value


def simple_material(name, color, roughness=0.45, metallic=0.0, coat=0.0):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.diffuse_color = (*color, 1.0)
    shader = principled(mat)
    set_input(shader, "Base Color", (*color, 1.0))
    set_input(shader, "Roughness", roughness)
    set_input(shader, "Metallic", metallic)
    set_input(shader, "Coat Weight", coat)
    set_input(shader, "Coat Roughness", 0.25)
    return mat


def object_floor(name):
    upper = name.upper()
    for floor in FLOOR_INDEX:
        if upper.startswith(floor + "_") or (floor == "ROOFTOP" and upper.startswith("BALCONY_")):
            return floor
    if upper.startswith("EXTERIOR_ENTRY_"):
        return "WELCOME"
    return None


def tag(obj, floor=None, role="detail"):
    if floor:
        obj["portfolio_floor"] = floor
        obj["portfolio_floor_index"] = FLOOR_INDEX[floor]
    obj["web_export_role"] = role
    obj["house_quality_upgrade"] = True
    return obj


def assign(obj, mat):
    if not obj.data or not hasattr(obj.data, "materials"):
        return
    obj.data.materials.clear()
    obj.data.materials.append(mat)


def place_existing(name, loc, dims=None, hide=False):
    """Set an authored object's transform absolutely, so reruns never drift."""
    obj = bpy.data.objects.get(name)
    if not obj:
        return None
    obj.location = loc
    if dims is not None:
        obj.dimensions = dims
    obj.hide_render = hide
    obj.hide_viewport = hide
    return obj


def bevel(obj, width=0.025, segments=3):
    if obj.type != "MESH" or min(obj.dimensions) <= 0.001:
        return
    mod = obj.modifiers.new("Soft miniature edges", "BEVEL")
    mod.width = min(width, min(obj.dimensions) * 0.22)
    mod.segments = segments


def box(name, loc, dims, mat, floor=None, bevel_width=0.025, role="detail", rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(location=loc, rotation=rot)
    obj = bpy.context.object
    obj.name = PREFIX + name
    obj.dimensions = dims
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    assign(obj, mat)
    bevel(obj, bevel_width)
    tag(obj, floor, role)
    move_to_upgrade_collection(obj)
    return obj


def cylinder(name, loc, radius, depth, mat, floor=None, vertices=24, role="detail", rot=(0, 0, 0), bevel_width=0.012):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=loc, rotation=rot)
    obj = bpy.context.object
    obj.name = PREFIX + name
    assign(obj, mat)
    bevel(obj, bevel_width, 2)
    tag(obj, floor, role)
    move_to_upgrade_collection(obj)
    return obj


def cone(name, loc, radius, depth, mat, floor=None, vertices=24, role="detail", rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cone_add(vertices=vertices, radius1=radius, radius2=0.0, depth=depth, location=loc, rotation=rot)
    obj = bpy.context.object
    obj.name = PREFIX + name
    assign(obj, mat)
    bevel(obj, 0.008, 2)
    tag(obj, floor, role)
    move_to_upgrade_collection(obj)
    return obj


def sphere(name, loc, scale, mat, floor=None, role="detail"):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, location=loc)
    obj = bpy.context.object
    obj.name = PREFIX + name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    assign(obj, mat)
    tag(obj, floor, role)
    move_to_upgrade_collection(obj)
    return obj


def torus(name, loc, major_radius, minor_radius, mat, floor=None, role="detail", rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_torus_add(
        major_radius=major_radius,
        minor_radius=minor_radius,
        major_segments=24,
        minor_segments=8,
        location=loc,
        rotation=rot,
    )
    obj = bpy.context.object
    obj.name = PREFIX + name
    assign(obj, mat)
    tag(obj, floor, role)
    move_to_upgrade_collection(obj)
    return obj


def cylinder_between(name, a, b, radius, mat, floor=None, role="detail"):
    a, b = Vector(a), Vector(b)
    delta = b - a
    obj = cylinder(name, (a + b) / 2, radius, delta.length, mat, floor, role=role)
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = delta.to_track_quat("Z", "Y")
    return obj


def move_to_upgrade_collection(obj):
    for col in list(obj.users_collection):
        col.objects.unlink(obj)
    upgrade.objects.link(obj)


def add_book(name, x, y, z, w, h, mat, floor, depth=0.25, lean=0.0):
    return box(name, (x, y, z), (w, depth, h), mat, floor, 0.008, "book", rot=(0, lean, 0))


def capture_protected_state():
    camera = bpy.data.objects.get("REFERENCE_FRONT_CAMERA")
    ground = bpy.data.objects.get("GROUND")
    bg = bpy.data.collections.get("BACKGROUND_LANDSCAPE")
    return {
        "camera": (tuple(camera.matrix_world), camera.data.type, camera.data.ortho_scale) if camera else None,
        "ground": (tuple(ground.matrix_world), tuple(m.name for m in ground.data.materials)) if ground else None,
        "background": tuple(
            sorted((o.name, tuple(o.matrix_world), o.hide_render) for o in bg.all_objects)
        ) if bg else None,
    }


def assert_protected_state(before):
    after = capture_protected_state()
    if before != after:
        raise RuntimeError("Protected camera/background/ground state changed; refusing to save.")


def clear_previous_upgrade():
    old = bpy.data.collections.get(COLLECTION_NAME)
    if old:
        for obj in list(old.objects):
            # Preserve exact world transforms when removing a previous lamp
            # control Empty.  The hover add-on works in world space.
            for child in list(obj.children):
                world = child.matrix_world.copy()
                child.parent = None
                child.matrix_world = world
            bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.collections.remove(old)
    for floor in ("PLAYROOM", "OFFICE", "STUDIO"):
        for obj in bpy.data.objects:
            if obj.name.startswith(floor + "_BOOKCASE_"):
                obj.hide_render = False
                obj.hide_viewport = False
                obj.pop("replaced_by", None)


protected_before = capture_protected_state()
clear_previous_upgrade()
upgrade = bpy.data.collections.new(COLLECTION_NAME)
bpy.context.scene.collection.children.link(upgrade)


# Restrained, glTF-friendly material set.  The colors strengthen the existing
# palette without flattening all furniture into the same finish.
MAT_WALNUT = simple_material("UPGRADE wood - deep walnut", (0.22, 0.095, 0.055), 0.34, coat=0.10)
MAT_OAK = simple_material("UPGRADE wood - warm oak", (0.56, 0.29, 0.12), 0.38, coat=0.08)
MAT_LIGHT_OAK = simple_material("UPGRADE wood - pale oak", (0.76, 0.51, 0.27), 0.41, coat=0.07)
MAT_BRONZE = simple_material("UPGRADE metal - dark bronze", (0.105, 0.064, 0.043), 0.25, 0.72)
MAT_BRASS = simple_material("UPGRADE metal - aged brass", (0.54, 0.30, 0.08), 0.26, 0.65)
MAT_CREAM = simple_material("UPGRADE painted - warm cream", (0.82, 0.75, 0.64), 0.46, coat=0.12)
MAT_PINK = simple_material("UPGRADE painted - coral pink", (0.82, 0.34, 0.34), 0.43, coat=0.10)
MAT_MUSTARD = simple_material("UPGRADE painted - mustard", (0.75, 0.45, 0.08), 0.42, coat=0.10)
MAT_SAGE = simple_material("UPGRADE painted - sage", (0.39, 0.50, 0.32), 0.45, coat=0.10)
MAT_LAVENDER = simple_material("UPGRADE painted - lavender", (0.55, 0.43, 0.67), 0.43, coat=0.11)
MAT_BLUE = simple_material("UPGRADE painted - attic blue", (0.32, 0.44, 0.56), 0.40, coat=0.12)
MAT_PAPER = simple_material("UPGRADE paper - warm white", (0.91, 0.85, 0.74), 0.78)
MAT_INK = simple_material("UPGRADE ink - charcoal", (0.055, 0.050, 0.048), 0.56)
MAT_GREEN = simple_material("UPGRADE accent - leaf green", (0.20, 0.38, 0.18), 0.55)
MAT_SCREEN = simple_material("UPGRADE screen - charcoal glass", (0.025, 0.032, 0.035), 0.15, coat=0.20)
BOOK_MATS = [MAT_PAPER, MAT_PINK, MAT_SAGE, MAT_LAVENDER, MAT_MUSTARD, MAT_BLUE]


def restyle_existing_plant(prefix, original_base, target_base, factor, floor):
    """Apply one permanent world-space layout transform to plant geometry.

    Transforming mesh/curve data avoids hundreds of object-parent dependency
    updates.  A data-block version marker makes the operation idempotent.
    """
    version = "plant-layout-2026-08-24-v1"
    source = Vector(original_base)
    target = Vector(target_base)
    world_transform = Matrix.Translation(target) @ Matrix.Scale(factor, 4) @ Matrix.Translation(-source)
    changed = 0
    for obj in [o for o in bpy.data.objects if o.name.startswith(prefix)]:
        if obj.type not in {"MESH", "CURVE"} or not obj.data:
            continue
        if obj.data.get("plant_layout_version") == version:
            continue
        local_transform = obj.matrix_world.inverted() @ world_transform @ obj.matrix_world
        obj.data.transform(local_transform)
        obj.data["plant_layout_version"] = version
        obj.data["plant_display_scale"] = factor
        obj["portfolio_floor"] = floor
        changed += 1
    print(f"PLANT_LAYOUT {prefix} changed={changed} scale={factor}")


# Plants should have different jobs and scales—not a repeated line of tiny
# floor pots.  Large plants stay floor-standing, while selected smaller plants
# sit convincingly on the workbench, console, corner cabinet, shelves, and
# studio flat-file.
restyle_existing_plant("BASEMENT_PLANT_", (2.65, 0.15, 0.18), (2.62, 0.12, 0.28), 1.45, "BASEMENT")
restyle_existing_plant("BASEMENT_BENCH_PLANT_", (-0.58, -0.02, 0.92), (-0.58, -0.02, 0.915), 1.25, "BASEMENT")
restyle_existing_plant("WELCOME_PLANT_", (-2.39, 0.05, 1.96), (-2.50, 0.10, 2.06), 1.55, "WELCOME")
restyle_existing_plant("WELCOME_CONSOLE_PLANT_", (1.34, -0.01, 2.74), (1.34, -0.01, 2.63), 1.35, "WELCOME")
restyle_existing_plant("PLAYROOM_PLANT_", (-3.10, 0.15, 3.74), (-3.05, 0.12, 3.84), 1.55, "PLAYROOM")
restyle_existing_plant("OFFICE_PLANT_", (-0.30, 0.12, 5.52), (-0.34, 0.12, 5.62), 1.35, "OFFICE")
restyle_existing_plant("OFFICE_CORNER_PLANT_", (-3.08, 0.07, 6.12), (-3.08, 0.07, 6.12), 1.25, "OFFICE")
restyle_existing_plant("STUDIO_PLANT_", (-2.75, 0.10, 7.30), (-2.72, 0.12, 7.40), 1.50, "STUDIO")
# This one moves off the floor and onto the studio flat-file top.
restyle_existing_plant("STUDIO_TALL_PLANT_", (0.95, 0.15, 7.30), (2.18, 0.08, 8.16), 0.92, "STUDIO")
restyle_existing_plant("STUDIO_SHELF_FERN_", (-2.98, 1.145, 8.24), (-2.98, 1.145, 8.24), 1.30, "STUDIO")
restyle_existing_plant("STUDIO_SHELF_SNAKE_", (-2.58, 1.145, 8.62), (-2.58, 1.145, 8.62), 1.12, "STUDIO")
restyle_existing_plant("ROOFTOP_PLANT_", (2.90, 0.05, 9.08), (2.90, 0.05, 9.19), 1.30, "ROOFTOP")


# Give every existing house object useful floor/export metadata.
for obj in bpy.data.objects:
    floor = object_floor(obj.name)
    if floor:
        obj["portfolio_floor"] = floor
        obj["portfolio_floor_index"] = FLOOR_INDEX[floor]
        obj["web_export_role"] = obj.get("web_export_role", "existing_house")


# Replace the three conspicuously repeated tall bookcases.  Welcome and
# rooftop retain their tall bookcases to preserve the reference rhythm.
for floor in ("PLAYROOM", "OFFICE", "STUDIO"):
    for obj in bpy.data.objects:
        if obj.name.startswith(floor + "_BOOKCASE_"):
            obj.hide_render = True
            obj.hide_viewport = True
            obj["replaced_by"] = COLLECTION_NAME


def playroom_cubby():
    # Compact two-bay unit: it deliberately clears the arcade cabinet on the
    # left and the stair divider on the right.
    f, x, y, z0, w, h, d = "PLAYROOM", 2.14, 0.12, 3.84, 0.94, 0.62, 0.40
    box("PLAYROOM_CUBBY_BACK", (x, y + 0.16, z0 + h / 2), (w, 0.06, h), MAT_WALNUT, f, 0.015, "storage")
    for sx in (-w / 2, w / 2):
        box("PLAYROOM_CUBBY_SIDE", (x + sx, y, z0 + h / 2), (0.075, d, h), MAT_WALNUT, f, 0.018, "storage")
    for zz in (z0, z0 + h / 2, z0 + h):
        box("PLAYROOM_CUBBY_SHELF", (x, y, zz), (w, d, 0.075), MAT_WALNUT, f, 0.018, "storage")
    box("PLAYROOM_CUBBY_DIVIDER", (x, y, z0 + h * 0.26), (0.055, d, h * 0.46), MAT_WALNUT, f, 0.012, "storage")
    for i, xx in enumerate((x - 0.23, x + 0.23)):
        mat = (MAT_MUSTARD, MAT_SAGE)[i]
        box("PLAYROOM_TOY_BIN", (xx, y - 0.225, z0 + 0.145), (0.36, 0.055, 0.20), mat, f, 0.025, "storage")
        cylinder("PLAYROOM_BIN_PULL", (xx, y - 0.26, z0 + 0.145), 0.026, 0.05, MAT_BRASS, f, 16, "handle", rot=(math.pi / 2, 0, 0))
    for i in range(5):
        add_book("PLAYROOM_CUBBY_BOOK", x - 0.35 + i * 0.12, y - 0.19, z0 + 0.43, 0.07, 0.22 + (i % 3) * 0.03, BOOK_MATS[i % len(BOOK_MATS)], f)
    sphere("PLAYROOM_WOOD_TOY", (x + 0.34, y - 0.20, z0 + 0.46), (0.075, 0.055, 0.075), MAT_MUSTARD, f, "toy")


def office_cabinet():
    # Narrower and shifted right so it no longer touches the low side cabinet
    # or sits in front of the typographic poster.
    f, x, y, z0, w, h, d = "OFFICE", 2.06, 0.13, 5.62, 1.02, 0.98, 0.40
    box("OFFICE_CABINET_BODY", (x, y + 0.13, z0 + h / 2), (w, 0.12, h), MAT_WALNUT, f, 0.02, "storage")
    for sx in (-w / 2, w / 2):
        box("OFFICE_CABINET_SIDE", (x + sx, y, z0 + h / 2), (0.07, d, h), MAT_WALNUT, f, 0.017, "storage")
    for zz in (z0, z0 + 0.49, z0 + h):
        box("OFFICE_CABINET_SHELF", (x, y, zz), (w, d, 0.075), MAT_WALNUT, f, 0.017, "storage")
    for i, xx in enumerate((x - 0.25, x + 0.25)):
        box("OFFICE_CABINET_DOOR", (xx, y - 0.225, z0 + 0.245), (0.43, 0.055, 0.39), MAT_MUSTARD if i == 0 else MAT_CREAM, f, 0.025, "storage")
        cylinder("OFFICE_CABINET_HANDLE", (xx + (-0.10 if i == 0 else 0.10), y - 0.27, z0 + 0.25), 0.022, 0.05, MAT_BRONZE, f, 16, "handle", rot=(math.pi / 2, 0, 0))
    for i in range(7):
        add_book("OFFICE_REFERENCE_BOOK", x - 0.39 + i * 0.115, y - 0.19, z0 + 0.67, 0.065, 0.27 + (i % 3) * 0.03, BOOK_MATS[(i + 2) % len(BOOK_MATS)], f)


def studio_flat_file():
    # The flat-file remains wider than the office cabinet, but now has clear
    # breathing room between the visitor chair, poster, and stairs.
    f, x, y, z0, w, h, d = "STUDIO", 1.95, 0.13, 7.40, 1.28, 0.72, 0.43
    box("STUDIO_FLATFILE_BODY", (x, y + 0.10, z0 + h / 2), (w, 0.22, h), MAT_SAGE, f, 0.025, "storage")
    box("STUDIO_FLATFILE_TOP", (x, y, z0 + h), (w + 0.08, d, 0.08), MAT_LIGHT_OAK, f, 0.022, "storage")
    for row in range(3):
        for col in range(2):
            xx = x + (-0.30 if col == 0 else 0.30)
            zz = z0 + 0.15 + row * 0.19
            box("STUDIO_FLATFILE_DRAWER", (xx, y - 0.145, zz), (0.53, 0.055, 0.145), MAT_CREAM if (row + col) % 2 else MAT_SAGE, f, 0.018, "storage")
            box("STUDIO_FLATFILE_LABEL", (xx, y - 0.183, zz), (0.15, 0.025, 0.050), MAT_BRASS, f, 0.008, "handle")


playroom_cubby()
office_cabinet()
studio_flat_file()


# Furniture craftsmanship and desk accessories, unique to each floor.
# Basement: practical maker bench.
box("BASEMENT_WORKBENCH_APRON", (-1.50, -0.30, 0.79), (1.86, 0.09, 0.22), MAT_WALNUT, "BASEMENT", 0.018, "furniture")
box("BASEMENT_CUTTING_MAT", (-1.62, -0.355, 0.93), (0.78, 0.32, 0.018), MAT_SAGE, "BASEMENT", 0.006, "tool")
cylinder("BASEMENT_PROTOTYPE_BASE", (-0.65, -0.35, 0.96), 0.13, 0.06, MAT_LIGHT_OAK, "BASEMENT", 20, "prototype")
sphere("BASEMENT_PROTOTYPE_FORM", (-0.65, -0.35, 1.08), (0.10, 0.10, 0.13), MAT_MUSTARD, "BASEMENT", "prototype")
box("BASEMENT_TOOL_TRAY", (-2.35, -0.36, 0.96), (0.34, 0.24, 0.06), MAT_BRONZE, "BASEMENT", 0.014, "tool")

# Welcome: softer, genuinely upholstered sofa details.
box("WELCOME_SOFA_FRONT_PIPING", (-0.80, -0.505, 2.35), (1.46, 0.035, 0.035), MAT_LAVENDER, "WELCOME", 0.017, "upholstery")
box("WELCOME_SOFA_CENTER_SEAM", (-0.80, -0.507, 2.48), (0.025, 0.03, 0.28), MAT_LAVENDER, "WELCOME", 0.010, "upholstery")
sphere("WELCOME_THROW_PILLOW", (-1.28, -0.49, 2.58), (0.25, 0.08, 0.21), MAT_PINK, "WELCOME", "upholstery")
box("WELCOME_CONSOLE_HANDLE_L", (0.72, 0.075, 2.39), (0.17, 0.035, 0.025), MAT_BRASS, "WELCOME", 0.010, "handle")
box("WELCOME_CONSOLE_HANDLE_R", (1.18, 0.075, 2.39), (0.17, 0.035, 0.025), MAT_BRASS, "WELCOME", 0.010, "handle")

# Playroom: grounded coffee table.  The beanbag stays clean and soft; a hard
# torus seam made its silhouette look fused rather than upholstered.
box("PLAYROOM_TABLE_LOWER_SHELF", (-0.40, -0.39, 3.91), (1.03, 0.44, 0.055), MAT_LIGHT_OAK, "PLAYROOM", 0.018, "furniture")
for xx in (-0.88, 0.08):
    cylinder("PLAYROOM_TABLE_LEG", (xx, -0.44, 3.91), 0.045, 0.30, MAT_OAK, "PLAYROOM", 20, "furniture")

# Replace the twelve identical oval "eggs" with a deliberately varied toy and
# book display.  The original shelves stay exactly where they are.
for row in range(3):
    for col in range(4):
        old_toy = bpy.data.objects.get(f"PLAYROOM_TOY_{row}_{col}")
        if old_toy:
            old_toy.hide_render = True
            old_toy.hide_viewport = True
            old_toy["replaced_by"] = "curated playroom shelf display"

# Lower shelf: books, a tiny car, and two construction blocks.
for i, (x, w, h, mat) in enumerate((
    (-1.57, 0.055, 0.22, MAT_BLUE),
    (-1.49, 0.065, 0.26, MAT_PAPER),
    (-1.40, 0.055, 0.19, MAT_PINK),
)):
    add_book(f"PLAYROOM_SHELF_BOOK_LOWER_{i}", x, 1.185, 4.36 + 0.035 + h / 2, w, h, mat, "PLAYROOM", depth=0.15)
box("PLAYROOM_TOY_CAR_BODY", (-1.10, 1.18, 4.465), (0.31, 0.15, 0.10), MAT_MUSTARD, "PLAYROOM", 0.025, "toy")
box("PLAYROOM_TOY_CAR_CAB", (-1.04, 1.18, 4.545), (0.13, 0.14, 0.09), MAT_PINK, "PLAYROOM", 0.025, "toy")
for x in (-1.20, -0.99):
    cylinder("PLAYROOM_TOY_CAR_WHEEL", (x, 1.092, 4.43), 0.045, 0.035, MAT_BRONZE, "PLAYROOM", 16, "toy", rot=(math.pi / 2, 0, 0), bevel_width=0.006)
box("PLAYROOM_BLOCK_LARGE", (-0.78, 1.18, 4.46), (0.16, 0.15, 0.13), MAT_SAGE, "PLAYROOM", 0.018, "toy")
box("PLAYROOM_BLOCK_SMALL", (-0.67, 1.18, 4.44), (0.10, 0.15, 0.09), MAT_LAVENDER, "PLAYROOM", 0.016, "toy")

# Middle shelf: a neat book stack and a small friendly robot.
for i, (z, w, mat) in enumerate(((4.755, 0.32, MAT_PINK), (4.795, 0.27, MAT_PAPER), (4.835, 0.23, MAT_BLUE))):
    box(f"PLAYROOM_SHELF_BOOK_STACK_{i}", (-1.48, 1.18, z), (w, 0.15, 0.035), mat, "PLAYROOM", 0.007, "book")
box("PLAYROOM_ROBOT_BODY", (-1.08, 1.18, 4.81), (0.19, 0.14, 0.18), MAT_SAGE, "PLAYROOM", 0.028, "toy")
box("PLAYROOM_ROBOT_HEAD", (-1.08, 1.18, 4.945), (0.23, 0.14, 0.13), MAT_CREAM, "PLAYROOM", 0.035, "toy")
for x in (-1.135, -1.025):
    sphere("PLAYROOM_ROBOT_EYE", (x, 1.097, 4.96), (0.022, 0.012, 0.022), MAT_INK, "PLAYROOM", "toy")
for x in (-1.22, -0.94):
    box("PLAYROOM_ROBOT_ARM", (x, 1.18, 4.82), (0.07, 0.11, 0.045), MAT_MUSTARD, "PLAYROOM", 0.018, "toy")
for i, (x, mat) in enumerate(((-0.82, MAT_MUSTARD), (-0.70, MAT_BLUE))):
    box(f"PLAYROOM_MIDDLE_BLOCK_{i}", (x, 1.18, 4.79 + i * 0.025), (0.10, 0.15, 0.14 + i * 0.05), mat, "PLAYROOM", 0.018, "toy")

# Upper shelf: a little rocket and a concise row of design/activity books.
cylinder("PLAYROOM_ROCKET_BODY", (-1.50, 1.18, 5.16), 0.065, 0.19, MAT_BLUE, "PLAYROOM", 20, "toy")
cone("PLAYROOM_ROCKET_NOSE", (-1.50, 1.18, 5.315), 0.068, 0.12, MAT_PINK, "PLAYROOM", 20, "toy")
for side in (-1, 1):
    box("PLAYROOM_ROCKET_FIN", (-1.50 + side * 0.075, 1.18, 5.095), (0.07, 0.12, 0.09), MAT_MUSTARD, "PLAYROOM", 0.012, "toy", rot=(0, side * math.radians(22), 0))
for i, (x, h, mat, lean) in enumerate((
    (-1.27, 0.25, MAT_PAPER, -0.06),
    (-1.17, 0.21, MAT_SAGE, 0.03),
    (-1.07, 0.27, MAT_LAVENDER, -0.02),
    (-0.96, 0.23, MAT_MUSTARD, 0.05),
)):
    add_book(f"PLAYROOM_SHELF_BOOK_UPPER_{i}", x, 1.185, 5.04 + 0.035 + h / 2, 0.065, h, mat, "PLAYROOM", depth=0.15, lean=lean)
box("PLAYROOM_PUZZLE_BOX", (-0.74, 1.18, 5.16), (0.18, 0.15, 0.17), MAT_PINK, "PLAYROOM", 0.025, "toy")
box("PLAYROOM_PUZZLE_MARK", (-0.74, 1.094, 5.16), (0.07, 0.018, 0.07), MAT_MUSTARD, "PLAYROOM", 0.014, "toy", rot=(0, 0, math.radians(45)))

# Office: work-focused desk details.
box("OFFICE_DESK_DRAWER", (-1.62, -0.25, 6.08), (0.63, 0.38, 0.18), MAT_LIGHT_OAK, "OFFICE", 0.018, "furniture")
box("OFFICE_DESK_DRAWER_PULL", (-1.62, -0.455, 6.08), (0.20, 0.025, 0.025), MAT_BRONZE, "OFFICE", 0.008, "handle")
cylinder("OFFICE_MONITOR_STAND", (-1.62, 0.07, 6.34), 0.055, 0.23, MAT_BRONZE, "OFFICE", 20, "tech")
box("OFFICE_MONITOR_FOOT", (-1.62, -0.06, 6.26), (0.34, 0.22, 0.035), MAT_BRONZE, "OFFICE", 0.012, "tech")
box("OFFICE_MOUSE", (-0.97, -0.34, 6.28), (0.14, 0.20, 0.055), MAT_CREAM, "OFFICE", 0.027, "tech")
box("OFFICE_TABLET", (-2.22, -0.34, 6.28), (0.35, 0.25, 0.025), MAT_SCREEN, "OFFICE", 0.016, "tech")
cylinder("OFFICE_PENCIL_CUP", (-0.82, -0.20, 6.38), 0.07, 0.21, MAT_MUSTARD, "OFFICE", 20, "stationery")
for i in range(4):
    cylinder("OFFICE_PENCIL", (-0.86 + i * 0.025, -0.20, 6.55 + (i % 2) * 0.03), 0.009, 0.25, BOOK_MATS[i], "OFFICE", 12, "stationery")

# Studio: visual-design tools, kept compact and ordered.
box("STUDIO_MOUSE", (-0.55, -0.35, 8.06), (0.14, 0.19, 0.055), MAT_SAGE, "STUDIO", 0.028, "tech")
for i, mat in enumerate((MAT_PINK, MAT_MUSTARD, MAT_BLUE)):
    box("STUDIO_SWATCH_STACK", (-1.96 + i * 0.11, -0.38, 8.075 + i * 0.012), (0.24, 0.11, 0.016), mat, "STUDIO", 0.005, "sample")
box("STUDIO_DRAWER_HANDLE", (-2.12, -0.205, 7.72), (0.22, 0.028, 0.025), MAT_BRASS, "STUDIO", 0.008, "handle")

# Rooftop/balcony: clean lounge + compact design desk.  The original oversized
# office chair and tall bookcase are hidden because they blocked the desk,
# poster and purple door from the intended front view.
place_existing("ROOFTOP_ARMCHAIR", (-2.67, -0.10, 9.50), (0.78, 0.72, 0.30))
place_existing("ROOFTOP_ARMCHAIR_BACK", (-2.67, 0.13, 9.86), (0.78, 0.22, 0.70))
place_existing("ROOFTOP_ARM", (-3.09, -0.08, 9.73), (0.18, 0.65, 0.50))
place_existing("ROOFTOP_ARM.001", (-2.25, -0.08, 9.73), (0.18, 0.65, 0.50))
box("ROOFTOP_CHAIR_CUSHION", (-2.67, -0.50, 9.61), (0.64, 0.34, 0.13), MAT_BLUE, "ROOFTOP", 0.06, "upholstery")
box("ROOFTOP_CHAIR_PIPING", (-2.67, -0.685, 9.61), (0.56, 0.025, 0.025), MAT_CREAM, "ROOFTOP", 0.012, "upholstery")

place_existing("ROOFTOP_DESK_TOP", (-0.95, 0.05, 9.76), (1.32, 0.55, 0.09))
place_existing("ROOFTOP_DESK_LEG_-0.65", (-1.48, 0.10, 9.41), (0.08, 0.38, 0.58))
place_existing("ROOFTOP_DESK_LEG_0.65", (-0.42, 0.10, 9.41), (0.08, 0.38, 0.58))
place_existing("ROOFTOP_DESK_MONITOR", (-0.95, 0.17, 10.12), (0.62, 0.08, 0.42))
place_existing("ROOFTOP_DESK_SCREEN", (-0.95, 0.105, 10.12), (0.52, 0.018, 0.31))
place_existing("ROOFTOP_DESK_STAND", (-0.95, 0.16, 9.88), (0.07, 0.09, 0.17))
place_existing("ROOFTOP_DESK_KEYBOARD", (-0.93, -0.18, 9.83), (0.42, 0.18, 0.03))
for part, loc in {
    "ROOFTOP_DESK_LAMP_BASE": (-1.45, -0.18, 9.83),
    "ROOFTOP_DESK_LAMP_STEM": (-1.45, -0.18, 9.96),
    "ROOFTOP_DESK_LAMP_BULB_SOCKET": (-1.45, -0.25, 9.972),
    "ROOFTOP_DESK_LAMP_BULB": (-1.45, -0.25, 10.03),
    "ROOFTOP_DESK_LAMP_SHADE": (-1.45, -0.18, 10.10),
}.items():
    place_existing(part, loc)
for part in ("ROOFTOP_DESK_CHAIR_BACK", "ROOFTOP_DESK_CHAIR_POST", "ROOFTOP_DESK_CHAIR_SEAT"):
    place_existing(part, bpy.data.objects[part].location, hide=True)

# A small tucked stool reads as usable seating without hiding the desk.
cylinder("ROOFTOP_STOOL_SEAT", (-0.95, -0.38, 9.47), 0.22, 0.11, MAT_BLUE, "ROOFTOP", 24, "furniture")
for x in (-1.09, -0.81):
    cylinder("ROOFTOP_STOOL_LEG", (x, -0.38, 9.30), 0.025, 0.29, MAT_BRONZE, "ROOFTOP", 16, "furniture")
box("ROOFTOP_MOUSE", (-0.48, -0.25, 9.82), (0.12, 0.17, 0.045), MAT_LAVENDER, "ROOFTOP", 0.023, "tech")
cylinder("ROOFTOP_SIDE_TABLE_TOP", (-1.94, -0.42, 9.52), 0.20, 0.06, MAT_LIGHT_OAK, "ROOFTOP", 28, "furniture")
cylinder("ROOFTOP_SIDE_TABLE_STEM", (-1.94, -0.42, 9.30), 0.032, 0.42, MAT_BRONZE, "ROOFTOP", 18, "furniture")
cylinder("ROOFTOP_SIDE_TABLE_FOOT", (-1.94, -0.42, 9.10), 0.13, 0.035, MAT_BRONZE, "ROOFTOP", 24, "furniture")

# Replace the tall bookcase with a compact open shelf that leaves both the
# statement poster and lavender door unobstructed.
for obj in bpy.data.objects:
    if obj.name.startswith("ROOFTOP_BOOKCASE_"):
        obj.hide_render = True
        obj.hide_viewport = True
        obj["replaced_by"] = "compact rooftop open shelf"
rx, ry, rz, rw, rh, rd = 1.27, 0.12, 9.18, 0.82, 0.86, 0.36
box("ROOFTOP_OPEN_SHELF_BACK", (rx, ry + 0.14, rz + rh / 2), (rw, 0.055, rh), MAT_WALNUT, "ROOFTOP", 0.015, "storage")
for sx in (-rw / 2, rw / 2):
    box("ROOFTOP_OPEN_SHELF_SIDE", (rx + sx, ry, rz + rh / 2), (0.065, rd, rh), MAT_WALNUT, "ROOFTOP", 0.016, "storage")
for z in (rz, rz + rh / 2, rz + rh):
    box("ROOFTOP_OPEN_SHELF_BOARD", (rx, ry, z), (rw, rd, 0.065), MAT_WALNUT, "ROOFTOP", 0.016, "storage")
for i, (x, h, mat) in enumerate((
    (1.00, 0.27, MAT_PAPER), (1.10, 0.31, MAT_PINK), (1.21, 0.24, MAT_SAGE),
    (1.34, 0.29, MAT_LAVENDER), (1.46, 0.25, MAT_BLUE),
)):
    add_book(f"ROOFTOP_OPEN_SHELF_BOOK_{i}", x, -0.08, rz + 0.43 + 0.045 + h / 2, 0.065, h, mat, "ROOFTOP", depth=0.20)
box("ROOFTOP_OPEN_SHELF_BOX", (1.05, -0.09, 9.35), (0.26, 0.20, 0.20), MAT_LAVENDER, "ROOFTOP", 0.025, "storage")
cylinder("ROOFTOP_OPEN_SHELF_VASE", (1.48, -0.08, 9.35), 0.075, 0.26, MAT_CREAM, "ROOFTOP", 20, "decor")


# Refine the intentionally retained welcome-floor tall bookcase.
for floor, x, y, z0, w, h in (
    ("WELCOME", 2.05, 0.10, 1.96, 0.86, 1.42),
):
    box(f"{floor}_BOOKCASE_BACK", (x, y + 0.16, z0 + h / 2), (w, 0.055, h), MAT_WALNUT, floor, 0.012, "storage")
    box(f"{floor}_BOOKCASE_PLINTH", (x, y - 0.02, z0 + 0.02), (w + 0.10, 0.38, 0.09), MAT_WALNUT, floor, 0.018, "storage")
    box(f"{floor}_BOOKCASE_CROWN", (x, y - 0.02, z0 + h), (w + 0.10, 0.38, 0.09), MAT_WALNUT, floor, 0.018, "storage")
    for side in (-1, 1):
        box(f"{floor}_BOOKEND", (x + side * (w * 0.36), y - 0.18, z0 + h * 0.42), (0.035, 0.23, 0.19), MAT_BRASS, floor, 0.008, "bookend")

# Correct the retained bookcase structure's paper-like material misclassification.
for obj in bpy.data.objects:
    if obj.name.startswith(("WELCOME_BOOKCASE_", "ROOFTOP_BOOKCASE_")) and not any(t in obj.name for t in ("BOOK_", "BOOKEND")):
        assign(obj, MAT_WALNUT)


# Layered poster backing and small graphic studies preserve every existing
# phrase while making the walls feel intentionally art-directed.
POSTERS = {
    "BASEMENT": ((0.38, 1.43, 1.33), (1.18, 0.035, 1.08), MAT_WALNUT, MAT_MUSTARD),
    "WELCOME": ((-0.80, 1.43, 3.21), (0.82, 0.035, 0.88), MAT_LIGHT_OAK, MAT_LAVENDER),
    "PLAYROOM": ((0.28, 1.43, 4.92), (0.98, 0.035, 0.98), MAT_LIGHT_OAK, MAT_PINK),
    "OFFICE": ((0.65, 1.43, 6.65), (1.04, 0.035, 1.04), MAT_LIGHT_OAK, MAT_MUSTARD),
    "STUDIO": ((0.62, 1.43, 8.24), (1.04, 0.035, 0.98), MAT_LIGHT_OAK, MAT_SAGE),
    "ROOFTOP": ((0.30, 1.43, 10.26), (1.06, 0.035, 1.10), MAT_LIGHT_OAK, MAT_LAVENDER),
}
for floor, (loc, dims, frame_mat, accent) in POSTERS.items():
    box(f"{floor}_POSTER_SHADOW_MAT", loc, dims, frame_mat, floor, 0.012, "poster")
    # a narrow offset color tab gives each sign a distinct editorial identity
    box(f"{floor}_POSTER_COLOR_TAB", (loc[0] - dims[0] * 0.43, 1.392, loc[2] + dims[2] * 0.32), (0.07, 0.025, 0.20), accent, floor, 0.008, "poster")

# Stairs receive consistent nosings; external rails and balcony use one dark
# bronze system so the circulation reads as architecture, not loose blocks.
for obj in list(bpy.data.objects):
    if obj.name.startswith(tuple(f + "_STAIR_" for f in ("BASEMENT", "WELCOME", "PLAYROOM", "OFFICE", "STUDIO"))) and "RISER" not in obj.name and obj.type == "MESH":
        floor = object_floor(obj.name)
        box(
            obj.name + "_NOSING",
            (obj.location.x, obj.location.y - obj.dimensions.y / 2 - 0.012, obj.location.z + obj.dimensions.z / 2 + 0.012),
            (obj.dimensions.x, 0.055, 0.035),
            MAT_LIGHT_OAK,
            floor,
            0.012,
            "stair_nosing",
        )

for obj in bpy.data.objects:
    upper = obj.name.upper()
    if upper.startswith("BALCONY_") or (upper.startswith("EXTERIOR_ENTRY_") and any(t in upper for t in ("RAIL", "POST", "HANDRAIL"))):
        assign(obj, MAT_BRONZE)
        bevel(obj, 0.012, 2)

for obj in list(bpy.data.objects):
    if obj.name.startswith("EXTERIOR_ENTRY_STAIR_TREAD_"):
        box(
            obj.name + "_NOSING",
            (obj.location.x + obj.dimensions.x / 2 + 0.008, obj.location.y, obj.location.z + obj.dimensions.z / 2 + 0.012),
            (0.045, obj.dimensions.y, 0.035),
            MAT_LIGHT_OAK,
            "WELCOME",
            0.010,
            "stair_nosing",
        )

# Slim external stringers visually connect the landing to the ground.
cylinder_between("EXTERIOR_STRINGER_FRONT", (4.48, -1.39, 1.70), (6.74, -1.39, -0.55), 0.045, MAT_BRONZE, "WELCOME", "stair_structure")
cylinder_between("EXTERIOR_STRINGER_BACK", (4.48, -0.37, 1.70), (6.74, -0.37, -0.55), 0.045, MAT_BRONZE, "WELCOME", "stair_structure")


# Hanging lamps remain separate controls with their original names.  Added
# collars make the visible source feel attached to the actual fixture.  The
# control Empty carries metadata only: existing lights are intentionally not
# parented because the working hover add-on positions them in world space.
for floor, idx in FLOOR_INDEX.items():
    empty = bpy.data.objects.new(f"Room_{idx:02d}_Lamp", None)
    empty.empty_display_type = "CIRCLE"
    empty.empty_display_size = 0.18
    empty["web_control_id"] = f"Room_{idx:02d}_Lamp"
    empty["portfolio_floor"] = floor
    empty["web_export_role"] = "lamp_control"
    upgrade.objects.link(empty)
    globe = bpy.data.objects.get(f"{floor}_CEILING_GLOBE")
    socket = bpy.data.objects.get(f"{floor}_CEILING_SOCKET")
    canopy = bpy.data.objects.get(f"{floor}_CEILING_CANOPY")
    cord = bpy.data.objects.get(f"{floor}_CEILING_CORD")
    light = bpy.data.objects.get(f"{floor}_HOVER_LIGHT")
    parts = [o for o in (globe, socket, canopy, cord, light) if o]
    if globe:
        empty.location = globe.location
        torus(f"{floor}_LAMP_COLLAR", (globe.location.x, globe.location.y, globe.location.z + globe.dimensions.z * 0.40), max(globe.dimensions.x * 0.18, 0.075), 0.022, MAT_BRASS, floor, "lamp_fixture")
    for part in parts:
        part["web_control_id"] = f"Room_{idx:02d}_Lamp"
        part["web_export_role"] = "lamp_light" if part.type == "LIGHT" else "lamp_fixture"
    if light:
        light.data.color = (1.0, 0.50, 0.20)
        # Off at rest is essential: the add-on fades only the hovered floor to
        # its already-authored hover_target_energy.
        light.data.energy = 0.0
        light.data.shadow_soft_size = 1.15
    for candidate in bpy.data.objects:
        if candidate.type == "LIGHT" and candidate.get("hover_parent") == f"{floor}_HOVER_LIGHT":
            candidate.data.energy = 0.0
    for fixture in (globe, bpy.data.objects.get(f"{floor}_LAMP_BULB")):
        mat = fixture.active_material if fixture else None
        shader = principled(mat)
        set_input(shader, "Emission Strength", 0.0)


# Roof and chimney: stronger blue glazed-tile response and finished edges.
for mat in bpy.data.materials:
    if "ROOF" in mat.name.upper() and "IVORY" not in mat.name.upper() and mat.use_nodes:
        shader = principled(mat)
        base = shader.inputs.get("Base Color") if shader else None
        if base:
            old = base.default_value
            base.default_value = (min(old[0] * 0.82, 0.34), min(old[1] * 0.92, 0.45), min(old[2] * 1.15 + 0.035, 0.62), old[3])
            mat.diffuse_color = base.default_value
        set_input(shader, "Roughness", 0.39)
        set_input(shader, "Coat Weight", 0.12)
        set_input(shader, "Coat Roughness", 0.24)

for obj in bpy.data.objects:
    if obj.name.startswith("ROOF_") and obj.type == "MESH":
        if not any(m.type == "BEVEL" for m in obj.modifiers):
            bevel(obj, 0.015, 3)

chimney = bpy.data.objects.get("CHIMNEY")
if chimney:
    for i, z in enumerate((11.62, 11.78)):
        box(f"CHIMNEY_BAND_{i}", (chimney.location.x, chimney.location.y, z), (0.68, 0.68, 0.045), MAT_LIGHT_OAK, "ROOFTOP", 0.012, "roof_detail")


# Final scene/export hygiene.
for obj in upgrade.objects:
    obj.hide_render = False
    obj.hide_viewport = False
    if obj.type == "MESH":
        obj["gltf_export"] = True

scene = bpy.context.scene
scene.render.filepath = RENDER_PATH
scene.render.image_settings.file_format = "PNG"
scene.render.resolution_percentage = 100

assert_protected_state(protected_before)
bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
print(f"HOUSE_UPGRADE_COMPLETE objects={len(upgrade.objects)} blend={BLEND_PATH}")
