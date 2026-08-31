import bpy, math, os
from mathutils import Vector

# Fresh reference-first rebuild. This script is an internal build tool; the
# deliverable is the .blend it writes to the Desktop.
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for datablocks in (bpy.data.materials, bpy.data.curves, bpy.data.meshes, bpy.data.cameras, bpy.data.lights):
    pass

def mat(name, color, rough=.72, emission=None):
    m=bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.diffuse_color=(*color,1)
    m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value=(*color,1)
    # Soft collectible-toy finish: colorful painted surfaces receive a
    # restrained satin clear coat and tighter highlights instead of reading
    # as completely matte. Natural/technical materials keep their identity.
    matte_names={'potting soil','basement concrete','paper'}
    technical_names={'window glass','frosted lamp glass','black metal','screen','charcoal'}
    wood_names={'warm oak','light oak','dark walnut'}
    leaf_names={'leaf dark','leaf light'}
    if name in matte_names:
        final_rough=rough; coat=.0; coat_rough=.35
    elif name in technical_names:
        final_rough=rough; coat=.08; coat_rough=.22
    elif name in wood_names:
        final_rough=min(rough,.48); coat=.16; coat_rough=.25
    elif name in leaf_names:
        final_rough=min(rough,.40); coat=.18; coat_rough=.20
    else:
        final_rough=min(rough,.36); coat=.30; coat_rough=.17
    p.inputs['Roughness'].default_value=final_rough
    if 'Coat Weight' in p.inputs:
        p.inputs['Coat Weight'].default_value=coat
    if 'Coat Roughness' in p.inputs:
        p.inputs['Coat Roughness'].default_value=coat_rough
    if 'Specular IOR Level' in p.inputs:
        p.inputs['Specular IOR Level'].default_value=.42
    if emission is not None:
        p.inputs['Emission Color'].default_value=(*emission,1)
        p.inputs['Emission Strength'].default_value=0
    return m

WHITE=mat('ivory plaster',(0.91,.88,.82))
CREAM=mat('attic cream',(.89,.80,.68))
OAK=mat('warm oak',(.55,.32,.16))
LIGHT_OAK=mat('light oak',(.72,.49,.27))
DARK_WOOD=mat('dark walnut',(.20,.11,.07))
SOIL=mat('potting soil',(.075,.045,.025),.96)
CHARCOAL=mat('charcoal',(.08,.075,.07))
CONCRETE=mat('basement concrete',(.22,.23,.22),.9)
SAGE=mat('studio sage',(.48,.57,.39))
MUSTARD=mat('office mustard',(.76,.55,.24))
CORAL=mat('playroom coral',(.77,.38,.36))
LAVENDER=mat('welcome lavender',(.55,.46,.65))
BLUE=mat('attic blue',(.43,.57,.62))
GREEN=mat('leaf dark',(.15,.35,.16))
GREEN2=mat('leaf light',(.29,.50,.23))
PAPER=mat('paper',(.91,.86,.74))
PINK=mat('soft pink',(.74,.38,.44))
PURPLE=mat('door lavender',(.56,.43,.63))
YELLOW=mat('chair yellow',(.84,.57,.16))
SCREEN=mat('screen',(.025,.032,.035),.35)
METAL=mat('black metal',(.055,.06,.06),.4)
ROOF=mat('roof blue gray',(.34,.39,.49))
ROOF_TILE_LIGHT=mat('roof tile blue light',(.40,.47,.60),.34)
ROOF_TILE_DARK=mat('roof tile blue dark',(.25,.31,.43),.32)
GLASS=mat('window glass',(.64,.78,.82),.12)
_window_glass_bsdf=GLASS.node_tree.nodes['Principled BSDF']
_window_glass_bsdf.inputs['Transmission Weight'].default_value=.90
_window_glass_bsdf.inputs['Roughness'].default_value=.07
if 'Alpha' in _window_glass_bsdf.inputs:
    _window_glass_bsdf.inputs['Alpha'].default_value=.24
GLASS.diffuse_color=(.64,.78,.82,.24)
if hasattr(GLASS,'surface_render_method'):
    GLASS.surface_render_method='DITHERED'
MIRROR=mat('mirror silver',(.52,.62,.65),.12)
_mirror_bsdf=MIRROR.node_tree.nodes['Principled BSDF']
_mirror_bsdf.inputs['Metallic'].default_value=.88
FROSTED_GLASS=mat('frosted lamp glass',(1.0,.82,.56),.28)
_lamp_glass_bsdf=FROSTED_GLASS.node_tree.nodes['Principled BSDF']
_lamp_glass_bsdf.inputs['Transmission Weight'].default_value=.42
_lamp_glass_bsdf.inputs['IOR'].default_value=1.45
GLOW=mat('warm bulb',(.95,.63,.27),.25,(1,.38,.08))
PLAY_SIGN=mat('play sign coral glow',(.92,.30,.18),.38,(1.0,.16,.04))
_play_bsdf=PLAY_SIGN.node_tree.nodes.get('Principled BSDF')
_play_bsdf.inputs['Emission Strength'].default_value=1.8
WHITE_TEXT=mat('warm white lettering',(.98,.95,.86),.50,(1.0,.92,.76))
_white_text_bsdf=WHITE_TEXT.node_tree.nodes.get('Principled BSDF')
_white_text_bsdf.inputs['Emission Strength'].default_value=2.2

def box(name,loc,size,material,bevel=.045,rot=(0,0,0)):
    bpy.ops.mesh.primitive_cube_add(location=loc,rotation=rot)
    o=bpy.context.object; o.name=name; o.scale=(size[0]/2,size[1]/2,size[2]/2)
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    o.data.materials.append(material)
    if bevel:
        mod=o.modifiers.new('rounded edges','BEVEL'); mod.width=bevel; mod.segments=4
    return o

def cyl(name,loc,radius,depth,material,verts=32,rot=(0,0,0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=radius,depth=depth,location=loc,rotation=rot)
    o=bpy.context.object; o.name=name; o.data.materials.append(material)
    b=o.modifiers.new('soft rim','BEVEL'); b.width=min(radius*.18,.035); b.segments=3
    return o

def cone(name,loc,r1,r2,depth,material,rot=(0,0,0)):
    bpy.ops.mesh.primitive_cone_add(vertices=32,radius1=r1,radius2=r2,depth=depth,location=loc,rotation=rot)
    o=bpy.context.object; o.name=name; o.data.materials.append(material)
    b=o.modifiers.new('soft rim','BEVEL'); b.width=.018; b.segments=3
    return o

def sph(name,loc,scale,material):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32,ring_count=20,location=loc)
    o=bpy.context.object; o.name=name; o.scale=scale
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    o.data.materials.append(material); bpy.ops.object.shade_smooth()
    return o

def botanical_leaf(name,base,width,height,material,lean=0,twist=0):
    """Curved, pointed leaf mesh with thickness and a raised center vein."""
    rings=9
    verts=[]
    for i in range(rings):
        t=i/(rings-1)
        taper=math.sin(math.pi*t)**.72
        half=width*.5*taper
        # Gentle bowl/forward curve prevents the leaf reading as a flat card.
        curve_y=height*.055*math.sin(math.pi*t)
        curve_z=height*(t-.055*math.sin(math.pi*t))
        verts.extend([(-half,curve_y,curve_z),(half,curve_y,curve_z)])
    faces=[]
    for i in range(rings-1):
        a=i*2; faces.append((a,a+1,a+3,a+2))
    mesh=bpy.data.meshes.new(name+'_MESH')
    mesh.from_pydata(verts,[],faces); mesh.update()
    leaf=bpy.data.objects.new(name,mesh); bpy.context.collection.objects.link(leaf)
    leaf.location=base; leaf.rotation_euler=(0,math.radians(lean),math.radians(twist))
    leaf.data.materials.append(material)
    solid=leaf.modifiers.new('leaf thickness','SOLIDIFY'); solid.thickness=max(width*.035,.003)
    bevel=leaf.modifiers.new('soft leaf edge','BEVEL'); bevel.width=max(width*.018,.002); bevel.segments=2
    for poly in mesh.polygons: poly.use_smooth=True

    # A thin raised midrib adds botanical structure at close range.
    curve=bpy.data.curves.new(name+'_VEIN_CURVE','CURVE'); curve.dimensions='3D'; curve.bevel_depth=max(width*.018,.002); curve.bevel_resolution=2
    spline=curve.splines.new('POLY'); spline.points.add(rings-1)
    for i in range(rings):
        t=i/(rings-1)
        spline.points[i].co=(0,height*.057*math.sin(math.pi*t),height*(t-.055*math.sin(math.pi*t)),1)
    vein=bpy.data.objects.new(name+'_VEIN',curve); bpy.context.collection.objects.link(vein)
    vein.location=base; vein.rotation_euler=leaf.rotation_euler; vein.data.materials.append(GREEN)
    return leaf

