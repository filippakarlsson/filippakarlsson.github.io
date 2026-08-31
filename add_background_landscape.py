"""Add detailed procedural grass and background trees to the existing house."""

import math
import os
import random

import bpy
from mathutils import Vector


BLEND_PATH = "/Users/filippakarlsson/Desktop/filippa_house_reference_rebuilt.blend"
FINAL_RENDER = "/Users/filippakarlsson/Desktop/filippa_house_reference_rebuilt.png"
PREVIEW_RENDER = "/tmp/filippa_house_landscape_preview.png"
COLLECTION_NAME = "BACKGROUND_LANDSCAPE"
PREFIX = "LANDSCAPE_"
RNG = random.Random(20260820)


def principled(material):
    return next((n for n in material.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)


def set_input(shader, name, value):
    if shader and name in shader.inputs:
        shader.inputs[name].default_value = value


def simple_material(name, color, roughness, sheen=0.0, subsurface=0.0):
    material = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    material.use_nodes = True
    shader = principled(material)
    shader.inputs["Base Color"].default_value = (*color, 1.0)
    shader.inputs["Roughness"].default_value = roughness
    set_input(shader, "Sheen Weight", sheen)
    set_input(shader, "Subsurface Weight", subsurface)
    material.diffuse_color = (*color, 1.0)
    return material


def grass_ground_material():
    name = "LANDSCAPE realistic grass ground"
    material = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()

    output = nodes.new("ShaderNodeOutputMaterial")
    shader = nodes.new("ShaderNodeBsdfPrincipled")
    shader.inputs["Roughness"].default_value = 0.84
    set_input(shader, "Specular IOR Level", 0.28)

    texcoord = nodes.new("ShaderNodeTexCoord")
    noise = nodes.new("ShaderNodeTexNoise")
    noise.noise_dimensions = "3D"
    noise.inputs["Scale"].default_value = 9.0
    noise.inputs["Detail"].default_value = 6.0
    noise.inputs["Roughness"].default_value = 0.72

    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.20
    ramp.color_ramp.elements[0].color = (0.025, 0.095, 0.018, 1.0)
    ramp.color_ramp.elements[1].position = 0.82
    ramp.color_ramp.elements[1].color = (0.18, 0.37, 0.07, 1.0)
    middle = ramp.color_ramp.elements.new(0.52)
    middle.color = (0.075, 0.22, 0.035, 1.0)

    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.28
    bump.inputs["Distance"].default_value = 0.055

    links.new(texcoord.outputs["Generated"], noise.inputs["Vector"])
    links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], shader.inputs["Base Color"])
    links.new(noise.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], shader.inputs["Normal"])
    links.new(shader.outputs["BSDF"], output.inputs["Surface"])
    material.diffuse_color = (0.08, 0.24, 0.035, 1.0)
    return material


def bark_material():
    name = "LANDSCAPE detailed bark"
    material = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()

    output = nodes.new("ShaderNodeOutputMaterial")
    shader = nodes.new("ShaderNodeBsdfPrincipled")
    shader.inputs["Roughness"].default_value = 0.88
    set_input(shader, "Specular IOR Level", 0.22)
    texcoord = nodes.new("ShaderNodeTexCoord")
    noise = nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 5.0
    noise.inputs["Detail"].default_value = 7.0
    noise.inputs["Roughness"].default_value = 0.78
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (0.06, 0.025, 0.010, 1.0)
    ramp.color_ramp.elements[1].color = (0.32, 0.14, 0.050, 1.0)
    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.42
    bump.inputs["Distance"].default_value = 0.075
    links.new(texcoord.outputs["Generated"], noise.inputs["Vector"])
    links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], shader.inputs["Base Color"])
    links.new(noise.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], shader.inputs["Normal"])
    links.new(shader.outputs["BSDF"], output.inputs["Surface"])
    material.diffuse_color = (0.14, 0.055, 0.018, 1.0)
    return material


