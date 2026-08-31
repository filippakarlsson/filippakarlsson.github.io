"""Remove background trees while preserving all landscape grass."""

import os

import bpy


BLEND_PATH = "/Users/filippakarlsson/Desktop/filippa_house_reference_rebuilt.blend"
RENDER_PATH = "/Users/filippakarlsson/Desktop/filippa_house_reference_rebuilt.png"


def main():
    if os.path.realpath(bpy.data.filepath) != os.path.realpath(BLEND_PATH):
        raise RuntimeError(f"Wrong source blend: {bpy.data.filepath}")

    removed = []
    for obj in list(bpy.data.objects):
        if obj.name.startswith("LANDSCAPE_TREE_"):
            removed.append(obj.name)
            bpy.data.objects.remove(obj, do_unlink=True)

    # Remove only now-unused procedural tree contour textures. Grass materials,
    # the grass blade mesh, and the GROUND material are deliberately preserved.
    for texture in list(bpy.data.textures):
        if texture.name.startswith("LANDSCAPE_TREE_") and texture.users == 0:
            bpy.data.textures.remove(texture)

    scene = bpy.context.scene
    for obj in scene.objects:
        if obj.type == "LIGHT" and "HOVER" in obj.name:
            obj.data.energy = 0.0
    scene["background_landscape_pass"] = "grass-only-trees-removed"
    scene.render.resolution_percentage = 100
    scene.eevee.taa_render_samples = 160
    scene.render.filepath = RENDER_PATH

    bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
    bpy.ops.render.render(write_still=True)
    bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
    print("Removed tree objects:", len(removed))
    print("Grass preserved:", bpy.data.objects.get("LANDSCAPE_GRASS_BLADES") is not None)


if __name__ == "__main__":
    main()