def text_obj(name,body,loc,size=.10,material=CHARCOAL,align='CENTER'):
    bpy.ops.object.text_add(location=loc,rotation=(math.pi/2,0,0))
    o=bpy.context.object; o.name=name; o.data.body=body; o.data.align_x=align
    o.data.align_y='CENTER'; o.data.size=size; o.data.extrude=.004
    o.data.materials.append(material); return o

def beam(name,a,b,width,depth,material):
    a,b=Vector(a),Vector(b); mid=(a+b)/2
    o=box(name,mid,((b-a).length,depth,width),material,.025)
    o.rotation_euler=(b-a).to_track_quat('X','Z').to_euler(); return o

def plant(name,x,y,z,scale=1,species='broad'):
    # Tapered ceramic pot, raised rim and visible dark soil.
    cone(name+'_POT',(x,y,z+.125*scale),.16*scale,.12*scale,.25*scale,DARK_WOOD)
    cyl(name+'_POT_RIM',(x,y,z+.255*scale),.15*scale,.045*scale,DARK_WOOD,32)
    cyl(name+'_SOIL',(x,y,z+.282*scale),.12*scale,.020*scale,SOIL,28)

    stem_origin=(x,y,z+.285*scale)

    def add_leaf(i,dx,dy,base_z,width,height,lean,twist,material=None,stem=True):
        base=(x+dx*scale,y+dy*scale,z+base_z*scale)
        if stem: beam(f'{name}_STEM_{i}',stem_origin,base,.009*scale,.009*scale,GREEN)
        botanical_leaf(f'{name}_LEAF_{i}',base,width*scale,height*scale,
                       material or (GREEN if i%3 else GREEN2),lean,twist)

    if species == 'succulent':
        # Compact fleshy rosette for desks and small corners.
        for i,(dx,bz,w,h,lean,twist) in enumerate([
            (-.11,.29,.11,.20,-30,-15),(-.06,.30,.12,.23,-18,8),
            (0,.30,.13,.27,0,-4),(.07,.30,.12,.23,18,10),(.12,.29,.11,.20,30,-8),
            (-.04,.31,.10,.18,-10,25),(.05,.31,.10,.18,12,-24)]):
            add_leaf(i,dx,(i%2-.5)*.025,bz,w,h,lean,twist,stem=False)

    elif species == 'snake':
        # Narrow upright leaves, varied height and subtle alternating color.
        for i,(dx,bz,w,h,lean) in enumerate([
            (-.13,.29,.065,.42,-8),(-.08,.29,.07,.56,-5),(-.02,.29,.065,.68,-2),
            (.04,.29,.075,.50,3),(.10,.29,.065,.62,6),(.15,.29,.06,.40,9)]):
            add_leaf(i,dx,(i%2)*.018,bz,w,h,lean,(i-3)*3,GREEN2 if i%2 else GREEN,stem=False)

    elif species == 'fern':
        # Fine outward fronds with many smaller leaves.
        for i in range(12):
            side=-1 if i<6 else 1; row=i%6
            add_leaf(i,side*(.035+row*.026),(row%2)*.015,.29,
                     .055,.19+row*.025,side*(18+row*6),side*(8+row*3),
                     GREEN2 if row%2 else GREEN)

    elif species == 'tree':
        # Thin woody trunk and small oval leaves, as in the office reference.
        trunk_top=(x,y,z+.78*scale)
        beam(name+'_TRUNK',stem_origin,trunk_top,.026*scale,.026*scale,OAK)
        tips=[(-.24,.57),(-.20,.72),(-.14,.84),(-.08,.66),(-.03,.94),
              (.04,.74),(.09,.88),(.14,.64),(.19,.79),(.24,.58),
              (-.27,.87),(.27,.91),(.01,.58)]
        for i,(dx,dzv) in enumerate(tips):
            branch_base=(x,y,z+.53*scale)
            base=(x+dx*scale,y+(i%2)*.018*scale,z+(dzv-.15)*scale)
            beam(f'{name}_BRANCH_{i}',branch_base,base,.014*scale,.014*scale,OAK)
            botanical_leaf(f'{name}_LEAF_{i}',base,.075*scale,.15*scale,
                           GREEN if i%2 else GREEN2,dx*70,(i-3)*7)

    else:  # broad leaf floor plant
        for i,(dx,bz,w,h,lean,twist) in enumerate([
            (-.17,.30,.10,.28,-27,-12),(-.11,.31,.11,.35,-18,8),
            (-.04,.31,.11,.42,-7,-4),(.03,.31,.12,.36,4,7),
            (.10,.31,.11,.40,13,-8),(.17,.30,.10,.31,25,12),
            (0,.32,.10,.46,0,0),(.20,.30,.085,.25,31,-15)]):
            add_leaf(i,dx,(i%2-.5)*.025,bz,w,h,lean,twist)

def bookshelf(name,x,y,z,w=1.0,h=1.35,d=.30,books=True):
    box(name+'_L',(x-w/2,y,z+h/2),(.07,d,h),DARK_WOOD,.025)
    box(name+'_R',(x+w/2,y,z+h/2),(.07,d,h),DARK_WOOD,.025)
    box(name+'_TOP',(x,y,z+h),(w,d,.07),DARK_WOOD,.025)
    for row in range(4):
        sz=z+.06+row*(h-.08)/4
        box(f'{name}_SHELF_{row}',(x,y,sz),(w,d,.06),DARK_WOOD,.018)
        if books:
            cursor=x-w/2+.10
            colors=[PINK,PAPER,BLUE,YELLOW,PURPLE,SAGE]
            for j in range(6):
                bw=.055+(j%3)*.012; bh=.18+(j%4)*.035
                if cursor+bw>x+w/2-.08: break
                book=box(f'{name}_BOOK_{row}_{j}',(cursor,y-.17,sz+.04+bh/2),(bw,.10,bh),colors[(row+j)%len(colors)],.008)
                book.rotation_euler[1]=math.radians((-4,0,3)[j%3]); cursor+=bw+.035

def framed_art(name,x,y,z,w,h,color,title=None,subtitle=None):
    box(name+'_FRAME',(x,y,z),(w+.10,.06,h+.10),LIGHT_OAK,.018)
    box(name+'_CARD',(x,y-.04,z),(w,.025,h),color,.012)
    if title: text_obj(name+'_TITLE',title,(x,y-.065,z+.05),min(.10,w/5))
    if subtitle: text_obj(name+'_SUB',subtitle,(x,y-.067,z-.12),min(.052,w/9))

def statement_sign(name,x,z,w,h,lines,card=PAPER,text_material=CHARCOAL,frame=LIGHT_OAK):
    """Reference-style framed room statement with readable stacked copy."""
    y=D/2-.14
    box(name+'_FRAME',(x,y,z),(w+.11,.075,h+.11),frame,.022)
    box(name+'_CARD',(x,y-.048,z),(w,.028,h),card,.014)
    body='\n'.join(lines)
    t=text_obj(name+'_TEXT',body,(x,y-.082,z),min(.115,w/5.4),text_material)
    t.data.space_line=1.08
    return t

