"""Attach interactive light sources to visible fixtures in the existing blend."""

import os

import bpy


BLEND_PATH = "/Users/filippakarlsson/Desktop/filippa_house_reference_rebuilt.blend"


def main():
    if os.path.realpath(bpy.data.filepath) != os.path.realpath(BLEND_PATH):
        raise RuntimeError(f"Wrong source blend: {bpy.data.filepath}")

    removed = []
    # These were broad invisible room fills, which made the hover illumination
    # appear detached from the modeled lamps.  The same useful energy is moved
    # into the real pendant bulb below.
    for obj in list(bpy.data.objects):
        if obj.type == "LIGHT" and "CEILING_FILL" in obj.name and "HOVER" in obj.name:
            removed.append(obj.name)
            bpy.data.objects.remove(obj, do_unlink=True)

    attached = []
    for light in bpy.data.objects:
        if light.type != "LIGHT" or "HOVER" not in light.name:
            continue
        fixture_name = light.get("shade_object", "")
        fixture = bpy.data.objects.get(fixture_name)
        if fixture is not None:
            light.location = fixture.matrix_world.translation
            light["physical_source_object"] = fixture.name
            attached.append((light.name, fixture.name))

        light.data.energy = 0.0
        light.data.use_shadow = True
        light.data.use_soft_falloff = True
        light.data.color = (1.0, 0.55, 0.25)
        if light.name.endswith("_HOVER_LIGHT"):
            light["hover_target_energy"] = 380.0
            light["physical_source_offset_z"] = -0.21
            light.location.z -= 0.21
            light.data.shadow_soft_size = 0.20
        elif "SIGN" in light.name:
            light["hover_target_energy"] = 40.0
            light["physical_source_offset_z"] = 0.0
            light.data.shadow_soft_size = 0.16
        else:
            light["hover_target_energy"] = 90.0
            light["physical_source_offset_z"] = 0.0
            light.data.shadow_soft_size = 0.10

    bpy.context.scene["hover_light_source_pass"] = "visible-fixtures-v1"
    bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
    print("Removed invisible fills:", removed)
    print("Attached light sources:", attached)


if __name__ == "__main__":
    main()
