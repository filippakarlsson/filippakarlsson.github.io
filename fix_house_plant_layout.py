"""Correct plant scale and support placement in the existing house only."""

import bpy
from mathutils import Matrix, Vector


BLEND_PATH = "/Users/filippakarlsson/Desktop/filippa_house_reference_rebuilt.blend"
VERSION = "plant-layout-2026-08-24-v1"


def transform_plant(prefix, source_base, target_base, factor, floor):
    source = Vector(source_base)
    target = Vector(target_base)
    world_transform = Matrix.Translation(target) @ Matrix.Scale(factor, 4) @ Matrix.Translation(-source)
    changed = 0
    for obj in [o for o in bpy.data.objects if o.name.startswith(prefix)]:
        if obj.type not in {"MESH", "CURVE"} or not obj.data:
            continue
        if obj.data.get("plant_layout_version") == VERSION:
            continue
        local_transform = obj.matrix_world.inverted() @ world_transform @ obj.matrix_world
        obj.data.transform(local_transform)
        obj.data["plant_layout_version"] = VERSION
        obj.data["plant_display_scale"] = factor
        obj["portfolio_floor"] = floor
        changed += 1
    print(f"PLANT_LAYOUT {prefix} changed={changed} scale={factor}")


# Floor-standing plants: larger silhouettes with pot bases exactly on floors.
transform_plant("BASEMENT_PLANT_", (2.65, 0.15, 0.18), (2.62, 0.12, 0.28), 1.45, "BASEMENT")
transform_plant("WELCOME_PLANT_", (-2.39, 0.05, 1.96), (-2.50, 0.10, 2.06), 1.55, "WELCOME")
transform_plant("PLAYROOM_PLANT_", (-3.10, 0.15, 3.74), (-3.05, 0.12, 3.84), 1.55, "PLAYROOM")
transform_plant("OFFICE_PLANT_", (-0.30, 0.12, 5.52), (-0.34, 0.12, 5.62), 1.35, "OFFICE")
transform_plant("STUDIO_PLANT_", (-2.75, 0.10, 7.30), (-2.72, 0.12, 7.40), 1.50, "STUDIO")
transform_plant("ROOFTOP_PLANT_", (2.90, 0.05, 9.08), (2.90, 0.05, 9.19), 1.30, "ROOFTOP")

# Furniture/shelf plants: intentionally smaller, but properly supported.
transform_plant("BASEMENT_BENCH_PLANT_", (-0.58, -0.02, 0.92), (-0.58, -0.02, 0.915), 1.25, "BASEMENT")
transform_plant("WELCOME_CONSOLE_PLANT_", (1.34, -0.01, 2.74), (1.34, -0.01, 2.63), 1.35, "WELCOME")
transform_plant("OFFICE_CORNER_PLANT_", (-3.08, 0.07, 6.12), (-3.08, 0.07, 6.12), 1.25, "OFFICE")
transform_plant("STUDIO_SHELF_FERN_", (-2.98, 1.145, 8.24), (-2.98, 1.145, 8.24), 1.30, "STUDIO")
transform_plant("STUDIO_SHELF_SNAKE_", (-2.58, 1.145, 8.62), (-2.58, 1.145, 8.62), 1.12, "STUDIO")

# Move the second studio plant onto the flat-file cabinet rather than leaving
# another pot on the floor.
transform_plant("STUDIO_TALL_PLANT_", (0.95, 0.15, 7.30), (2.18, 0.08, 8.16), 0.92, "STUDIO")

bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
print("PLANT_LAYOUT_COMPLETE")