def desk(name,x,y,z,chair_mat):
    box(name+'_TOP',(x,y,z+.68),(1.55,.58,.10),LIGHT_OAK,.045)
    for dx in (-.65,.65): box(name+f'_LEG_{dx}',(x+dx,y+.05,z+.33),(.09,.42,.62),OAK,.025)
    box(name+'_MONITOR',(x,y+.12,z+1.08),(.72,.10,.48),SCREEN,.055)
    box(name+'_SCREEN',(x,y+.055,z+1.08),(.61,.018,.36),BLUE,.018)
    box(name+'_STAND',(x,y+.11,z+.81),(.08,.10,.20),METAL,.018)
    box(name+'_KEYBOARD',(x,y-.25,z+.76),(.52,.20,.035),METAL,.018)
    box(name+'_CHAIR_SEAT',(x,y-.68,z+.45),(.58,.52,.17),chair_mat,.10)
    box(name+'_CHAIR_BACK',(x,y-.84,z+.77),(.56,.14,.62),chair_mat,.10)
    cyl(name+'_CHAIR_POST',(x,y-.68,z+.22),.045,.38,METAL,20)

def cozy_sofa(name,x,y,z,material):
    """Soft layered sofa with separate seat, back, arms and cushions."""
    box(name+'_BASE',(x,y,z+.28),(1.65,.70,.30),material,.14)
    box(name+'_BACK',(x,y+.25,z+.67),(1.62,.22,.72),material,.14)
    box(name+'_ARM_L',(x-.82,y-.02,z+.49),(.24,.68,.52),material,.12)
    box(name+'_ARM_R',(x+.82,y-.02,z+.49),(.24,.68,.52),material,.12)
    box(name+'_CUSHION_L',(x-.39,y-.24,z+.52),(.68,.45,.17),PAPER,.09)
    box(name+'_CUSHION_R',(x+.39,y-.24,z+.52),(.68,.45,.17),PAPER,.09)
    for dx in (-.65,.65): cyl(name+'_FOOT',(x+dx,y,z+.075),.045,.14,DARK_WOOD,16)

def pendant(room,center_z):
    # Keep the pendant high enough to wash the full room instead of making a
    # concentrated hotspot on the furniture directly beneath it.
    cyl(room+'_LAMP_CEILING_CANOPY',(0,-.50,center_z+.855),.115,.065,METAL,28)
    cyl(room+'_LAMP_CORD',(0,-.50,center_z+.72),.010,.26,METAL,12)
    cyl(room+'_LAMP_SOCKET',(0,-.50,center_z+.565),.065,.115,LIGHT_OAK,24)
    sph(room+'_LAMP_GLOBE',(0,-.50,center_z+.43),(.19,.19,.19),FROSTED_GLASS)
    bulb_mat=GLOW.copy(); bulb_mat.name=room+'_HOVER_BULB_MATERIAL'
    bulb=sph(room+'_LAMP_BULB',(0,-.50,center_z+.43),(.074,.074,.085),bulb_mat)
    bpy.ops.object.light_add(type='POINT',location=(0,-.45,center_z+.43))
    light=bpy.context.object; light.name=room+'_HOVER_LIGHT'; light.data.energy=0
    light.data.color=(1.0,.20,.035); light.data.shadow_soft_size=1.30
    light['floor']=room; light['shade_object']=bulb.name
    light['hover_target_energy']=520.0
    light['hover_target_emission']=2.35
    # Very soft ceiling fills share the same hover parent.  They extend the
    # warm wash toward both corners without creating another visible lamp or
    # a harsh central hotspot.
    for side,x in (('LEFT',-2.15),('RIGHT',2.15)):
        bpy.ops.object.light_add(type='POINT',location=(x,.10,center_z+.40))
        fill=bpy.context.object; fill.name=room+f'_CEILING_FILL_{side}_HOVER_ACCENT_LIGHT'
        fill.data.energy=0; fill.data.color=(1.0,.18,.03); fill.data.shadow_soft_size=1.45
        fill['hover_parent']=light.name
        fill['hover_target_energy']=90.0
        fill['hover_target_emission']=0.0

def hover_accent(room,name,loc,shade,energy=120.0,emission=1.55):
    """Link a practical table/task lamp to its room's main hover light."""
    linked_glow=shade
    if shade and 'LAMP_SHADE' in shade.name:
        # Preserve the fabric/painted shade and put the glow in a smaller
        # physical bulb inside it, with a visible metal socket beneath.  A
        # separate low emission on the fabric makes the shade visibly read as
        # switched on without turning it into a solid glowing plastic cone.
        shade_mat=shade.active_material.copy()
        shade_mat.name=name+'_HOVER_FABRIC_SHADE_MATERIAL'
        shade_mat.use_nodes=True
        shade_bsdf=shade_mat.node_tree.nodes.get('Principled BSDF')
        if shade_bsdf:
            if 'Emission Color' in shade_bsdf.inputs:
                shade_bsdf.inputs['Emission Color'].default_value=(1.0,.30,.055,1)
            if 'Emission Strength' in shade_bsdf.inputs:
                shade_bsdf.inputs['Emission Strength'].default_value=0
        shade.data.materials.clear(); shade.data.materials.append(shade_mat)
        bulb_mat=GLOW.copy(); bulb_mat.name=name+'_HOVER_BULB_MATERIAL'
        linked_glow=sph(name+'_BULB',loc,(.045,.045,.052),bulb_mat)
        cyl(name+'_BULB_SOCKET',(loc[0],loc[1],loc[2]-.058),.038,.075,METAL,20)
    elif shade and shade.active_material:
        # Non-lamp accents such as the playroom sign glow through their own
        # face material when that floor is hovered.
        shade_mat=shade.active_material.copy()
        shade_mat.name=name+'_HOVER_SHADE_MATERIAL'
        shade_mat.use_nodes=True
        bsdf=shade_mat.node_tree.nodes.get('Principled BSDF')
        if bsdf:
            if 'Emission Color' in bsdf.inputs:
                bsdf.inputs['Emission Color'].default_value=(1.0,.18,.025,1)
            if 'Emission Strength' in bsdf.inputs:
                bsdf.inputs['Emission Strength'].default_value=0
        shade.data.materials.clear(); shade.data.materials.append(shade_mat)
    bpy.ops.object.light_add(type='POINT',location=loc)
    accent=bpy.context.object; accent.name=name+'_HOVER_ACCENT_LIGHT'
    accent.data.energy=0; accent.data.color=(1.0,.16,.025)
    accent.data.shadow_soft_size=.55
    accent['hover_parent']=room+'_HOVER_LIGHT'
    accent['hover_target_energy']=energy
    accent['hover_target_emission']=emission
    if shade and 'LAMP_SHADE' in shade.name:
        accent['outer_shade_object']=shade.name
        accent['outer_shade_emission']=.70
    if linked_glow: accent['shade_object']=linked_glow.name
    return accent

W,D,H=7.6,3.05,1.78
BASE=.18
room_specs=[
    ('BASEMENT',CONCRETE),('WELCOME',LAVENDER),('PLAYROOM',CORAL),
    ('OFFICE',MUSTARD),('STUDIO',SAGE)
]