def rounded_canopy_material():
    name = "LANDSCAPE rounded natural canopy"
    material = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    shader = nodes.new("ShaderNodeBsdfPrincipled")
    shader.inputs["Roughness"].default_value = 0.54
    set_input(shader, "Sheen Weight", 0.08)
    set_input(shader, "Subsurface Weight", 0.025)
    texcoord = nodes.new("ShaderNodeTexCoord")
    noise = nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 3.8
    noise.inputs["Detail"].default_value = 4.0
    noise.inputs["Roughness"].default_value = 0.68
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (0.040, 0.15, 0.028, 1.0)
    ramp.color_ramp.elements[1].color = (0.21, 0.43, 0.10, 1.0)
    middle = ramp.color_ramp.elements.new(0.52)
    middle.color = (0.085, 0.28, 0.050, 1.0)
    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.07
    bump.inputs["Distance"].default_value = 0.025
    links.new(texcoord.outputs["Generated"], noise.inputs["Vector"])
    links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], shader.inputs["Base Color"])
    links.new(noise.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], shader.inputs["Normal"])
    links.new(shader.outputs["BSDF"], output.inputs["Surface"])
    material.diffuse_color = (0.085, 0.26, 0.05, 1.0)
    return material


def landscape_collection():
    found = bpy.data.collections.get(COLLECTION_NAME)
    if found is None:
        found = bpy.data.collections.new(COLLECTION_NAME)
        bpy.context.scene.collection.children.link(found)
    return found


def move_to_collection(obj):
    target = landscape_collection()
    for current in list(obj.users_collection):
        current.objects.unlink(obj)
    target.objects.link(obj)


def clear_previous():
    for obj in list(bpy.data.objects):
        if obj.name.startswith(PREFIX):
            bpy.data.objects.remove(obj, do_unlink=True)


def create_grass_blades(ground_top, materials):
    vertices = []
    faces = []
    material_indices = []

    def excluded(x, y):
        inside_house = -4.45 < x < 4.45 and -1.9 < y < 2.0
        exterior_stairs = 3.65 < x < 7.45 and -1.65 < y < -0.10
        return inside_house or exterior_stairs

    # Dense foreground and side lawn, with a slightly lighter far meadow.
    accepted = 0
    attempts = 0
    target = 4600
    while accepted < target and attempts < target * 5:
        attempts += 1
        x = RNG.uniform(-8.7, 8.7)
        y = RNG.uniform(-4.8, 8.7)
        if excluded(x, y):
            continue
        accepted += 1
        height = RNG.uniform(0.08, 0.24) * (1.15 if y < -1.8 else 1.0)
        width = RNG.uniform(0.012, 0.032)
        lean = RNG.uniform(-0.045, 0.045)
        angle = RNG.uniform(0.0, math.tau)
        dx = math.cos(angle) * width * 0.5
        dy = math.sin(angle) * width * 0.5
        lx = math.cos(angle + math.pi * 0.5) * lean
        ly = math.sin(angle + math.pi * 0.5) * lean
        z = ground_top + 0.006

        base = len(vertices)
        vertices.extend(
            [
                (x - dx, y - dy, z),
                (x + dx, y + dy, z),
                (x + dx * 0.18 + lx, y + dy * 0.18 + ly, z + height * 0.78),
                (x + lx, y + ly, z + height),
            ]
        )
        faces.append((base, base + 1, base + 2, base + 3))
        material_indices.append(RNG.randrange(len(materials)))

        # A crossed blade gives each tuft volume from the three-quarter camera.
        dx2 = math.cos(angle + math.pi * 0.5) * width * 0.42
        dy2 = math.sin(angle + math.pi * 0.5) * width * 0.42
        base = len(vertices)
        vertices.extend(
            [
                (x - dx2, y - dy2, z),
                (x + dx2, y + dy2, z),
                (x + dx2 * 0.18 + lx, y + dy2 * 0.18 + ly, z + height * 0.78),
                (x + lx, y + ly, z + height),
            ]
        )
        faces.append((base, base + 1, base + 2, base + 3))
        material_indices.append(RNG.randrange(len(materials)))

    mesh = bpy.data.meshes.new(PREFIX + "GRASS_BLADES_MESH")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(PREFIX + "GRASS_BLADES", mesh)
    landscape_collection().objects.link(obj)
    for mat in materials:
        mesh.materials.append(mat)
    for polygon, material_index in zip(mesh.polygons, material_indices):
        polygon.material_index = material_index
    return obj