# Structure: white cutaway frame, colored backs, real stair core.
for i,(name,wall) in enumerate(room_specs):
    f=BASE+i*H; c=f+H/2
    box(name+'_BACK_WALL',(0,D/2,c),(W,.16,H),wall,.02)
    box(name+'_FLOOR',(0,0,f),(W+.35,D+.30,.20),WHITE,.055)
    box(name+'_TOP_BEAM',(0,0,f+H),(W+.35,D+.30,.22),WHITE,.055)
    # Segmented left side wall creates a genuine opening around the window;
    # previously the transparent pane sat over one solid white column.
    opening_y_min,opening_y_max=-.76,.46
    opening_z_min,opening_z_max=c-.56,c+.62
    front_depth=opening_y_min-(-D/2)
    back_depth=D/2-opening_y_max
    box(name+'_LEFT_FRAME',(-W/2,(-D/2+opening_y_min)/2,c),(.22,front_depth,H),wall,.05)
    box(name+'_LEFT_FRAME_BACK',(-W/2,(opening_y_max+D/2)/2,c),(.22,back_depth,H),wall,.05)
    lower_height=opening_z_min-f
    upper_height=f+H-opening_z_max
    box(name+'_LEFT_FRAME_BELOW',(-W/2,(opening_y_min+opening_y_max)/2,f+lower_height/2),
        (.22,opening_y_max-opening_y_min,lower_height),wall,.035)
    box(name+'_LEFT_FRAME_ABOVE',(-W/2,(opening_y_min+opening_y_max)/2,opening_z_max+upper_height/2),
        (.22,opening_y_max-opening_y_min,upper_height),wall,.035)
    box(name+'_RIGHT_FRAME',(W/2,0,c),(.22,D,H),WHITE,.05)
    box(name+'_STAIR_DIVIDER',(W/2-1.05,.30,c),(.09,2.30,H-.12),WHITE,.025)
    stair_rise=(H-.28)/9
    for s in range(9):
        # A shallow depth progression keeps the flight front-facing in the
        # angled camera instead of sliding dramatically sideways.
        sx=W/2-.54; sy=-.22+s*.035; sz=f+.10+s*stair_rise
        box(f'{name}_STAIR_{s}',(sx,sy,sz),(.92,.36,.12),wall,.025)
        box(f'{name}_STAIR_RISER_{s}',(sx,sy+.16,sz+stair_rise/2),(.92,.055,stair_rise),wall,.012)
    pendant(name,c)
    # Side window only, recessed into the left side.
    # Sit the pane on the interior face of the left side wall.  The angled
    # front camera can then see it as a true side window rather than edge-on.
    wx=-W/2+.13
    box(name+'_SIDE_WINDOW_GLASS',(wx,-.15,c+.05),(.04,1.0,1.0),GLASS,.008)
    for yy in (-.68,.38): box(name+'_WINDOW_EDGE',(wx-.03,yy,c+.05),(.08,.055,1.12),WHITE,.012)
    for zz in (c-.50,c+.55): box(name+'_WINDOW_EDGE',(wx-.03,-.15,zz),(.08,1.10,.055),WHITE,.012)
    box(name+'_WINDOW_MULLION',(wx-.06,-.15,c+.05),(.07,.045,1.0),WHITE,.01)

# Basement workshop.
z=BASE
box('BASEMENT_RUG',(-.70,-.48,z+.12),(2.7,1.15,.035),CONCRETE,.03)
# Broad workshop bench with metal legs and drawers.
box('BASEMENT_WORKBENCH_TOP',(-1.50,-.02,z+.68),(2.05,.62,.11),LIGHT_OAK,.045)
for dx in (-.87,.87):
    box(f'BASEMENT_BENCH_LEG_{dx}',(-1.50+dx,.03,z+.34),(.09,.46,.64),METAL,.02)
box('BASEMENT_DRAWER_UNIT',(-.90,.07,z+.36),(.58,.48,.58),DARK_WOOD,.045)
for row in range(3):
    box(f'BASEMENT_DRAWER_{row}',(-.90,-.19,z+.20+row*.18),(.44,.035,.13),LIGHT_OAK,.012)
    cyl(f'BASEMENT_DRAWER_HANDLE_{row}',(-.90,-.225,z+.20+row*.18),.018,.10,METAL,14,rot=(math.pi/2,0,0))

# Round workshop stool in front of the bench.
cyl('BASEMENT_STOOL_SEAT',(-1.62,-.72,z+.38),.28,.13,OAK,28)
cyl('BASEMENT_STOOL_POST',(-1.62,-.72,z+.20),.045,.34,METAL,18)
for angle in (0,120,240):
    px=-1.62+.20*math.cos(math.radians(angle)); py=-.72+.20*math.sin(math.radians(angle))
    box(f'BASEMENT_STOOL_FOOT_{angle}',(px,py,z+.045),(.08,.08,.09),METAL,.015)

# Articulated task lamp, angled over the work surface.
cyl('BASEMENT_TASK_LAMP_BASE',(-2.22,-.16,z+.76),.13,.055,METAL,24)
beam('BASEMENT_TASK_LAMP_ARM_A',(-2.22,-.16,z+.79),(-2.08,-.12,z+1.13),.035,.035,METAL)
beam('BASEMENT_TASK_LAMP_ARM_B',(-2.08,-.12,z+1.13),(-1.82,-.10,z+.98),.035,.035,METAL)
basement_task_shade=cone('BASEMENT_TASK_LAMP_SHADE',(-1.76,-.10,z+.94),.14,.075,.22,MUSTARD,rot=(0,math.radians(-52),0))
hover_accent('BASEMENT','BASEMENT_TASK_LAMP',(-1.70,-.18,z+.91),basement_task_shade,115.0,1.35)

# Corkboard filled with varied pinned sketches and notes.
box('BASEMENT_TOOLBOARD',(-1.30,D/2-.13,z+1.25),(1.48,.06,.68),LIGHT_OAK,.018)
note_colors=(PAPER,PINK,BLUE,YELLOW,SAGE)
note_layout=[(-.54,.18,.18,.18),(-.25,.17,.16,.23),(.02,.20,.18,.17),(.31,.16,.15,.22),(.55,.18,.17,.18),
             (-.46,-.14,.16,.20),(-.15,-.12,.21,.16),(.18,-.15,.16,.21),(.48,-.13,.20,.16)]
for j,(dx,dz,nw,nh) in enumerate(note_layout):
    box(f'BASEMENT_NOTE_{j}',(-1.30+dx,D/2-.205,z+1.25+dz),(nw,.025,nh),note_colors[j%len(note_colors)],.008)
    cyl(f'BASEMENT_PIN_{j}',(-1.30+dx,D/2-.225,z+1.25+dz+nh*.34),.014,.025,PINK,10,rot=(math.pi/2,0,0))

# Small objects on the bench: notebook, mug, tool box and plant.
box('BASEMENT_NOTEBOOK',(-1.40,-.34,z+.76),(.38,.24,.035),PAPER,.012,rot=(0,0,math.radians(-7)))
cyl('BASEMENT_MUG',(-.62,-.28,z+.82),.07,.13,PAPER,24)
box('BASEMENT_TOOLBOX',(-1.02,-.27,z+.82),(.34,.20,.16),CHARCOAL,.03)
# Keep the pot fully supported by the right edge of the workbench.
plant('BASEMENT_BENCH_PLANT',-.58,-.02,z+.74,.38,'succulent')

bookshelf('BASEMENT_STORAGE',1.55,.08,z,.72,1.30,books=False)
# Workshop storage placed directly on the shelf surfaces and inside the frame.
storage_levels=[z+.06+row*(1.30-.08)/4 for row in range(4)]
for j,(bx,bmat) in enumerate([(1.40,DARK_WOOD),(1.68,LIGHT_OAK)]):
    box(f'BASEMENT_STORAGE_BOTTOM_BIN_{j}',(bx,.02,storage_levels[0]+.13),(.22,.19,.20),bmat,.025)
box('BASEMENT_STORAGE_TOOL_CASE',(1.55,.01,storage_levels[1]+.12),(.46,.20,.18),CHARCOAL,.025)
for j,(bx,bmat,bh) in enumerate([(1.37,PAPER,.22),(1.47,BLUE,.25),(1.57,MUSTARD,.20),(1.67,SAGE,.24)]):
    box(f'BASEMENT_STORAGE_BINDER_{j}',(bx,-.01,storage_levels[2]+.03+bh/2),(.065,.17,bh),bmat,.008)
for j,(bx,bmat) in enumerate([(1.42,OAK),(1.56,PAPER),(1.69,CONCRETE)]):
    cyl(f'BASEMENT_STORAGE_JAR_{j}',(bx,.00,storage_levels[3]+.12),.065,.18,bmat,20)
box('BASEMENT_MACHINE',(2.38,.05,z+.48),(.58,.48,.90),PAPER,.06)
cyl('BASEMENT_GAUGE',(2.38,-.205,z+.62),.11,.035,METAL,32,rot=(math.pi/2,0,0))
plant('BASEMENT_PLANT',2.65,.15,z,.72,'snake')
statement_sign('BASEMENT_SIGN',.38,z+1.15,.90,.82,
               ('experiment','fail','learn','repeat'))

# Welcome entry.
z=BASE+H
cyl('WELCOME_COAT_STAND',(-1.35,.02,z+.70),.045,1.30,OAK,20)
cyl('WELCOME_COAT_STAND_BASE',(-1.35,.02,z+.055),.22,.085,OAK,28)
for a in (0,120,240):
    foot_x=-1.35+.18*math.cos(math.radians(a)); foot_y=.02+.18*math.sin(math.radians(a))
    box(f'WELCOME_COAT_STAND_FOOT_{a}',(foot_x,foot_y,z+.035),(.22,.055,.055),OAK,.015,
        rot=(0,0,math.radians(a)))
for a in (-55,0,55):
    arm=beam('WELCOME_HOOK',( -1.35,.02,z+1.23),(-1.35+.24*math.sin(math.radians(a)),.02,z+1.23+.16*math.cos(math.radians(a))),.04,.04,OAK)
# A visible wooden hanger connects the garment directly to the stand hook.
beam('WELCOME_GARMENT_HANGER_L',(-1.35,-.075,z+1.235),(-1.53,-.075,z+1.12),.025,.035,LIGHT_OAK)
beam('WELCOME_GARMENT_HANGER_R',(-1.35,-.075,z+1.235),(-1.07,-.075,z+1.12),.025,.035,LIGHT_OAK)
beam('WELCOME_GARMENT_HANGER_BAR',(-1.53,-.075,z+1.12),(-1.07,-.075,z+1.12),.020,.030,LIGHT_OAK)
# Soft connected coat with shoulder, collar, body and sleeve.
box('WELCOME_COAT_SHOULDER',(-1.28,-.09,z+1.105),(.48,.15,.17),PURPLE,.075,rot=(0,0,math.radians(-3)))
box('WELCOME_COAT_BODY',(-1.25,-.09,z+.87),(.36,.15,.52),PURPLE,.09,rot=(0,0,math.radians(-3)))
box('WELCOME_COAT_COLLAR',(-1.30,-.10,z+1.19),(.16,.16,.12),LAVENDER,.045)
box('WELCOME_COAT_SLEEVE',(-1.50,-.10,z+.88),(.13,.14,.43),PURPLE,.06,rot=(0,0,math.radians(-13)))
box('WELCOME_ENTRY_BASKET',(1.80,.02,z+.20),(.42,.32,.30),LIGHT_OAK,.06)
for bx in (1.66,1.80,1.94):
    box(f'WELCOME_BASKET_SLAT_{bx}',(bx,-.16,z+.20),(.035,.025,.22),OAK,.006)

# Pale rug grounds the seating area like the long runner in the reference.
box('WELCOME_RUG',(-.10,-.45,z+.115),(2.15,1.02,.035),PAPER,.035)
cozy_sofa('WELCOME_SOFA',-.10,-.12,z,LAVENDER)
framed_art('WELCOME_ART',-.10,D/2-.14,z+1.25,.55,.60,PINK)
welcome_art_text=text_obj('WELCOME_ART_TEXT','welcome\nhome',(-.10,D/2-.205,z+1.25),.085,CHARCOAL)
welcome_art_text.data.space_line=1.08
cyl('WELCOME_MIRROR',(1.05,D/2-.18,z+1.20),.31,.055,LIGHT_OAK,48,rot=(math.pi/2,0,0))
sph('WELCOME_MIRROR_GLASS',(1.05,D/2-.215,z+1.20),(.255,.03,.255),MIRROR)

# Slim entry console beneath the mirror, with drawers, lamp, books and ceramics.
box('WELCOME_CONSOLE_TOP',(1.03,.18,z+.63),(1.18,.36,.08),LIGHT_OAK,.035)
box('WELCOME_CONSOLE_BODY',(1.03,.25,z+.40),(1.10,.30,.39),OAK,.035)
for dx in (-.27,.27):
    box(f'WELCOME_CONSOLE_DOOR_{dx}',(1.03+dx,.07,z+.40),(.45,.025,.28),LIGHT_OAK,.015)
    cyl(f'WELCOME_CONSOLE_KNOB_{dx}',(1.03+dx,.045,z+.40),.018,.025,METAL,14,rot=(math.pi/2,0,0))
for dx in (-.44,.44):
    box(f'WELCOME_CONSOLE_LEG_{dx}',(1.03+dx,.22,z+.17),(.055,.22,.34),DARK_WOOD,.012)
cyl('WELCOME_TABLE_LAMP_BASE',(.68,-.01,z+.71),.09,.045,OAK,24)
cyl('WELCOME_TABLE_LAMP_STEM',(.68,-.01,z+.84),.016,.24,METAL,14)
welcome_lamp_shade=cone('WELCOME_TABLE_LAMP_SHADE',(.68,-.01,z+.98),.13,.075,.18,PAPER)
hover_accent('WELCOME','WELCOME_TABLE_LAMP',(.68,-.08,z+.91),welcome_lamp_shade,110.0,1.30)
for j,(bw,bmat) in enumerate([(.24,PAPER),(.21,PINK),(.23,BLUE)]):
    box(f'WELCOME_CONSOLE_BOOK_{j}',(1.12,-.02,z+.69+j*.03),(bw,.18,.025),bmat,.006)
cyl('WELCOME_CONSOLE_VASE',(1.42,-.01,z+.73),.055,.15,SAGE,22)
plant('WELCOME_CONSOLE_PLANT',1.42,-.01,z+.78,.25,'succulent')
# Floor plant moved into the open gap left of the coat stand; the basket now
# occupies its former right-side position beside the console.
plant('WELCOME_PLANT',-1.84,.05,z,.72,'broad')
bookshelf('WELCOME_BOOKCASE',2.45,.10,z,.72,1.35)

# With the purple door removed, spread the complete entry arrangement into
# the newly available left-side space instead of bunching it on the right.
welcome_left_shift_prefixes=(
    'WELCOME_COAT','WELCOME_HOOK','WELCOME_GARMENT','WELCOME_RUG','WELCOME_SOFA',
    'WELCOME_ART','WELCOME_MIRROR','WELCOME_CONSOLE','WELCOME_PLANT',
    'WELCOME_BOOKCASE','WELCOME_ENTRY_BASKET','WELCOME_BASKET'
)
for welcome_object in bpy.data.objects:
    if welcome_object.name.startswith(welcome_left_shift_prefixes):
        welcome_object.location.x-=.55

# Fine spacing after the group shift: sofa further left, console clearly to
# its right with air between them, bookcase separated from the console, and
# the basket occupying the newly empty far-left corner.
for welcome_object in bpy.data.objects:
    if welcome_object.name.startswith(('WELCOME_SOFA','WELCOME_RUG','WELCOME_ART')):
        welcome_object.location.x-=.15
    elif welcome_object.name.startswith(('WELCOME_CONSOLE','WELCOME_MIRROR')):
        welcome_object.location.x+=.47
    elif welcome_object.name.startswith('WELCOME_BOOKCASE'):
        welcome_object.location.x+=.15
    elif welcome_object.name.startswith(('WELCOME_ENTRY_BASKET','WELCOME_BASKET')):
        welcome_object.location.x-=4.20