def cylinder_between(name, start, end, radius_start, radius_end, mat):
    start = Vector(start)
    end = Vector(end)
    vector = end - start
    bpy.ops.mesh.primitive_cone_add(
        vertices=10,
        radius1=radius_start,
        radius2=radius_end,
        depth=vector.length,
        location=(start + end) * 0.5,
    )
    obj = bpy.context.object
    obj.name = name
    obj.rotation_euler = vector.to_track_quat("Z", "Y").to_euler()
    obj.data.materials.append(mat)
    bpy.ops.object.shade_smooth()
    move_to_collection(obj)
    return obj


def join_objects(objects, name):
    if not objects:
        return None
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.object.join()
    objects[0].name = name
    return objects[0]


def foliage_cluster(name, location, scale, material):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=1.0, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    obj.rotation_euler = (
        RNG.uniform(-0.35, 0.35),
        RNG.uniform(-0.35, 0.35),
        RNG.uniform(0.0, math.tau),
    )
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(material)
    bpy.ops.object.shade_smooth()
    move_to_collection(obj)
    return obj


def leaf_detail_mesh(name, centers, materials, count, size_scale):
    vertices = []
    faces = []
    indices = []
    for _ in range(count):
        center, spread = RNG.choice(centers)
        x = center.x + RNG.uniform(-spread.x, spread.x)
        y = center.y + RNG.uniform(-spread.y, spread.y)
        z = center.z + RNG.uniform(-spread.z, spread.z)
        length = RNG.uniform(0.070, 0.150) * size_scale
        width = length * RNG.uniform(0.38, 0.64)
        azimuth = RNG.uniform(0.0, math.tau)
        tilt = RNG.uniform(0.30, 1.28)
        long_axis = Vector(
            (
                math.cos(azimuth) * math.sin(tilt),
                math.sin(azimuth) * math.sin(tilt),
                math.cos(tilt),
            )
        )
        side_axis = Vector((-math.sin(azimuth), math.cos(azimuth), 0.0))
        midpoint = Vector((x, y, z))
        base = len(vertices)
        vertices.extend(
            [
                midpoint - long_axis * length,
                midpoint - long_axis * length * 0.28 - side_axis * width * 0.78,
                midpoint + long_axis * length * 0.34 - side_axis * width,
                midpoint + long_axis * length,
                midpoint + long_axis * length * 0.34 + side_axis * width,
                midpoint - long_axis * length * 0.28 + side_axis * width * 0.78,
            ]
        )
        faces.append((base, base + 1, base + 2, base + 3, base + 4, base + 5))
        indices.append(RNG.randrange(len(materials)))

    mesh = bpy.data.meshes.new(name + "_MESH")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    landscape_collection().objects.link(obj)
    for mat in materials:
        mesh.materials.append(mat)
    for polygon, index in zip(mesh.polygons, indices):
        polygon.material_index = index
    return obj