# Playroom.
z=BASE+2*H
sph('PLAYROOM_BEANBAG',(-2.25,-.15,z+.42),(.66,.52,.46),PINK)
sph('PLAYROOM_BEANBAG_DIMPLE',(-2.25,-.34,z+.67),(.25,.12,.12),CORAL)
for row in range(3):
    box(f'PLAYROOM_TOY_SHELF_{row}',(-1.15,D/2-.16,z+.62+row*.34),(1.05,.28,.07),LIGHT_OAK,.02)
    for j in range(4): sph(f'PLAYROOM_TOY_{row}_{j}',(-1.50+j*.25,D/2-.34,z+.73+row*.34),(.07,.06,.09),(PINK,BLUE,YELLOW,GREEN2)[j])
box('PLAYROOM_TABLE',(-.40,-.45,z+.33),(1.30,.62,.10),LIGHT_OAK,.08)
for dx in (-.48,.48): box('PLAYROOM_TABLE_LEG',(-.40+dx,-.45,z+.16),(.08,.40,.28),OAK,.025)
box('ARCADE_BODY',(1.22,.02,z+.66),(.62,.58,1.25),CHARCOAL,.08)
box('ARCADE_TOP',(1.22,-.08,z+1.28),(.62,.62,.26),CORAL,.055)
box('ARCADE_SCREEN',(1.22,-.33,z+.98),(.44,.035,.35),SCREEN,.035)
box('ARCADE_CONTROL',(1.22,-.38,z+.70),(.50,.23,.10),DARK_WOOD,.025,rot=(math.radians(12),0,0))
bookshelf('PLAYROOM_BOOKCASE',2.05,.10,z,.72,1.35)
statement_sign('PLAYROOM_SIGN',.28,z+1.18,.70,.70,
               ('play','build','repeat'),PLAY_SIGN,WHITE_TEXT,PINK)
hover_accent('PLAYROOM','PLAYROOM_SIGN',(.28,-.10,z+1.18),bpy.data.objects.get('PLAYROOM_SIGN_CARD'),55.0,1.05)
plant('PLAYROOM_PLANT',-3.10,.15,z,.78,'fern')

# Office — airy trestle desk and a mustard task chair.
z=BASE+3*H
box('OFFICE_RUG',(-.85,-.48,z+.12),(2.65,1.00,.035),PAPER,.035)

# Left-corner vignette beside the real side window.
box('OFFICE_CORNER_CABINET',(-3.08,.10,z+.31),(.43,.38,.58),SAGE,.045)
for row in range(3):
    box(f'OFFICE_CORNER_DRAWER_{row}',(-3.08,-.11,z+.17+row*.17),(.32,.035,.12),LIGHT_OAK,.012)
plant('OFFICE_CORNER_PLANT',-3.08,.07,z+.60,.42,'succulent')
box('OFFICE_FLOATING_SHELF',(-2.92,D/2-.17,z+1.20),(.78,.25,.065),LIGHT_OAK,.018)
box('OFFICE_SHELF_BOOK_A',(-3.12,D/2-.34,z+1.33),(.09,.12,.20),PINK,.008)
box('OFFICE_SHELF_BOOK_B',(-3.01,D/2-.34,z+1.30),(.08,.12,.15),PAPER,.008)
cyl('OFFICE_SHELF_VASE',(-2.72,D/2-.34,z+1.31),.065,.19,OAK,22)

box('OFFICE_DESK_TOP',(-1.62,-.02,z+.68),(1.70,.55,.09),LIGHT_OAK,.04)
box('OFFICE_TRESTLE_L',(-2.24,.00,z+.34),(.10,.42,.64),OAK,.025,rot=(0,math.radians(-8),0))
box('OFFICE_TRESTLE_R',(-1.00,.00,z+.34),(.10,.42,.64),OAK,.025,rot=(0,math.radians(8),0))
box('OFFICE_MONITOR',(-1.62,.10,z+1.08),(.70,.09,.46),SCREEN,.05)
box('OFFICE_SCREEN',(-1.62,.045,z+1.08),(.58,.018,.34),BLUE,.015)
box('OFFICE_KEYBOARD',(-1.62,-.28,z+.75),(.48,.18,.035),METAL,.015)
box('OFFICE_CHAIR_SEAT',(-1.62,-.68,z+.43),(.56,.48,.16),YELLOW,.10)
box('OFFICE_CHAIR_BACK',(-1.62,-.84,z+.75),(.52,.14,.58),YELLOW,.12)
cyl('OFFICE_CHAIR_POST',(-1.62,-.68,z+.21),.045,.36,METAL,20)

# Reference desk styling: small lamp, mug, stationery and stacked books.
cyl('OFFICE_TABLE_LAMP_BASE',(-2.25,-.17,z+.76),.105,.045,OAK,24)
cyl('OFFICE_TABLE_LAMP_STEM',(-2.25,-.17,z+.91),.018,.28,METAL,14)
office_lamp_shade=cone('OFFICE_TABLE_LAMP_SHADE',(-2.25,-.17,z+1.07),.15,.085,.22,PAPER)
hover_accent('OFFICE','OFFICE_TABLE_LAMP',(-2.25,-.24,z+.99),office_lamp_shade,110.0,1.30)
cyl('OFFICE_MUG',(-1.02,-.23,z+.79),.065,.12,PAPER,24)
cyl('OFFICE_PENCIL_CUP',(-1.23,-.22,z+.80),.055,.13,OAK,20)
for j,px in enumerate((-1.25,-1.22,-1.19)):
    cyl(f'OFFICE_PENCIL_{j}',(px,-.22,z+.92),.008,.23,(PINK,BLUE,YELLOW)[j],10)
for j,(bw,bmat) in enumerate([(.30,PAPER),(.26,PINK),(.28,BLUE)]):
    box(f'OFFICE_BOOK_STACK_{j}',(-1.83,-.25,z+.755+j*.035),(bw,.22,.028),bmat,.006)

framed_art('OFFICE_PINBOARD',-.35,D/2-.14,z+1.22,1.00,.65,LIGHT_OAK)
for j in range(9): box(f'OFFICE_NOTE_{j}',(-.70+(j%3)*.28,D/2-.20,z+1.43-(j//3)*.19),(.15,.025,.13),(PAPER,PINK,BLUE)[j%3],.01)
statement_sign('OFFICE_SIGN',.65,z+1.13,.76,.76,
               ('interfaces','are','conversations'))
bookshelf('OFFICE_BOOKCASE',1.85,.10,z,.92,1.40)
# Two fabric storage bins break up the books like the reference shelving.
box('OFFICE_STORAGE_BIN_A',(1.62,-.08,z+.22),(.34,.22,.22),PAPER,.035)
box('OFFICE_STORAGE_BIN_B',(2.08,-.08,z+.22),(.34,.22,.22),LIGHT_OAK,.035)

# Small cabinet below the statement poster, with decor on top.
box('OFFICE_SIDE_TABLE',(.60,.05,z+.34),(.72,.40,.42),LIGHT_OAK,.045)
box('OFFICE_SIDE_DRAWER',(.60,-.18,z+.39),(.55,.035,.16),OAK,.012)
cyl('OFFICE_SIDE_VASE',(.43,-.04,z+.61),.055,.16,PAPER,22)
sph('OFFICE_SIDE_DECOR',(.76,-.04,z+.60),(.07,.05,.09),GREEN2)
# The office tree now occupies the deliberate gap between monitor and sign.
plant('OFFICE_PLANT',-.30,.12,z,.74,'tree')

# Studio — wider creative workstation with drawers and a green swivel chair.
z=BASE+4*H
box('STUDIO_WORKTOP',(-1.38,-.02,z+.68),(2.05,.62,.10),LIGHT_OAK,.045)
box('STUDIO_DRAWER_UNIT',(-2.12,.06,z+.39),(.52,.50,.58),SAGE,.055)
for row in range(3):
    box(f'STUDIO_DRAWER_{row}',(-2.12,-.205,z+.23+row*.18),(.38,.035,.13),LIGHT_OAK,.015)
box('STUDIO_LEG',(-.48,.04,z+.34),(.10,.46,.64),OAK,.025)
box('STUDIO_MONITOR',(-1.25,.10,z+1.09),(.78,.10,.50),SCREEN,.055)
box('STUDIO_SCREEN',(-1.25,.04,z+1.09),(.65,.018,.37),BLUE,.015)
box('STUDIO_KEYBOARD',(-1.28,-.29,z+.75),(.55,.19,.035),METAL,.015)
sph('STUDIO_CHAIR_BACK',(-1.25,-.83,z+.76),(.35,.10,.40),SAGE)
box('STUDIO_CHAIR_SEAT',(-1.25,-.67,z+.43),(.58,.50,.17),SAGE,.12)
cyl('STUDIO_CHAIR_POST',(-1.25,-.67,z+.21),.05,.37,METAL,20)
# Creative tools and stacked papers give the workstation the lived-in feel
# of the reference instead of repeating the sparse yellow office desk.
cyl('STUDIO_DESK_LAMP_BASE',(-2.00,-.19,z+.76),.095,.045,OAK,24)
cyl('STUDIO_DESK_LAMP_STEM',(-2.00,-.19,z+.91),.016,.28,METAL,14)
studio_lamp_shade=cone('STUDIO_DESK_LAMP_SHADE',(-2.00,-.19,z+1.06),.14,.075,.20,PAPER)
hover_accent('STUDIO','STUDIO_DESK_LAMP',(-2.00,-.25,z+.98),studio_lamp_shade,105.0,1.28)
cyl('STUDIO_PENCIL_CUP',(-.61,-.20,z+.80),.055,.13,SAGE,20)
for j,px in enumerate((-.64,-.61,-.58)):
    cyl(f'STUDIO_PENCIL_{j}',(px,-.20,z+.92),.008,.23,(PINK,BLUE,YELLOW)[j],10)
for j,(bw,bmat) in enumerate([(.32,PAPER),(.28,BLUE),(.30,PINK)]):
    box(f'STUDIO_PAPER_STACK_{j}',(-1.68,-.25,z+.755+j*.032),(bw,.21,.025),bmat,.006)
for row in range(2):
    for col in range(5):
        framed_art(f'STUDIO_ART_{row}_{col}',-.95+col*.34,D/2-.14,z+1.42-row*.35,.20,.26,(PAPER,PINK,BLUE,YELLOW,SAGE)[(row+col)%5])
bookshelf('STUDIO_BOOKCASE',1.85,.10,z,1.05,1.42)
statement_sign('STUDIO_SIGN',.62,z+.94,.76,.70,
               ('design','with','purpose'))
plant('STUDIO_PLANT',-2.75,.10,z,.62,'succulent')
plant('STUDIO_TALL_PLANT',.95,.15,z,.82,'broad')

# Layered botanical corner beside the side window, matching the reference.
box('STUDIO_LEFT_SHELF_LOW',(-2.78,D/2-.18,z+.91),(.82,.27,.065),LIGHT_OAK,.018)
box('STUDIO_LEFT_SHELF_HIGH',(-2.78,D/2-.18,z+1.29),(.82,.27,.065),LIGHT_OAK,.018)
for sx in (-3.08,-2.48):
    box(f'STUDIO_SHELF_BRACKET_{sx}',(sx,D/2-.08,z+1.10),(.045,.13,.35),OAK,.008)
plant('STUDIO_SHELF_FERN',-2.98,D/2-.38,z+.94,.30,'fern')
plant('STUDIO_SHELF_SNAKE',-2.58,D/2-.38,z+1.32,.32,'snake')
box('STUDIO_SHELF_BOOK_A',(-2.82,D/2-.36,z+1.43),(.08,.12,.20),PINK,.008)
box('STUDIO_SHELF_BOOK_B',(-2.72,D/2-.36,z+1.40),(.08,.12,.15),PAPER,.008)

# Small open-frame reading chair from the right side of the green room.
box('STUDIO_READING_SEAT',(.77,-.62,z+.39),(.52,.50,.15),SAGE,.09)
box('STUDIO_READING_BACK',(.77,-.43,z+.70),(.51,.13,.52),SAGE,.10,rot=(math.radians(-8),0,0))
for dx in (-.28,.28):
    cyl(f'STUDIO_READING_FRONT_LEG_{dx}',(.77+dx,-.78,z+.19),.025,.38,OAK,14)
    cyl(f'STUDIO_READING_BACK_LEG_{dx}',(.77+dx,-.43,z+.19),.025,.38,OAK,14)
    cyl(f'STUDIO_READING_ARM_{dx}',(.77+dx,-.60,z+.59),.025,.48,OAK,14,rot=(math.pi/2,0,0))

# Attic/rooftop room and balcony.
top=BASE+5*H
box('ROOFTOP_FLOOR',(0,0,top),(W+.35,D+.30,.22),WHITE,.055)
# Solid attic supports meet the eaves instead of leaving the roof suspended.
box('ROOFTOP_BACK',(0,D/2,top+.675),(W,.16,1.35),CREAM,.02)
box('ROOFTOP_LEFT_POST',(-W/2,0,top+.675),(.22,D,1.35),WHITE,.045)
box('ROOFTOP_RIGHT_POST',((W/2),0,top+.675),(.22,D,1.35),WHITE,.045)
pendant('ROOFTOP',top+.85)
box('ROOFTOP_DOOR',(2.25,D/2-.18,top+.70),(.72,.10,1.34),PURPLE,.055)
box('ROOFTOP_DOOR_PANEL',(2.25,D/2-.25,top+.70),(.50,.035,1.08),LAVENDER,.035)
box('ROOFTOP_ARMCHAIR',(-2.55,-.10,top+.42),(.78,.72,.30),BLUE,.13)
box('ROOFTOP_ARMCHAIR_BACK',(-2.55,.13,top+.78),(.78,.22,.70),BLUE,.13)
for dx in (-.42,.42): box('ROOFTOP_ARM',(-2.55+dx,-.08,top+.65),(.18,.65,.50),BLUE,.10)
desk('ROOFTOP_DESK',-.80,.05,top,LAVENDER)
# Small warm desk lamp, linked to the rooftop hover group.
cyl('ROOFTOP_DESK_LAMP_BASE',(-1.30,-.20,top+.76),.09,.045,OAK,24)
cyl('ROOFTOP_DESK_LAMP_STEM',(-1.30,-.20,top+.89),.016,.24,METAL,14)
rooftop_lamp_shade=cone('ROOFTOP_DESK_LAMP_SHADE',(-1.30,-.20,top+1.03),.13,.075,.18,PAPER)
hover_accent('ROOFTOP','ROOFTOP_DESK_LAMP',(-1.30,-.27,top+.96),rooftop_lamp_shade,105.0,1.28)
bookshelf('ROOFTOP_BOOKCASE',1.28,.12,top,.72,1.28)
plant('ROOFTOP_PLANT',2.90,.05,top,.95,'snake')
statement_sign('ROOFTOP_SIGN',.30,top+1.18,.78,.82,
               ("let's",'create','beautiful','things'))

# Balcony railing.
# Keep the railing closest to the camera so it remains in front of the
# balcony furniture and plant, as in the reference cutaway.
rail_y=-D/2-.58
for x in (-W/2+.18,-2.5,-1.25,0,1.25,2.5,W/2-.18):
    box('BALCONY_POST',(x,rail_y,top+.48),(.035,.035,.92),METAL,.008)
box('BALCONY_RAIL',(0,rail_y,top+.94),(W-.35,.04,.045),METAL,.008)

# Connected gable roof with warm timber inner trim and physical blue tiles.
roof_half=W/2+.22; roof_base=top+1.35; ridge=top+2.68; roof_depth=D/2+.22

# Cream triangular back gable closes the empty grey gap under the ridge.
gable_mesh=bpy.data.meshes.new('ROOFTOP_GABLE_WALL_MESH')
gable_mesh.from_pydata([
    (-roof_half,D/2-.09,roof_base),
    ( roof_half,D/2-.09,roof_base),
    (0,D/2-.09,ridge)
],[],[(0,1,2)])
gable_mesh.update()
gable_wall=bpy.data.objects.new('ROOFTOP_GABLE_WALL',gable_mesh)
bpy.context.collection.objects.link(gable_wall); gable_wall.data.materials.append(CREAM)
gable_solid=gable_wall.modifiers.new('gable thickness','SOLIDIFY'); gable_solid.thickness=.15
gable_bevel=gable_wall.modifiers.new('soft gable edge','BEVEL'); gable_bevel.width=.025; gable_bevel.segments=3

# Full-depth sloped roof slabs attach to the gable and side posts.
roof_rise=ridge-roof_base
roof_slope=math.sqrt(roof_half**2+roof_rise**2)
roof_angle=math.atan2(roof_rise,roof_half)
roof_y_front=-roof_depth-.10; roof_y_back=roof_depth+.28
roof_panel_depth=roof_y_back-roof_y_front
roof_panel_y=(roof_y_front+roof_y_back)/2
roof_mid_z=(roof_base+ridge)/2
box('ROOF_SLAB_LEFT',(-roof_half/2,roof_panel_y,roof_mid_z),(roof_slope+.14,roof_panel_depth,.18),WHITE,.035,rot=(0,-roof_angle,0))
box('ROOF_SLAB_RIGHT',(roof_half/2,roof_panel_y,roof_mid_z),(roof_slope+.14,roof_panel_depth,.18),WHITE,.035,rot=(0,roof_angle,0))

beam('ROOF_LEFT',(-roof_half,-roof_depth,roof_base),(0,-roof_depth,ridge),.20,.22,WHITE)
beam('ROOF_RIGHT',(0,-roof_depth,ridge),(roof_half,-roof_depth,roof_base),.20,.22,WHITE)
beam('ROOF_TRIM_LEFT',(-roof_half+.10,-roof_depth-.13,roof_base-.07),(0,-roof_depth-.13,ridge-.07),.10,.10,LIGHT_OAK)
beam('ROOF_TRIM_RIGHT',(0,-roof_depth-.13,ridge-.07),(roof_half-.10,-roof_depth-.13,roof_base-.07),.10,.10,LIGHT_OAK)
beam('ROOF_BLUE_LEFT',(-roof_half,-roof_depth-.20,roof_base+.10),(0,-roof_depth-.20,ridge+.10),.07,.08,ROOF)
beam('ROOF_BLUE_RIGHT',(0,-roof_depth-.20,ridge+.10),(roof_half,-roof_depth-.20,roof_base+.10),.07,.08,ROOF)

# Overlapping blue-grey tegel: separate beveled tiles create a real pattern
# and remain fully packed in the .blend with no external image dependency.
tile_rows=7; tile_columns=8
tile_step_y=roof_panel_depth/tile_columns
tile_len=roof_slope/tile_rows+.075
for side in (-1,1):
    tile_rotation=-roof_angle if side==-1 else roof_angle
    normal_x=side*math.sin(roof_angle)
    for row in range(tile_rows):
        t=(row+.5)/tile_rows
        tile_x=side*roof_half*(1-t)+normal_x*.125
        tile_z=roof_base+roof_rise*t+math.cos(roof_angle)*.125
        for column in range(tile_columns):
            tile_y=roof_y_front+(column+.5)*tile_step_y
            tile_mat=(ROOF_TILE_LIGHT,ROOF,ROOF_TILE_DARK)[(row+column+(0 if side==-1 else 1))%3]
            box(f'ROOF_TILE_{side}_{row}_{column}',(tile_x,tile_y,tile_z),
                (tile_len,tile_step_y+.035,.055),tile_mat,.026,rot=(0,tile_rotation,0))

# Rounded overlapping ridge caps finish the tiled roof line.
for column in range(tile_columns):
    cap_y=roof_y_front+(column+.5)*tile_step_y
    cyl(f'ROOF_RIDGE_CAP_{column}',(0,cap_y,ridge+.17),.13,tile_step_y+.055,
        ROOF_TILE_DARK,24,rot=(math.pi/2,0,0))

box('CHIMNEY',(2.55,.35,top+2.12),(.62,.62,1.55),WHITE,.055)
cyl('CHIMNEY_CAP',(2.55,.35,top+2.92),.38,.10,LIGHT_OAK,28)

# Delicate terrace tree at left.  Its depth sits in front of the roof beams
# but behind the balcony rail, preventing the foliage from disappearing.
tree_y=-D/2-.40
box('TREE_PLANTER',(-3.30,tree_y,top+.22),(.72,.48,.42),LIGHT_OAK,.045)
box('TREE_PLANTER_INSET',(-3.30,tree_y-.255,top+.23),(.56,.025,.28),OAK,.012)
cyl('TREE_PLANTER_SOIL',(-3.30,tree_y,top+.44),.28,.035,SOIL,28)
cyl('TREE_TRUNK',(-3.30,tree_y,top+1.16),.055,1.50,OAK,18)
for j,(dx,dz) in enumerate([(-.25,1.25),(.15,1.40),(-.05,1.72),(.28,1.86),(-.32,1.95)]):
    beam(f'TREE_BRANCH_{j}',(-3.30,tree_y,top+1.02),(-3.30+dx,tree_y,top+dz),.025,.025,OAK)
    for k in range(4): sph(f'TREE_LEAF_{j}_{k}',(-3.30+dx+(k-1.5)*.08,tree_y,top+dz+(k%2)*.08),(.07,.04,.12),GREEN2 if (j+k)%2 else GREEN)

# Foundation and neutral floor/background.
box('FOUNDATION',(0,.05,BASE-.30),(W+.50,D+.35,.45),WHITE,.07)
box('GROUND',(0,2,-.58),(18,14,.18),WHITE,.05)

# Camera and lighting.
# Subtle front three-quarter view, matching the reference's visible left
# interior side walls while preserving the straight architectural elevation.
bpy.ops.object.camera_add(location=(6.5,-27,6.25))
cam=bpy.context.object; cam.name='REFERENCE_FRONT_CAMERA'; cam.data.type='ORTHO'; cam.data.ortho_scale=14.6
target=Vector((0,0,5.55)); cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler(); bpy.context.scene.camera=cam

def area(name,loc,energy,size,color):
    bpy.ops.object.light_add(type='AREA',location=loc)
    o=bpy.context.object; o.name=name; o.data.energy=energy; o.data.shape='DISK'; o.data.size=size; o.data.color=color
    o.rotation_euler=(target-o.location).to_track_quat('-Z','Y').to_euler()

area('KEY_SOFT',(0,-10,10),700,7,(1,.82,.68))
area('FILL_SOFT',(-7,-6,6),260,6,(.70,.82,1))
area('TOP_SOFT',(5,-4,12),180,5,(1,.75,.55))
world=bpy.context.scene.world; world.use_nodes=True
world.node_tree.nodes['Background'].inputs['Color'].default_value=(.88,.90,.91,1)
world.node_tree.nodes['Background'].inputs['Strength'].default_value=.30

scene=bpy.context.scene
scene.render.engine='BLENDER_EEVEE'
scene.render.resolution_x=1024; scene.render.resolution_y=1536; scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'; scene.render.film_transparent=False
scene.view_settings.view_transform='AgX'
scene.render.filepath='/Users/filippakarlsson/Desktop/filippa_house_reference_rebuilt.png'
blend_path='/Users/filippakarlsson/Desktop/filippa_house_reference_rebuilt.blend'
scene['HOVER']='Use installed House Hover add-on. Lights are named *_HOVER_LIGHT.'
bpy.ops.wm.save_as_mainfile(filepath=blend_path)
bpy.ops.render.render(write_still=True)
print('CREATED',blend_path)
print('RENDER',scene.render.filepath)