def create_tree(index, x, y, height, breadth, bark, canopy_material, leaf_materials, ground_top, distance_fade=1.0):
    base = Vector((x, y, ground_top))
    trunk_top = base + Vector((RNG.uniform(-0.18, 0.18), RNG.uniform(-0.12, 0.12), height * 0.70))
    trunk_radius = 0.16 * (height / 11.0)
    woody = [
        cylinder_between(
            PREFIX + f"TREE_{index}_TRUNK",
            base,
            trunk_top,
            trunk_radius,
            trunk_radius * 0.42,
            bark,
        )
    ]

    branch_ends = []
    primary_ends = []
    for branch_index in range(9):
        level = RNG.uniform(0.43, 0.76)
        start = base + (trunk_top - base) * level
        angle = branch_index / 9.0 * math.tau + RNG.uniform(-0.28, 0.28)
        reach = breadth * RNG.uniform(0.38, 0.72)
        end = start + Vector(
            (
                math.cos(angle) * reach,
                math.sin(angle) * reach * 0.72,
                height * RNG.uniform(0.10, 0.25),
            )
        )
        woody.append(
            cylinder_between(
                PREFIX + f"TREE_{index}_BRANCH_{branch_index}",
                start,
                end,
                trunk_radius * RNG.uniform(0.22, 0.34),
                trunk_radius * 0.08,
                bark,
            )
        )
        branch_ends.append(end)
        primary_ends.append(end)
        # Fine secondary branches keep the silhouette tree-like when the
        # smaller canopy clusters leave natural gaps.
        for twig_index in range(1):
            twig_start = start.lerp(end, RNG.uniform(0.48, 0.68))
            twig_angle = angle + RNG.choice((-0.52, 0.52)) + RNG.uniform(-0.18, 0.18)
            twig_end = end + Vector(
                (
                    math.cos(twig_angle) * breadth * RNG.uniform(0.16, 0.28),
                    math.sin(twig_angle) * breadth * RNG.uniform(0.12, 0.22),
                    height * RNG.uniform(0.035, 0.085),
                )
            )
            woody.append(
                cylinder_between(
                    PREFIX + f"TREE_{index}_TWIG_{branch_index}_{twig_index}",
                    twig_start,
                    twig_end,
                    trunk_radius * 0.105,
                    trunk_radius * 0.025,
                    bark,
                )
            )
            branch_ends.append(twig_end)
    join_objects(woody, PREFIX + f"TREE_{index}_BARK")

    crown_center = trunk_top + Vector((0.0, 0.0, height * 0.055))
    canopy_centers = [
        crown_center,
        crown_center + Vector((breadth * 0.40, 0.0, -height * 0.035)),
        crown_center + Vector((-breadth * 0.40, 0.0, -height * 0.035)),
        crown_center + Vector((0.0, breadth * 0.29, -height * 0.01)),
        crown_center + Vector((0.0, -breadth * 0.29, -height * 0.01)),
        crown_center + Vector((breadth * 0.31, breadth * 0.19, height * 0.025)),
        crown_center + Vector((-breadth * 0.31, breadth * 0.19, height * 0.025)),
        crown_center + Vector((breadth * 0.29, -breadth * 0.20, height * 0.035)),
        crown_center + Vector((-breadth * 0.29, -breadth * 0.20, height * 0.035)),
        crown_center + Vector((0.0, 0.0, height * 0.080)),
        crown_center + Vector((breadth * 0.18, 0.0, -height * 0.080)),
        crown_center + Vector((-breadth * 0.18, 0.0, -height * 0.080)),
    ]
    canopy_objects = []
    detail_centers = []
    # Overlapping smooth clusters echo the house's rounded dollhouse forms,
    # while varied size, color, and placement keep the canopy natural.
    cluster_index = 0
    for anchor in canopy_centers:
        for _ in range(2):
            radius = breadth * RNG.uniform(0.23, 0.34)
            location = anchor + Vector(
                (
                    RNG.uniform(-radius * 0.34, radius * 0.34),
                    RNG.uniform(-radius * 0.28, radius * 0.28),
                    RNG.uniform(-radius * 0.25, radius * 0.34),
                )
            )
            scale = (
                radius * RNG.uniform(0.90, 1.25),
                radius * RNG.uniform(0.76, 1.05),
                radius * RNG.uniform(0.88, 1.28),
            )
            canopy_objects.append(
                foliage_cluster(
                    PREFIX + f"TREE_{index}_CANOPY_{cluster_index}",
                    location,
                    scale,
                    RNG.choice(leaf_materials),
                )
            )
            detail_centers.append((location, Vector(scale) * 0.92))
            cluster_index += 1
    canopy = join_objects(canopy_objects, PREFIX + f"TREE_{index}_CANOPY")
    if canopy:
        bpy.context.view_layer.objects.active = canopy
        remesh = canopy.modifiers.new("continuous organic canopy", "REMESH")
        remesh.mode = "VOXEL"
        remesh.voxel_size = max(0.075, breadth * 0.055)
        remesh.adaptivity = 0.04
        remesh.use_remove_disconnected = False
        remesh.use_smooth_shade = True
        bpy.ops.object.modifier_apply(modifier=remesh.name)
        smooth = canopy.modifiers.new("soft rounded canopy", "SMOOTH")
        smooth.factor = 0.42
        smooth.iterations = 3
        bpy.ops.object.modifier_apply(modifier=smooth.name)

        # A low-strength cloud displacement keeps the silhouette naturally
        # uneven without reintroducing sharp, rough individual-leaf geometry.
        texture_name = PREFIX + f"TREE_{index}_CANOPY_CONTOUR"
        contour = bpy.data.textures.get(texture_name) or bpy.data.textures.new(texture_name, type="CLOUDS")
        contour.noise_scale = max(0.28, breadth * 0.19)
        contour.noise_depth = 2
        displace = canopy.modifiers.new("subtle organic canopy contour", "DISPLACE")
        displace.texture = contour
        displace.texture_coords = "GLOBAL"
        displace.strength = breadth * 0.050
        displace.mid_level = 0.5
        bpy.ops.object.modifier_apply(modifier=displace.name)
        finish_smooth = canopy.modifiers.new("gentle contour finish", "SMOOTH")
        finish_smooth.factor = 0.16
        finish_smooth.iterations = 1
        bpy.ops.object.modifier_apply(modifier=finish_smooth.name)
        canopy.data.materials.clear()
        canopy.data.materials.append(canopy_material)
        bpy.ops.object.shade_smooth()

    # A restrained layer of individual leaves breaks up the silhouette without
    # restoring the previous rough, spiky appearance.
    leaf_detail_mesh(
        PREFIX + f"TREE_{index}_LEAF_DETAIL",
        detail_centers,
        leaf_materials,
        int(820 * distance_fade),
        max(0.70, distance_fade * 0.78),
    )


def add_landscape():
    ground = bpy.data.objects.get("GROUND")
    if ground is None:
        raise RuntimeError("GROUND object is missing")
    ground_top = ground.location.z + ground.dimensions.z * 0.5

    ground_mat = grass_ground_material()
    ground.data.materials.clear()
    ground.data.materials.append(ground_mat)

    grass_materials = [
        simple_material("LANDSCAPE grass blade deep", (0.035, 0.18, 0.025), 0.72, 0.05, 0.02),
        simple_material("LANDSCAPE grass blade green", (0.09, 0.31, 0.045), 0.70, 0.05, 0.025),
        simple_material("LANDSCAPE grass blade sunlit", (0.20, 0.43, 0.075), 0.68, 0.06, 0.025),
    ]
    create_grass_blades(ground_top, grass_materials)

    bark = bark_material()
    canopy = rounded_canopy_material()
    leaf_materials = [
        simple_material("LANDSCAPE leaves deep", (0.045, 0.17, 0.035), 0.56, 0.08, 0.035),
        simple_material("LANDSCAPE leaves green", (0.10, 0.31, 0.060), 0.54, 0.09, 0.04),
        simple_material("LANDSCAPE leaves light", (0.20, 0.42, 0.10), 0.52, 0.10, 0.045),
    ]

    trees = [
        (-6.0, 6.0, 8.5, 1.50, 0.96),
        (-4.4, 8.0, 14.2, 1.90, 0.84),
        (-0.2, 9.0, 14.8, 2.00, 0.82),
        (4.1, 8.1, 14.0, 1.90, 0.84),
        (6.5, 6.1, 8.4, 1.48, 0.96),
    ]
    for index, (x, y, height, breadth, fade) in enumerate(trees):
        create_tree(index, x, y, height, breadth, bark, canopy, leaf_materials, ground_top, fade)


def main():
    if os.path.realpath(bpy.data.filepath) != os.path.realpath(BLEND_PATH):
        raise RuntimeError(f"Wrong source blend: {bpy.data.filepath}")
    clear_previous()
    add_landscape()

    scene = bpy.context.scene
    for obj in scene.objects:
        if obj.type == "LIGHT" and "HOVER" in obj.name:
            obj.data.energy = 0.0
    scene["background_landscape_pass"] = "detailed-trees-grass-v1"
    scene.render.resolution_percentage = 100
    scene.eevee.taa_render_samples = 160
    scene.render.filepath = FINAL_RENDER
    bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)

    preview = os.environ.get("HOUSE_LANDSCAPE_PREVIEW") == "1"
    if preview:
        scene.render.resolution_percentage = 50
        scene.eevee.taa_render_samples = 64
        scene.render.filepath = PREVIEW_RENDER
    bpy.ops.render.render(write_still=True)
    if not preview:
        bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
    print("Landscape created; preview=", preview, "render=", scene.render.filepath)


if __name__ == "__main__":
    main()
