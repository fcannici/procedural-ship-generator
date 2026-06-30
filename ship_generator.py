import bpy
import bmesh
import math
import mathutils
import random

def create_grid(bm, x_min, x_max, y_min, y_max, z, grid_size=25.4, depth=0.5, width=1.0):
    # This function will sculpt the 1x1 grid lines on the floor
    pass


def create_deck_planks(bm_deck, start_y, end_y, w2_bot, w2_top, z, thickness, scale_front, scale_back, section_type, l2, has_grid=False):
    deck_y_segments = max(1, int((end_y - start_y) / 25.4))
    seg_len = (end_y - start_y) / deck_y_segments
    num_deck_planks = 4
    plank_gap = 0.5
    pw = (w2_top * 2) / num_deck_planks
    base_thickness = 1.0
    w2_mid = (w2_bot + w2_top) / 2.0
    
    # 1. Generate the solid continuous base
    num_base_segments = 1 if section_type == 'MID' else 12
    base_segments = []
    
    for i in range(num_base_segments + 1):
        t = i / num_base_segments
        y = start_y + (end_y - start_y) * t
        
        if section_type in ('STERN', 'BOW'):
            p_y = (y - (-l2)) / (2*l2) if l2 > 0 else 0
            sc = scale_back + (scale_front - scale_back) * p_y
        else:
            sc = 1.0
            
        verts = [
            bm_deck.verts.new((-w2_bot * sc, y, z)),
            bm_deck.verts.new((w2_bot * sc, y, z)),
            bm_deck.verts.new((w2_top * sc, y, z + base_thickness)),
            bm_deck.verts.new((-w2_top * sc, y, z + base_thickness))
        ]
        base_segments.append(verts)
        
    for i in range(num_base_segments):
        v1 = base_segments[i]
        v2 = base_segments[i+1]
        if i == 0:
            bm_deck.faces.new((v1[0], v1[1], v1[2], v1[3]))
        if i == num_base_segments - 1:
            bm_deck.faces.new((v2[0], v2[3], v2[2], v2[1]))
            
        bm_deck.faces.new((v1[0], v2[0], v2[1], v1[1])) # Bottom
        bm_deck.faces.new((v1[3], v1[2], v2[2], v2[3])) # Top
        bm_deck.faces.new((v1[0], v1[3], v2[3], v2[0])) # Left
        bm_deck.faces.new((v1[1], v2[1], v2[2], v1[2])) # Right

    # 2. Generate the individual planks on top of the base
    grid_size = 25.4
    groove_width = 1.0
    plank_gap = 0.5
    
    if has_grid:
        max_idx_x = int(math.ceil(w2_top / grid_size))
        min_iy = int(math.floor(start_y / grid_size)) - 1
        max_iy = int(math.ceil(end_y / grid_size)) + 1
        
        for ix in range(-max_idx_x, max_idx_x):
            for iy in range(min_iy, max_iy):
                cx = (ix + 0.5) * grid_size
                cy = (iy + 0.5) * grid_size
                
                tx1 = cx - (grid_size/2.0) + groove_width
                tx2 = cx + (grid_size/2.0) - groove_width
                ty1 = cy - (grid_size/2.0) + groove_width
                ty2 = cy + (grid_size/2.0) - groove_width
                
                valid_ty1 = max(ty1, start_y + groove_width)
                valid_ty2 = min(ty2, end_y - groove_width)
                
                if valid_ty1 >= valid_ty2:
                    continue
                    
                p_ty1 = (valid_ty1 - (-l2)) / (2*l2) if l2 > 0 else 0
                p_ty2 = (valid_ty2 - (-l2)) / (2*l2) if l2 > 0 else 0
                
                if section_type in ('STERN', 'BOW'):
                    sc1 = scale_back + (scale_front - scale_back) * p_ty1
                    sc2 = scale_back + (scale_front - scale_back) * p_ty2
                else:
                    sc1 = 1.0
                    sc2 = 1.0
                    
                w_top_1 = w2_top * sc1
                w_top_2 = w2_top * sc2
                w_mid_1 = w2_bot * sc1
                w_mid_2 = w2_bot * sc2
                
                min_w_top = min(w_top_1, w_top_2)
                min_w_mid = min(w_mid_1, w_mid_2)
                
                valid_tx1 = max(tx1, -min_w_top + groove_width)
                valid_tx2 = min(tx2, min_w_top - groove_width)
                
                if valid_tx1 >= valid_tx2:
                    continue
                    
                num_planks = 3
                full_w = tx2 - tx1
                if full_w <= 0: continue
                pw = full_w / num_planks
                planks = []
                for p in range(num_planks):
                    px1 = tx1 + p * pw
                    px2 = tx1 + (p + 1) * pw - plank_gap
                    if px2 > px1:
                        planks.append((px1, px2))
                        
                for px1, px2 in planks:
                    p1_top_b = max(min(px1, w_top_1), -w_top_1)
                    p2_top_b = max(min(px2, w_top_1), -w_top_1)
                    p1_bot_b = max(min(px1, w_mid_1), -w_mid_1)
                    p2_bot_b = max(min(px2, w_mid_1), -w_mid_1)
                    
                    p1_top_f = max(min(px1, w_top_2), -w_top_2)
                    p2_top_f = max(min(px2, w_top_2), -w_top_2)
                    p1_bot_f = max(min(px1, w_mid_2), -w_mid_2)
                    p2_bot_f = max(min(px2, w_mid_2), -w_mid_2)
                    
                    back_valid = (p2_top_b - p1_top_b >= 0.01)
                    front_valid = (p2_top_f - p1_top_f >= 0.01)
                    
                    if not back_valid and not front_valid:
                        continue
                        
                    if back_valid and front_valid:
                        d_back = [
                            bm_deck.verts.new((p1_bot_b, valid_ty1, z + base_thickness - 0.1)),
                            bm_deck.verts.new((p2_bot_b, valid_ty1, z + base_thickness - 0.1)),
                            bm_deck.verts.new((p2_top_b, valid_ty1, z + thickness)),
                            bm_deck.verts.new((p1_top_b, valid_ty1, z + thickness))
                        ]
                        d_front = [
                            bm_deck.verts.new((p1_bot_f, valid_ty2, z + base_thickness - 0.1)),
                            bm_deck.verts.new((p2_bot_f, valid_ty2, z + base_thickness - 0.1)),
                            bm_deck.verts.new((p2_top_f, valid_ty2, z + thickness)),
                            bm_deck.verts.new((p1_top_f, valid_ty2, z + thickness))
                        ]
                        bm_deck.faces.new((d_back[0], d_back[1], d_back[2], d_back[3])) # Back
                        bm_deck.faces.new((d_front[0], d_front[3], d_front[2], d_front[1])) # Front
                        bm_deck.faces.new((d_back[0], d_back[3], d_front[3], d_front[0])) # Left
                        bm_deck.faces.new((d_back[1], d_front[1], d_front[2], d_back[2])) # Right
                        bm_deck.faces.new((d_back[3], d_back[2], d_front[2], d_front[3])) # Top
                        bm_deck.faces.new((d_back[0], d_front[0], d_front[1], d_back[1])) # Bottom
                            
                    elif back_valid and not front_valid:
                        d_back = [
                            bm_deck.verts.new((p1_bot_b, valid_ty1, z + base_thickness - 0.1)),
                            bm_deck.verts.new((p2_bot_b, valid_ty1, z + base_thickness - 0.1)),
                            bm_deck.verts.new((p2_top_b, valid_ty1, z + thickness)),
                            bm_deck.verts.new((p1_top_b, valid_ty1, z + thickness))
                        ]
                        f_bot = bm_deck.verts.new((p1_bot_f, valid_ty2, z + base_thickness - 0.1))
                        f_top = bm_deck.verts.new((p1_top_f, valid_ty2, z + thickness))
                        
                        bm_deck.faces.new((d_back[0], d_back[1], d_back[2], d_back[3])) # Back
                        bm_deck.faces.new((d_back[0], d_back[3], f_top, f_bot)) # Left
                        bm_deck.faces.new((d_back[1], f_bot, f_top, d_back[2])) # Right
                        bm_deck.faces.new((d_back[3], d_back[2], f_top)) # Top
                        bm_deck.faces.new((d_back[0], f_bot, d_back[1])) # Bottom
                        
                    elif not back_valid and front_valid:
                        d_front = [
                            bm_deck.verts.new((p1_bot_f, valid_ty2, z + base_thickness - 0.1)),
                            bm_deck.verts.new((p2_bot_f, valid_ty2, z + base_thickness - 0.1)),
                            bm_deck.verts.new((p2_top_f, valid_ty2, z + thickness)),
                            bm_deck.verts.new((p1_top_f, valid_ty2, z + thickness))
                        ]
                        b_bot = bm_deck.verts.new((p1_bot_b, valid_ty1, z + base_thickness - 0.1))
                        b_top = bm_deck.verts.new((p1_top_b, valid_ty1, z + thickness))
                        
                        bm_deck.faces.new((d_front[0], d_front[3], d_front[2], d_front[1])) # Front
                        bm_deck.faces.new((d_front[0], b_bot, b_top, d_front[3])) # Left
                        bm_deck.faces.new((d_front[1], d_front[2], b_top, b_bot)) # Right
                        bm_deck.faces.new((d_front[3], b_top, d_front[2])) # Top
                        bm_deck.faces.new((d_front[0], d_front[1], b_bot)) # Bottom
    else:
        for iy in range(deck_y_segments):
            sy1 = start_y + iy * seg_len + 0.2
            sy2 = start_y + (iy + 1) * seg_len - 0.2
            planks = []
            if iy % 2 == 0:
                for p in range(num_deck_planks):
                    px1 = -w2_top + p * pw
                    px2 = -w2_top + (p + 1) * pw - plank_gap
                    planks.append((px1, px2))
            else:
                px1 = -w2_top
                px2 = -w2_top + pw / 2 - plank_gap
                planks.append((px1, px2))
                for p in range(num_deck_planks - 1):
                    px1 = -w2_top + pw / 2 + p * pw
                    px2 = -w2_top + pw / 2 + (p + 1) * pw - plank_gap
                    planks.append((px1, px2))
                px1 = -w2_top + pw / 2 + (num_deck_planks - 1) * pw
                px2 = w2_top - plank_gap
                planks.append((px1, px2))
            for px1, px2 in planks:
                if px2 <= px1: continue
                
                p1_bot = max(min(px1, w2_bot), -w2_bot)
                p2_bot = max(min(px2, w2_bot), -w2_bot)
                p1_top = max(min(px1, w2_top), -w2_top)
                p2_top = max(min(px2, w2_top), -w2_top)
                
                if (p2_bot - p1_bot < 0.01) and (p2_top - p1_top < 0.01): continue
                
                d_verts = [
                    (p1_bot, z + base_thickness, 0),
                    (p2_bot, z + base_thickness, 0),
                    (p2_top, z + thickness, 0),
                    (p1_top, z + thickness, 0)
                ]
                if section_type in ('STERN', 'BOW'):
                    p_sy1 = (sy1 - (-l2)) / (2*l2) if l2 > 0 else 0
                    p_sy2 = (sy2 - (-l2)) / (2*l2) if l2 > 0 else 0
                    sc1 = scale_back + (scale_front - scale_back) * p_sy1
                    sc2 = scale_back + (scale_front - scale_back) * p_sy2
                else:
                    sc1 = 1.0
                    sc2 = 1.0
                d_back = [bm_deck.verts.new((c[0] * sc1, sy1, c[1])) for c in d_verts]
                d_front = [bm_deck.verts.new((c[0] * sc2, sy2, c[1])) for c in d_verts]
                bm_deck.faces.new((d_back[0], d_back[1], d_back[2], d_back[3])) # Back
                bm_deck.faces.new((d_front[0], d_front[3], d_front[2], d_front[1])) # Front
                bm_deck.faces.new((d_back[0], d_back[3], d_front[3], d_front[0])) # Left
                bm_deck.faces.new((d_back[1], d_front[1], d_front[2], d_back[2])) # Right
                bm_deck.faces.new((d_back[3], d_back[2], d_front[2], d_front[3])) # Top
                bm_deck.faces.new((d_back[0], d_front[0], d_front[1], d_back[1])) # Bottom
                
    bmesh.ops.remove_doubles(bm_deck, verts=bm_deck.verts, dist=0.001)

def build_hull(bm, props):

    """
    Builds the main hull base
    """
    pass

def generate_standalone_accessory(acc, ship_obj):
    import bpy
    import bmesh
    import math
    import mathutils
    
    props = ship_obj.ship_generator
    tol = props.tolerance
    
    mesh_name = f"Acc_{acc.acc_type}"
    mesh = bpy.data.meshes.new(mesh_name)
    obj = bpy.data.objects.new(mesh_name, mesh)
    bpy.context.collection.objects.link(obj)
    
    race_scale = 1.0
    if hasattr(props, 'creator_race'):
        if props.creator_race == 'HALFLING': race_scale = 0.75
        elif props.creator_race == 'GIANT': race_scale = 1.5
        elif props.creator_race == 'TITAN': race_scale = 2.0
        
    # Calculate target position based on ship
    h = props.wall_height * race_scale
    ft = props.floor_thickness
    
    if acc.level == 'MAIN':
        acc_z = h
    elif acc.level == 'CASTLE':
        has_castle = (props.section_type == 'STERN' and props.has_quarterdeck) or (props.section_type == 'BOW' and props.has_forecastle)
        acc_z = h + (props.deck_elevation * race_scale) if has_castle else h
    else: # BODEGA
        acc_z = ft
        
    obj.location = (
        ship_obj.location.x + acc.offset_x,
        ship_obj.location.y + acc.offset_y,
        ship_obj.location.z + acc_z
    )
    
    bm = bmesh.new()
    
    pin_radius = max(0.5, acc.snap_radius - tol)
    pin_depth = acc.snap_depth
    
    ret = bmesh.ops.create_cone(
        bm, cap_ends=True, cap_tris=False, segments=16,
        radius1=pin_radius, radius2=pin_radius, depth=pin_depth
    )
    bmesh.ops.translate(bm, vec=(0, 0, -pin_depth/2.0), verts=ret['verts'])
    
    # Store vertices for the visual part of the accessory so we can scale them without scaling the peg
    start_idx = len(bm.verts)
    
    if acc.acc_type == 'HELM':
        base = bmesh.ops.create_cone(bm, cap_ends=True, segments=16, radius1=4.0, radius2=3.0, depth=10.0)
        bmesh.ops.translate(bm, vec=(0, 0, 5.0), verts=base['verts'])
        
        wheel = bmesh.ops.create_cone(bm, cap_ends=True, segments=16, radius1=6.0, radius2=6.0, depth=1.5)
        rmat_x = mathutils.Matrix.Rotation(math.pi/2.0, 4, 'X')
        bmesh.ops.transform(bm, matrix=rmat_x, verts=wheel['verts'])
        bmesh.ops.translate(bm, vec=(0, 3.0, 10.0), verts=wheel['verts'])
        
    elif acc.acc_type.startswith('MAST') or acc.acc_type == 'BOWSPRIT':
        mast = bmesh.ops.create_cone(bm, cap_ends=True, segments=16, radius1=pin_radius, radius2=pin_radius*0.5, depth=150.0)
        
        if acc.acc_type == 'BOWSPRIT':
            rmat_x = mathutils.Matrix.Rotation(math.radians(-30), 4, 'X')
            bmesh.ops.transform(bm, matrix=rmat_x, verts=mast['verts'])
            bmesh.ops.translate(bm, vec=(0, 75.0, 37.5), verts=mast['verts'])
        else:
            bmesh.ops.translate(bm, vec=(0, 0, 75.0), verts=mast['verts'])
            
    # Apply race scale to the visual accessory geometry (skip the peg which is before start_idx)
    if race_scale != 1.0:
        visual_verts = bm.verts[start_idx:]
        if len(visual_verts) > 0:
            scale_mat = mathutils.Matrix.Scale(race_scale, 4)
            bmesh.ops.transform(bm, matrix=scale_mat, verts=visual_verts)
            
    # Apply user rotation
    rot_mat = mathutils.Matrix.Rotation(math.radians(acc.rotation_z), 4, 'Z')
    bmesh.ops.transform(bm, matrix=rot_mat, verts=bm.verts)
    
    bm.to_mesh(mesh)
    bm.free()
    
    for o in bpy.context.selected_objects:
        o.select_set(False)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

def rebuild_ship_mesh(obj):
    print("START REBUILD")
    if not obj or obj.type != 'MESH':
        return
        
    bpy.context.view_layer.update()
        
    props = obj.ship_generator
    if not props.is_ship and not props.is_connector_clip:
        return
        
    if bpy.context.object and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
        
    bm = bmesh.new()
    
    if props.is_connector_clip:
        tol = props.tolerance - props.clip_tightness
        peg_l2 = 10.0 + props.clip_length_offset # 20mm length by default
        p_verts = [
            (-3.0 + tol, 0, 0),
            (-5.0 + tol, 3.0 - tol, 0),
            (5.0 - tol, 3.0 - tol, 0),
            (3.0 - tol, 0, 0)
        ]
        p_back = [bm.verts.new((c[0], -peg_l2, c[1])) for c in p_verts]
        p_front = [bm.verts.new((c[0], peg_l2, c[1])) for c in p_verts]
        
        bm.faces.new((p_back[0], p_back[3], p_back[2], p_back[1])) # Outwards (-Y)
        bm.faces.new((p_front[0], p_front[1], p_front[2], p_front[3])) # Outwards (+Y)
        
        for i in range(4):
            bm.faces.new((p_back[i], p_back[(i+1)%4], p_front[(i+1)%4], p_front[i]))
            
        bm.normal_update()
        bm.to_mesh(obj.data)
        bm.free()
        return

    race_scale = 1.0
    if hasattr(props, 'creator_race'):
        if props.creator_race == 'HALFLING': race_scale = 0.75
        elif props.creator_race == 'GIANT': race_scale = 1.5
        elif props.creator_race == 'TITAN': race_scale = 2.0
        
    grid_size = 25.4
    l2 = (props.tiles_length * grid_size) / 2.0
    base_h = props.wall_height * race_scale
    h = base_h
    t = props.wall_thickness
    ft = props.floor_thickness
    
    if props.section_type == 'STERN' and props.has_quarterdeck:
        h += (props.deck_elevation * race_scale)
    elif props.section_type == 'BOW' and props.has_forecastle:
        h += (props.deck_elevation * race_scale)
    
    bot_w2 = (props.tiles_width * grid_size) / 2.0 + t
    w2 = bot_w2 * 2.0
    
    mid_w2 = w2 * 0.8
    mid_h = base_h * 0.4
    tol = props.tolerance
    
    # Calculate top widths to maintain perfectly collinear slopes with the base hull
    dz = base_h - mid_h
    top_w2 = w2
    
    plank_h = props.plank_height
    lapstrake_depth = props.lapstrake_depth
    
    def generate_outer_profile(checkpoints):
        pts = []
        for i in range(len(checkpoints) - 1):
            w0, z0 = checkpoints[i]
            w1, z1 = checkpoints[i+1]
            
            if z1 <= z0: continue
            
            z_current = z0
            while z_current < z1 - 0.001:
                z_next = min(z_current + plank_h, z1)
                
                p0 = (z_current - z0) / (z1 - z0)
                p1 = (z_next - z0) / (z1 - z0)
                
                x0 = w0 + (w1 - w0) * p0
                x1 = w0 + (w1 - w0) * p1
                
                pts.append((x0, z_current))
                pts.append((x1 + lapstrake_depth, z_next))
                
                z_current = z_next
        return pts
        
    profile_checkpoints = [(bot_w2, 0), (mid_w2, mid_h)]
    if h > base_h:
        profile_checkpoints.append((w2, base_h))
        profile_checkpoints.append((w2, h))
    else:
        profile_checkpoints.append((w2, base_h))
        
    outer_right_profile = generate_outer_profile(profile_checkpoints)
    
    outer_left = [(-p[0], p[1], 0) for p in reversed(outer_right_profile)]
    
    floor_bottom = [
        (-bot_w2, 0, 0),
        (bot_w2, 0, 0)
    ]
    
    outer_right = [(p[0], p[1], 0) for p in outer_right_profile]
    
    def get_inner_x_at_z(z):
        if z >= base_h:
            return w2 - t
        elif z >= mid_h:
            d_z = base_h - mid_h
            return (mid_w2 - t) + (z - mid_h) * ((w2 - mid_w2) / d_z) if d_z > 0 else (w2 - t)
        else:
            d_z = mid_h
            return (bot_w2 - t) + z * ((mid_w2 - bot_w2) / d_z) if d_z > 0 else (bot_w2 - t)
            
    inner_floor_x = get_inner_x_at_z(ft)
    
    inner_right = []
    has_ledge = getattr(props, 'generate_deck_ledge', True)
    ledge_w = getattr(props, 'deck_ledge_width', 2.0)
    
    deck_z = h - 2.0 if props.generate_top_deck else h
    
    raw_zs = [p[1] for p in reversed(outer_right_profile) if p[1] > ft]
    
    if has_ledge:
        def add_ledge(target_z, current_zs):
            new_zs = []
            for z, x in current_zs:
                if z > target_z or z < target_z - ledge_w:
                    new_zs.append((z, x))
            
            insert_idx = 0
            for i, (z, x) in enumerate(new_zs):
                if z < target_z:
                    insert_idx = i
                    break
            else:
                insert_idx = len(new_zs)
                
            ledge_points = [
                (target_z, get_inner_x_at_z(target_z)),
                (target_z, get_inner_x_at_z(target_z) - ledge_w),
                (target_z - ledge_w, get_inner_x_at_z(target_z - ledge_w))
            ]
            
            return new_zs[:insert_idx] + ledge_points + new_zs[insert_idx:]

        final_zs = [(z, get_inner_x_at_z(z)) for z in raw_zs]
        
        # Upper deck ledge
        if deck_z > ft + ledge_w:
            final_zs = add_ledge(deck_z, final_zs)
            
        # Lower deck ledge (for castles)
        has_castle = (props.section_type == 'STERN' and props.has_quarterdeck) or (props.section_type == 'BOW' and props.has_forecastle)
        lower_z = base_h - 2.0
        if has_castle and lower_z > ft + ledge_w:
            final_zs = add_ledge(lower_z, final_zs)
        
        for z, x in final_zs:
            inner_right.append((x, z, 0))
    else:
        for z in raw_zs:
            inner_right.append((get_inner_x_at_z(z), z, 0))
            
    inner_right.append((inner_floor_x, ft, 0))
    inner_left = [(-p[0], p[1], 0) for p in reversed(inner_right)]
        
    verts_coords = outer_left[:-1] + floor_bottom + outer_right[1:] + inner_right + inner_left
    
    idx_outer_left = 0
    len_outer_left = len(outer_left) - 1
    
    idx_floor_bot = len_outer_left
    len_floor_bot = len(floor_bottom)
    
    idx_outer_right = idx_floor_bot + len_floor_bot - 1
    
    idx_inner_right = idx_outer_right + len(outer_right)
    len_inner_right = len(inner_right)
    
    idx_floor_top = idx_inner_right + len_inner_right
    len_floor_top = 0
    
    idx_inner_left = idx_floor_top + len_floor_top
    len_inner_left = len(inner_left)
    
    left_cap_indices = list(range(0, idx_floor_bot + 1)) + list(range(idx_inner_left, len(verts_coords)))
    right_cap_indices = list(range(idx_outer_right, idx_floor_top))
    floor_cap_indices = [idx_floor_bot, idx_outer_right, idx_floor_top - 1, idx_inner_left]

    def create_hull_segment(bm, start_y, end_y, scale_front=1.0, scale_back=1.0):
        num_segments = 1 if props.section_type == 'MID' else 12
        segments = []
        
        for i in range(num_segments + 1):
            t = i / num_segments
            y = start_y + (end_y - start_y) * t
            sc = scale_back + (scale_front - scale_back) * t
            segments.append([bm.verts.new((c[0] * sc, y, c[1])) for c in verts_coords])
            
        # Floor Caps
        f3 = bm.faces.new([segments[0][i] for i in floor_cap_indices][::-1])
        f6 = bm.faces.new([segments[-1][i] for i in floor_cap_indices])
        bmesh.ops.triangulate(bm, faces=[f3, f6])
        
        # Monotonic path triangulation for walls to prevent triangulator tearing
        # and to properly handle cases where K (inner vertices) > M (outer vertices).
        M = len_outer_left + 1 # Number of vertices in outer_right_profile
        K = len_inner_right - 1 # Number of corresponding valid inner vertices above the floor
        
        path = [(0, K)]
        o, i = 0, K
        while o < M - 1 or i > 0:
            prog_o = (o + 1) / (M - 1) if M > 1 else 1.0
            prog_i = (K - (i - 1)) / K if K > 0 else 1.0
            
            if o < M - 1 and (i == 0 or prog_o <= prog_i):
                o += 1
            else:
                i -= 1
            path.append((o, i))
            
        for p_idx in range(len(path) - 1):
            o1, i1 = path[p_idx]
            o2, i2 = path[p_idx+1]
            
            # Left Wall Triangles
            ol1, ol2 = o1, o2
            il1, il2 = idx_inner_left + i1, idx_inner_left + i2
            
            if o1 == o2:
                bm.faces.new((segments[0][ol1], segments[0][il2], segments[0][il1]))
                bm.faces.new((segments[-1][ol1], segments[-1][il1], segments[-1][il2]))
            else:
                bm.faces.new((segments[0][ol1], segments[0][ol2], segments[0][il1]))
                bm.faces.new((segments[-1][ol1], segments[-1][il1], segments[-1][ol2]))
                
            # Right Wall Triangles
            or1, or2 = idx_outer_right + (M - 1 - o1), idx_outer_right + (M - 1 - o2)
            ir1, ir2 = idx_inner_right + (K - i1), idx_inner_right + (K - i2)
            
            if o1 == o2:
                bm.faces.new((segments[0][or1], segments[0][ir1], segments[0][ir2]))
                bm.faces.new((segments[-1][or1], segments[-1][ir2], segments[-1][ir1]))
            else:
                bm.faces.new((segments[0][or1], segments[0][ir1], segments[0][or2]))
                bm.faces.new((segments[-1][or1], segments[-1][or2], segments[-1][ir1]))

        # === Solid Plugs to Close the Ship's Interior ===
        plug_coords = [verts_coords[i] for i in range(idx_inner_right, len(verts_coords))]
        
        def add_solid_plug(y_back, y_front, min_z=None, max_z=None):
            p_prog_b = (y_back - (-l2)) / (2 * l2) if l2 > 0 else 0
            p_prog_f = (y_front - (-l2)) / (2 * l2) if l2 > 0 else 0
            s_b = scale_back + (scale_front - scale_back) * p_prog_b
            s_f = scale_back + (scale_front - scale_back) * p_prog_f
            
            def get_clamped_coord(c):
                z = c[1]
                
                # Apply max_z if needed
                if max_z is not None and z > max_z:
                    ix = get_inner_x_at_z(max_z)
                    if c[0] < 0:
                        ix = -ix
                    return (ix, max_z, 0)
                
                # Apply min_z if needed
                if min_z is None or z >= min_z:
                    return c
                
                # Interpolate X at min_z (inner wall)
                ix = get_inner_x_at_z(min_z)
                if c[0] < 0:
                    ix = -ix
                return (ix, min_z, 0)
                
            filtered_coords = []
            for c in plug_coords:
                cc = get_clamped_coord(c)
                if not filtered_coords or cc != filtered_coords[-1]:
                    filtered_coords.append(cc)
            
            pb_verts = []
            for cc in filtered_coords:
                x = cc[0] * s_b
                z = cc[1]
                if x > 0.1: x += 0.1
                elif x < -0.1: x -= 0.1
                if z < props.floor_thickness + 0.1: z -= 0.1
                pb_verts.append(bm.verts.new((x, y_back, z)))
            
            pf_verts = []
            for cc in filtered_coords:
                x = cc[0] * s_f
                z = cc[1]
                if x > 0.1: x += 0.1
                elif x < -0.1: x -= 0.1
                if z < props.floor_thickness + 0.1: z -= 0.1
                pf_verts.append(bm.verts.new((x, y_front, z)))
            
            f_pb = bm.faces.new(pb_verts[::-1]) # CW
            f_pf = bm.faces.new(pf_verts)       # CCW
            bmesh.ops.triangulate(bm, faces=[f_pb, f_pf])
            
            for i in range(len(filtered_coords)):
                bm.faces.new((pb_verts[i], pb_verts[(i+1)%len(filtered_coords)], pf_verts[(i+1)%len(filtered_coords)], pf_verts[i]))
        
        def add_arch_plug(y_back, y_front, min_z, max_z):
            p_prog_b = (y_back - (-l2)) / (2 * l2) if l2 > 0 else 0
            p_prog_f = (y_front - (-l2)) / (2 * l2) if l2 > 0 else 0
            s_b = scale_back + (scale_front - scale_back) * p_prog_b
            s_f = scale_back + (scale_front - scale_back) * p_prog_f
            
            def get_arch_coord(c):
                z = c[1]
                if z > max_z: z_eff = max_z
                elif z < min_z: z_eff = min_z
                else: z_eff = z
                    
                ix = get_inner_x_at_z(z_eff)
                offset = z_eff - min_z
                
                if c[0] < 0:
                    ix = -ix + offset
                    if ix > -0.1: ix = -0.1
                else:
                    ix = ix - offset
                    if ix < 0.1: ix = 0.1
                    
                return (ix, z_eff, 0)
                
            filtered_coords = []
            for c in plug_coords:
                cc = get_arch_coord(c)
                if not filtered_coords or cc != filtered_coords[-1]:
                    filtered_coords.append(cc)
            
            pb_verts = []
            for cc in filtered_coords:
                x = cc[0] * s_b
                z = cc[1]
                if x > 0.1: x += 0.1
                elif x < -0.1: x -= 0.1
                if z < props.floor_thickness + 0.1: z -= 0.1
                pb_verts.append(bm.verts.new((x, y_back, z)))
            
            pf_verts = []
            for cc in filtered_coords:
                x = cc[0] * s_f
                z = cc[1]
                if x > 0.1: x += 0.1
                elif x < -0.1: x -= 0.1
                if z < props.floor_thickness + 0.1: z -= 0.1
                pf_verts.append(bm.verts.new((x, y_front, z)))
            
            f_pb = bm.faces.new(pb_verts[::-1])
            f_pf = bm.faces.new(pf_verts)
            bmesh.ops.triangulate(bm, faces=[f_pb, f_pf])
            
            for i in range(len(filtered_coords)):
                bm.faces.new((pb_verts[i], pb_verts[(i+1)%len(filtered_coords)], pf_verts[(i+1)%len(filtered_coords)], pf_verts[i]))
        
        if props.section_type == 'STERN':
            add_solid_plug(-l2, -l2 + props.wall_thickness) # Transom plug (REAR, always closed)
            if props.has_quarterdeck:
                # Archway / upper wall (parte B)
                if getattr(props, 'quarterdeck_closed_front', False):
                    add_solid_plug(l2 - props.wall_thickness, l2, min_z=base_h)
                else:
                    add_solid_plug(l2 - props.wall_thickness, l2, min_z=h - 10.0)
                    if getattr(props, 'generate_print_supports', False):
                        add_arch_plug(l2 - props.wall_thickness, l2, min_z=base_h, max_z=h - 10.0)
                    if getattr(props, 'generate_print_supports', False):
                        add_arch_plug(l2 - props.wall_thickness, l2, min_z=base_h, max_z=h - 10.0)
        elif props.section_type == 'BOW':
            add_solid_plug(l2 - props.wall_thickness, l2) # Tip plug (FRONT, always closed)
            if props.has_forecastle:
                # Archway / upper wall (parte B)
                if getattr(props, 'forecastle_closed_back', False):
                    add_solid_plug(-l2, -l2 + props.wall_thickness, min_z=base_h)
                else:
                    add_solid_plug(-l2, -l2 + props.wall_thickness, min_z=h - 10.0)
                    if getattr(props, 'generate_print_supports', False):
                        add_arch_plug(-l2, -l2 + props.wall_thickness, min_z=base_h, max_z=h - 10.0)
                    if getattr(props, 'generate_print_supports', False):
                        add_arch_plug(-l2, -l2 + props.wall_thickness, min_z=base_h, max_z=h - 10.0)
                
        num_verts = len(verts_coords)
        for s in range(num_segments):
            for i in range(num_verts):
                bm.faces.new((segments[s][i], segments[s][(i+1)%num_verts], segments[s+1][(i+1)%num_verts], segments[s+1][i]))
            
        return segments[-1], segments[0]

    if props.section_type == 'MID':
        create_hull_segment(bm, -l2, l2)
    elif props.section_type == 'BOW':
        create_hull_segment(bm, -l2, l2, scale_front=0.01, scale_back=1.0)
    elif props.section_type == 'STERN':
        create_hull_segment(bm, -l2, l2, scale_front=1.0, scale_back=0.7)

    if props.has_grid:
        groove_width = 1.0
        
        max_extent_x = bot_w2 - t
        max_extent_y = l2
        
        max_idx_x = int(math.ceil(max_extent_x / grid_size))
        max_idx_y = int(math.ceil(max_extent_y / grid_size))
        
        tile_height = 0.5
        
        for ix in range(-max_idx_x, max_idx_x):
            for iy in range(-max_idx_y, max_idx_y):
                cx = (ix + 0.5) * grid_size
                cy = (iy + 0.5) * grid_size
                
                tx1 = cx - (grid_size/2.0) + groove_width
                tx2 = cx + (grid_size/2.0) - groove_width
                ty1 = cy - (grid_size/2.0) + groove_width
                ty2 = cy + (grid_size/2.0) - groove_width
                
                valid_ty1 = max(ty1, -l2 + groove_width)
                valid_ty2 = min(ty2, l2 - groove_width)
                
                if valid_ty1 >= valid_ty2:
                    continue
                    
                if props.section_type == 'BOW':
                    progress_start = (valid_ty1 - (-l2)) / (2*l2)
                    progress_end = (valid_ty2 - (-l2)) / (2*l2)
                    w2_start = inner_floor_x * (1.0 - progress_start)
                    w2_end = inner_floor_x * (1.0 - progress_end)
                elif props.section_type == 'STERN':
                    progress_start = (valid_ty1 - (-l2)) / (2*l2)
                    progress_end = (valid_ty2 - (-l2)) / (2*l2)
                    w2_start = inner_floor_x * (0.7 + 0.3 * progress_start)
                    w2_end = inner_floor_x * (0.7 + 0.3 * progress_end)
                else:
                    w2_start = inner_floor_x
                    w2_end = inner_floor_x
                    
                plank_gap = 0.4
                num_main_planks = 2
                full_w = tx2 - tx1
                if full_w <= 0: continue
                pw = full_w / num_main_planks
                planks = []
                
                if iy % 2 == 0:
                    for p in range(num_main_planks):
                        px1 = tx1 + p * pw
                        px2 = tx1 + (p + 1) * pw - plank_gap
                        planks.append((px1, px2))
                else:
                    px1 = tx1
                    px2 = tx1 + pw / 2 - plank_gap
                    planks.append((px1, px2))
                    for p in range(num_main_planks - 1):
                        px1 = tx1 + pw / 2 + p * pw
                        px2 = tx1 + pw / 2 + (p + 1) * pw - plank_gap
                        planks.append((px1, px2))
                    px1 = tx1 + pw / 2 + (num_main_planks - 1) * pw
                    px2 = tx2 - plank_gap
                    planks.append((px1, px2))
                
                for px1, px2 in planks:
                    if px2 <= px1: continue
                    
                    p1_b = max(min(px1, w2_start), -w2_start)
                    p2_b = max(min(px2, w2_start), -w2_start)
                    p1_f = max(min(px1, w2_end), -w2_end)
                    p2_f = max(min(px2, w2_end), -w2_end)
                    
                    back_valid = (p2_b - p1_b >= 0.01)
                    front_valid = (p2_f - p1_f >= 0.01)
                    
                    if not back_valid and not front_valid:
                        continue
                        
                    if back_valid and front_valid:
                        v1 = bm.verts.new((p1_b, valid_ty1, ft - 0.2))
                        v2 = bm.verts.new((p2_b, valid_ty1, ft - 0.2))
                        v3 = bm.verts.new((p2_f, valid_ty2, ft - 0.2))
                        v4 = bm.verts.new((p1_f, valid_ty2, ft - 0.2))
                        f_tile = bm.faces.new((v1, v2, v3, v4))
                    elif back_valid and not front_valid:
                        v1 = bm.verts.new((p1_b, valid_ty1, ft - 0.2))
                        v2 = bm.verts.new((p2_b, valid_ty1, ft - 0.2))
                        v3 = bm.verts.new((p1_f, valid_ty2, ft - 0.2))
                        f_tile = bm.faces.new((v1, v2, v3))
                    elif not back_valid and front_valid:
                        v1 = bm.verts.new((p1_b, valid_ty1, ft - 0.2))
                        v2 = bm.verts.new((p2_f, valid_ty2, ft - 0.2))
                        v3 = bm.verts.new((p1_f, valid_ty2, ft - 0.2))
                        f_tile = bm.faces.new((v1, v2, v3))
                        
                    geom = bmesh.ops.extrude_face_region(bm, geom=[f_tile])
                    extruded_verts = [v for v in geom['geom'] if isinstance(v, bmesh.types.BMVert)]
                    bmesh.ops.translate(bm, vec=(0, 0, tile_height + 0.2), verts=extruded_verts)
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.001)

    deck_obj_name = obj.name + "_Deck"
    deck_obj = bpy.data.objects.get(deck_obj_name)

    if props.generate_top_deck:
        if not deck_obj:
            deck_mesh = bpy.data.meshes.new(deck_obj_name)
            deck_obj = bpy.data.objects.new(deck_obj_name, deck_mesh)
            bpy.context.collection.objects.link(deck_obj)
            deck_obj.parent = obj
            deck_obj.matrix_local = mathutils.Matrix.Identity(4)
            
        bm_deck = bmesh.new()
        
        deck_z = h - 2.0
        deck_thickness = 2.0
        deck_offset = getattr(props, 'deck_width_offset', 0.0)
        
        # Match deck shape perfectly to hull inner wall
        deck_w2_bot = get_inner_x_at_z(deck_z) - tol + deck_offset
        deck_w2_top = get_inner_x_at_z(deck_z + deck_thickness) - tol + deck_offset
        
        deck_start_y = -l2
        deck_end_y = l2
        scale_front_deck = 1.0
        scale_back_deck = 1.0
        
        has_castle = (props.section_type == 'STERN' and props.has_quarterdeck) or (props.section_type == 'BOW' and props.has_forecastle)
        
        if props.section_type == 'BOW':
            scale_front_deck = 0.01
        elif props.section_type == 'STERN':
            scale_front_deck = 1.0
            scale_back_deck = 0.7
            
            
        create_deck_planks(bm_deck, deck_start_y, deck_end_y, deck_w2_bot, deck_w2_top, deck_z, deck_thickness, scale_front_deck, scale_back_deck, props.section_type, l2, props.has_grid)
        
        has_castle = (props.section_type == 'STERN' and props.has_quarterdeck) or (props.section_type == 'BOW' and props.has_forecastle)
        if has_castle:
            lower_z = base_h - 2.0
            
            def get_outer_x_at_z(z):
                if z >= base_h:
                    return w2
                elif z >= mid_h:
                    d_z = base_h - mid_h
                    return mid_w2 + (z - mid_h) * ((w2 - mid_w2) / d_z) if d_z > 0 else w2
                else:
                    d_z = mid_h
                    return bot_w2 + z * ((mid_w2 - bot_w2) / d_z) if d_z > 0 else bot_w2
                    
            outer_lower_w2 = get_outer_x_at_z(base_h)
                
            lower_deck_start_y = -l2
            lower_deck_end_y = l2
                
            lower_deck_w2_bot = get_inner_x_at_z(lower_z) - tol + deck_offset
            lower_deck_w2_top = get_inner_x_at_z(lower_z + deck_thickness) - tol + deck_offset
            create_deck_planks(bm_deck, lower_deck_start_y, lower_deck_end_y, lower_deck_w2_bot, lower_deck_w2_top, lower_z, deck_thickness, scale_front_deck, scale_back_deck, props.section_type, l2, props.has_grid)
                    
        # Deck mesh finalization moved to the end after accessories

    td_obj_name = obj.name + "_Trapdoor"
    td_obj = bpy.data.objects.get(td_obj_name)
    
    if getattr(props, 'has_trapdoor', False):
        if not td_obj:
            td_mesh = bpy.data.meshes.new(td_obj_name)
            td_obj = bpy.data.objects.new(td_obj_name, td_mesh)
            bpy.context.collection.objects.link(td_obj)
            td_obj.parent = obj
            td_obj.matrix_local = mathutils.Matrix.Identity(4)
            
        bm_td = bmesh.new()
        
        td_size = getattr(props, 'trapdoor_size', 1.0) * 25.4
        tol = getattr(props, 'tolerance', 0.2)
        lid_size = td_size - (tol * 2.0) # Apply FDM tolerance to all sides
        lid_thick = props.floor_thickness
        
        mast_td_z = ft
        if props.generate_top_deck:
            mast_td_z = h - 2.0

        # Position the lid exactly inside the hole, so the user can see it in place.
        # It can be separated later by the user if needed.
        offset_y = getattr(props, 'trapdoor_y_offset', 0.0)
        
        ret = bmesh.ops.create_cube(bm_td, size=1.0)
        bmesh.ops.scale(bm_td, vec=(lid_size, lid_size, lid_thick), verts=ret['verts'])
        # Translate so it's flush with the floor or deck
        bmesh.ops.translate(bm_td, vec=(0, offset_y, mast_td_z + lid_thick / 2.0), verts=ret['verts'])
        
        # Add a simple handle/ring to the trapdoor
        ret_handle = bmesh.ops.create_cube(bm_td, size=1.0)
        bmesh.ops.scale(bm_td, vec=(lid_size * 0.2, lid_size * 0.4, 2.0), verts=ret_handle['verts'])
        bmesh.ops.translate(bm_td, vec=(0, offset_y, mast_td_z + lid_thick + 1.0), verts=ret_handle['verts'])
        
        bm_td.normal_update()
        bm_td.to_mesh(td_obj.data)
        bm_td.free()
    else:
        if td_obj:
            bpy.data.objects.remove(td_obj, do_unlink=True)



    mast_td_bm = bm
    mast_td_z = ft
    
    if props.generate_top_deck:
        mast_td_bm = bm_deck
        mast_td_z = deck_z



    if props.generate_top_deck:
        bm_deck.normal_update()
        bm_deck.to_mesh(deck_obj.data)
        bm_deck.free()
    else:
        if deck_obj:
            bpy.data.objects.remove(deck_obj, do_unlink=True)

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.normal_update()
    bm.to_mesh(obj.data)
    bm.free()
    
    # --- Separate Deck Cutter ---
    deck_cutter_name = obj.name + "_DeckCuts"
    deck_cutter_obj = bpy.data.objects.get(deck_cutter_name)
    
    needs_deck_cuts = False
    if props.generate_top_deck:
        if getattr(props, 'generate_stairs', False):
            needs_deck_cuts = True
        if getattr(props, 'has_trapdoor', False) or getattr(props, 'has_mast', False):
            needs_deck_cuts = True
        for acc in props.accessories:
            if acc.level in ('MAIN', 'CASTLE'):
                needs_deck_cuts = True

    if needs_deck_cuts:
        if not deck_cutter_obj:
            deck_cutter_mesh = bpy.data.meshes.new(deck_cutter_name)
            deck_cutter_obj = bpy.data.objects.new(deck_cutter_name, deck_cutter_mesh)
            bpy.context.collection.objects.link(deck_cutter_obj)
            deck_cutter_obj.parent = obj
            deck_cutter_obj.matrix_local = mathutils.Matrix.Identity(4)
            deck_cutter_obj.display_type = 'WIRE'
            deck_cutter_obj.hide_render = True
            deck_cutter_obj.hide_viewport = True
        
        bm_deck_cutter = bmesh.new()
        
        if getattr(props, 'generate_stairs', False):
            y_start = l2 if props.section_type == 'STERN' else -l2
            y_dir = -1.0 if props.section_type == 'STERN' else 1.0
            for stair in props.stairs:
                level = getattr(stair, 'level', 'BODEGA_MAIN')
                direction = getattr(stair, 'direction', 'INWARD')
                
                s_width = getattr(stair, 'width', 20.0) * race_scale
                s_length = getattr(stair, 'length', 40.0) * race_scale
                off_x = getattr(stair, 'offset_x', 0.0)
                off_y = getattr(stair, 'offset_y', 0.0)
                rot_z = getattr(stair, 'rotation_z', 0.0)
                
                y_dir_stair = y_dir * (-1.0 if direction == 'OUTWARD' else 1.0)
                
                tol = getattr(props, 'tolerance', 0.2)
                hole_len = s_length + (tol * 2.0)
                hole_w = s_width + (tol * 2.0)
                hole_h = 20.0
                
                cy = y_start + (off_y * y_dir) + (s_length / 2.0 * y_dir_stair)
                cx = off_x
                
                has_castle = (props.section_type == 'STERN' and props.has_quarterdeck) or (props.section_type == 'BOW' and props.has_forecastle)
                if level == 'BODEGA_MAIN':
                    cz = base_h
                else:
                    if not has_castle:
                        continue
                    cz = h
                
                ret = bmesh.ops.create_cube(bm_deck_cutter, size=1.0)
                bmesh.ops.scale(bm_deck_cutter, vec=(hole_w, hole_len, hole_h), verts=ret['verts'])
                if rot_z != 0.0:
                    rot_mat = mathutils.Matrix.Rotation(math.radians(rot_z), 4, 'Z')
                    bmesh.ops.transform(bm_deck_cutter, matrix=rot_mat, verts=ret['verts'])
                bmesh.ops.translate(bm_deck_cutter, vec=(cx, cy, cz), verts=ret['verts'])
                
        if getattr(props, 'has_trapdoor', False):
            td_size = getattr(props, 'trapdoor_size', 1.0) * 25.4
            y_off = getattr(props, 'trapdoor_y_offset', 0.0)
            ret = bmesh.ops.create_cube(bm_deck_cutter, size=1.0)
            bmesh.ops.scale(bm_deck_cutter, vec=(td_size, td_size, 10.0), verts=ret['verts'])
            bmesh.ops.translate(bm_deck_cutter, vec=(0, y_off, deck_z), verts=ret['verts'])

        if getattr(props, 'has_mast', False):
            sock_h = getattr(props, 'mast_socket_height', 15.0)
            sock_d = getattr(props, 'mast_diameter', 8.0)
            y_off = getattr(props, 'mast_y_offset', 0.0)
            cut_h = sock_h + 4.0
            ret = bmesh.ops.create_cone(bm_deck_cutter, cap_ends=True, cap_tris=False, segments=32, radius1=sock_d/2.0, radius2=sock_d/2.0, depth=cut_h)
            bmesh.ops.translate(bm_deck_cutter, vec=(0, y_off, deck_z), verts=ret['verts'])
        
        for acc in props.accessories:
            if acc.level in ('MAIN', 'CASTLE'):
                acc_z = h
                
                cut_h = acc.snap_depth + 4.0 # Add extra depth to ensure clean boolean cut
                ret = bmesh.ops.create_cone(bm_deck_cutter, cap_ends=True, cap_tris=False, segments=16, radius1=acc.snap_radius, radius2=acc.snap_radius, depth=cut_h)
                bmesh.ops.translate(bm_deck_cutter, vec=(acc.offset_x, acc.offset_y, acc_z - acc.snap_depth/2.0), verts=ret['verts'])
        
        bm_deck_cutter.to_mesh(deck_cutter_obj.data)
        bm_deck_cutter.free()
        
        deck_obj = bpy.data.objects.get(obj.name + "_Deck")
        if deck_obj:
            mod_deck = deck_obj.modifiers.get("DeckCuts")
            if not mod_deck:
                mod_deck = deck_obj.modifiers.new("DeckCuts", 'BOOLEAN')
            mod_deck.operation = 'DIFFERENCE'
            mod_deck.object = deck_cutter_obj
            mod_deck.solver = 'EXACT'
            if hasattr(mod_deck, 'use_self'):
                mod_deck.use_self = True
    else:
        if deck_cutter_obj:
            bpy.data.objects.remove(deck_cutter_obj, do_unlink=True)
        deck_obj = bpy.data.objects.get(obj.name + "_Deck")
        if deck_obj:
            mod_deck = deck_obj.modifiers.get("DeckCuts")
            if mod_deck:
                deck_obj.modifiers.remove(mod_deck)
    # ----------------------------

    ensure_cutter(obj, props, l2, bot_w2, mid_w2, top_w2, mid_h, h, base_h)

    # Post-boolean additions: Railings and Mast (placed in a separate object to avoid exact solver bugs)
    rail_name = obj.name + "_Accesorios"
    rail_obj = bpy.data.objects.get(rail_name)
    
    if getattr(props, 'generate_railings', False) or getattr(props, 'has_mast', False) or getattr(props, 'generate_stairs', False):
        if not rail_obj:
            rmesh = bpy.data.meshes.new(rail_name)
            rail_obj = bpy.data.objects.new(rail_name, rmesh)
            bpy.context.collection.objects.link(rail_obj)
            rail_obj.parent = obj
            
        bm_final = bmesh.new()
        
        mast_td_z = ft
        if props.generate_top_deck:
            mast_td_z = h - 2.0
            
        if getattr(props, 'generate_stairs', False):
            y_start = l2 if props.section_type == 'STERN' else -l2
            y_dir = -1.0 if props.section_type == 'STERN' else 1.0
            
            for stair in props.stairs:
                level = getattr(stair, 'level', 'BODEGA_MAIN')
                direction = getattr(stair, 'direction', 'INWARD')
                
                s_width = getattr(stair, 'width', 20.0) * race_scale
                stair_w2 = s_width / 2.0
                
                s_length = getattr(stair, 'length', 40.0) * race_scale
                
                off_x = getattr(stair, 'offset_x', 0.0)
                off_y = getattr(stair, 'offset_y', 0.0)
                rot_z = getattr(stair, 'rotation_z', 0.0)
                
                step_height = 5.0
                
                y_dir_stair = y_dir * (-1.0 if direction == 'OUTWARD' else 1.0)
                
                cx = off_x
                cy = y_start + (off_y * y_dir) + (s_length / 2.0 * y_dir_stair)
                rot_mat = None
                if rot_z != 0.0:
                    rot_mat = mathutils.Matrix.Rotation(math.radians(rot_z), 4, 'Z')
                
                def xform(lx, ly, lz, cx_val=cx, cy_val=cy, rm_val=rot_mat):
                    vec = mathutils.Vector((lx, ly, lz))
                    if rm_val:
                        vec = rm_val @ vec
                    return (vec.x + cx_val, vec.y + cy_val, vec.z)
                
                has_castle = (props.section_type == 'STERN' and getattr(props, 'has_quarterdeck', False)) or (props.section_type == 'BOW' and getattr(props, 'has_forecastle', False))
                if level == 'BODEGA_MAIN':
                    z_start = ft
                    target_z = base_h
                else:
                    if not has_castle:
                        continue
                    z_start = base_h
                    target_z = h
                
                elev_lower = target_z - z_start
                if elev_lower > 0:
                    num_steps = int(math.ceil(elev_lower / step_height))
                    step_depth = s_length / float(num_steps)
                    
                    pts = []
                    y_front = num_steps * step_depth * y_dir_stair - (s_length / 2.0 * y_dir_stair)
                    pts.append((y_front, z_start))
                    
                    for i in range(num_steps):
                        z1 = z_start + (i + 1) * step_height
                        if i == num_steps - 1:
                            z1 = target_z # Ensure exact match on last step
                        
                        dist = num_steps - 1 - i
                        y0_loc = dist * step_depth * y_dir_stair - (s_length / 2.0 * y_dir_stair)
                        y1_loc = (dist + 1) * step_depth * y_dir_stair - (s_length / 2.0 * y_dir_stair)
                        
                        pts.append((y1_loc, z1))
                        pts.append((y0_loc, z1))
                        
                    pts.append((pts[-1][0], z_start))
                    
                    verts_left = [bm_final.verts.new(xform(-stair_w2, p[0], p[1])) for p in pts]
                    verts_right = [bm_final.verts.new(xform(stair_w2, p[0], p[1])) for p in pts]
                    
                    if y_dir_stair > 0:
                        bm_final.faces.new(verts_left)
                        bm_final.faces.new(tuple(reversed(verts_right)))
                    else:
                        bm_final.faces.new(tuple(reversed(verts_left)))
                        bm_final.faces.new(verts_right)
                        
                    for i in range(len(pts)):
                        i_next = (i + 1) % len(pts)
                        if y_dir_stair > 0:
                            bm_final.faces.new((verts_left[i], verts_right[i], verts_right[i_next], verts_left[i_next]))
                        else:
                            bm_final.faces.new((verts_left[i], verts_left[i_next], verts_right[i_next], verts_right[i]))



        if getattr(props, 'generate_railings', False):
            rh = getattr(props, 'railing_height', 12.0)
            rt = getattr(props, 'railing_thickness', 2.5)
            rs = getattr(props, 'railing_spacing', 20.0)
            
            sc_front = 1.0
            sc_back = 1.0
            if props.section_type == 'BOW':
                sc_front = 0.01
            elif props.section_type == 'STERN':
                sc_back = 0.7
                
            def add_railing_line(bm, x1, y1, x2, y2, z, is_back=False, trim_start=0.0, trim_end=0.0):
                length = math.hypot(x2 - x1, y2 - y1)
                if length < 0.1: return
                
                angle = math.atan2(y2 - y1, x2 - x1)
                dx = math.cos(angle)
                dy = math.sin(angle)
                
                hx1 = x1 + dx * trim_start
                hy1 = y1 + dy * trim_start
                hx2 = x2 - dx * trim_end
                hy2 = y2 - dy * trim_end
                
                h_length = math.hypot(hx2 - hx1, hy2 - hy1)
                if h_length < 0.1: return
                
                num_posts = max(1, int(round(h_length / rs)))
                
                # Handrail
                ret = bmesh.ops.create_cube(bm, size=1.0)
                bmesh.ops.scale(bm, vec=(h_length + rt, rt, rt), verts=ret['verts'])
                rot = mathutils.Matrix.Rotation(angle, 4, 'Z')
                bmesh.ops.transform(bm, matrix=rot, verts=ret['verts'])
                bmesh.ops.translate(bm, vec=((hx1+hx2)/2.0, (hy1+hy2)/2.0, z + rh - rt/2.0), verts=ret['verts'])
                
                # Posts
                for i in range(num_posts + 1):
                    t = i / num_posts
                    px = hx1 + (hx2 - hx1) * t
                    py = hy1 + (hy2 - hy1) * t
                    
                    ret = bmesh.ops.create_cube(bm, size=1.0)
                    bmesh.ops.scale(bm, vec=(rt, rt, rh), verts=ret['verts'])
                    bmesh.ops.transform(bm, matrix=rot, verts=ret['verts'])
                    bmesh.ops.translate(bm, vec=(px, py, z + rh/2.0), verts=ret['verts'])
    
            off_in = getattr(props, 'railing_offset_inward', 0.5)
            
            # Helper to get precisely mathematically offset railing points for right side (x > 0)
            def get_shifted_railing(w_back, w_front, y_start, y_end, offset):
                dx = w_front - w_back
                dy = y_end - y_start
                L_line = math.hypot(dx, dy)
                if L_line < 0.001:
                    return w_back - offset, w_front - offset
                nx = -dy / L_line
                ny = dx / L_line
                Px = w_back + offset * nx
                Py = y_start + offset * ny
                t_start = (y_start - Py) / dy if dy != 0 else 0
                x_start = Px + t_start * dx
                t_end = (y_end - Py) / dy if dy != 0 else 0
                x_end = Px + t_end * dx
                return x_start, x_end, Px, Py, dx, dy

            w_back = top_w2 * sc_back
            w_front = top_w2 * sc_front
            x_br, x_fr, Px, Py, d_x, d_y = get_shifted_railing(w_back, w_front, -l2, l2, off_in)
            
            y_fl = l2
            y_fr = l2
            
            if props.section_type == 'BOW':
                # For the bow, find exactly where the railing intersects the side of the capping post
                y_post = l2 - (rt + 2 * off_in) * l2 / top_w2
                t_post = (y_post - Py) / d_y if d_y != 0 else 0
                x_fr = Px + t_post * d_x
                y_fr = y_post
                x_fl = -x_fr
                y_fl = y_post
            else:
                if x_fr < 0 and x_br > 0:
                    t = (0 - x_br) / (x_fr - x_br)
                    y_fr = -l2 + t * (2 * l2)
                    x_fr = 0.0
                x_fl = -x_fr
                
            x_bl = -x_br
            
            # Center the back railing on the back wall (thickness = 1.2, move inward 1.5 = 2.1)
            trim_s = 2.1 if props.section_type == 'STERN' else 0.0
            trim_e = 0.0
            
            if props.section_type == 'BOW':
                # Add a capping post at the tip
                ret = bmesh.ops.create_cube(bm_final, size=1.0)
                bmesh.ops.scale(bm_final, vec=(rt, rt, rh), verts=ret['verts'])
                bmesh.ops.translate(bm_final, vec=(0, y_post, h + rh/2.0), verts=ret['verts'])
                
                # Trim the side railings so their handrails end exactly inside the post
                # The handrail extends rt/2 past the end point, so we trim by rt/2
                trim_e = rt / 2.0
            
            add_railing_line(bm_final, x_bl, -l2, x_fl, y_fl, h, trim_start=trim_s, trim_end=trim_e)
            add_railing_line(bm_final, x_br, -l2, x_fr, y_fr, h, trim_start=trim_s, trim_end=trim_e)
            if props.section_type == 'STERN':
                add_railing_line(bm_final, x_br, -l2 + 2.1, x_bl, -l2 + 2.1, h, is_back=True)
                
        if getattr(props, 'has_mast', False):
            sock_h = getattr(props, 'mast_socket_height', 15.0)
            sock_d = getattr(props, 'mast_diameter', 8.0)
            y_off = getattr(props, 'mast_y_offset', 0.0)
            
            cut_h = sock_h + 2.0
            ret = bmesh.ops.create_cone(bm_final, cap_ends=True, cap_tris=False, segments=32, radius1=sock_d/2.0-0.5, radius2=sock_d/2.0-0.5, depth=cut_h)
            bmesh.ops.translate(bm_final, vec=(0, y_off, mast_td_z + sock_h/2.0), verts=ret['verts'])
            
        bm_final.normal_update()
        rail_obj.data.clear_geometry()
        bm_final.to_mesh(rail_obj.data)
        bm_final.free()
    else:
        if rail_obj:
            bpy.data.objects.remove(rail_obj, do_unlink=True)
            
    # Live-sync already extracted standalone accessory models
    for idx, acc in enumerate(props.accessories):
        acc_name = f"{obj.name}_Acc_{idx}_{acc.acc_type}"
        acc_obj = bpy.data.objects.get(acc_name)
        if acc_obj:
            if acc.level == 'MAIN':
                acc_z = base_h
            elif acc.level == 'CASTLE':
                has_castle = (props.section_type == 'STERN' and props.has_quarterdeck) or (props.section_type == 'BOW' and props.has_forecastle)
                acc_z = base_h + (props.deck_elevation * race_scale) if has_castle else base_h
            else: # BODEGA
                acc_z = ft
                
            acc_obj.location = (
                obj.location.x + acc.offset_x,
                obj.location.y + acc.offset_y,
                obj.location.z + acc_z
            )
            acc_obj.rotation_euler = (0, 0, math.radians(acc.rotation_z))

def ensure_cutter(obj, props, l2, bot_w2, mid_w2, top_w2, mid_h, h, base_h):
    def apply_modifier_safely(target_obj, mod_name):
        mod = target_obj.modifiers.get(mod_name)
        if not mod: return
        depsgraph = bpy.context.evaluated_depsgraph_get()
        depsgraph.update()
        target_eval = target_obj.evaluated_get(depsgraph)
        mesh_eval = target_eval.to_mesh()
        
        if len(mesh_eval.vertices) == 0:
            # EXACT solver collapsed and deleted the mesh!
            # We ABORT rather than falling back to FAST, because FAST creates solid poles out of cutters.
            target_eval.to_mesh_clear()
            target_obj.modifiers.remove(mod)
            print(f"Warning: Exact Boolean solver failed on {mod_name}. Aborting cut to prevent solid poles.")
            return
            
        target_obj.modifiers.remove(mod)
        bm_eval = bmesh.new()
        bm_eval.from_mesh(mesh_eval)
        target_obj.data.clear_geometry()
        bm_eval.to_mesh(target_obj.data)
        bm_eval.free()
        target_eval.to_mesh_clear()



    cutter_name = obj.name + "_Cuts"

    cutter_obj = bpy.data.objects.get(cutter_name)

    

    gen_wall = getattr(props, 'generate_plank_cuts', False)
    gen_floor = getattr(props, 'generate_floor_planks', False)
    has_mast = getattr(props, 'has_mast', False)
    has_trapdoor = getattr(props, 'has_trapdoor', False)

    

    if not gen_wall and not gen_floor and not has_mast and not has_trapdoor and len(props.accessories) == 0:
        pass # We no longer return early because we ALWAYS need to generate connector slots!

        

    if not cutter_obj:
        mesh = bpy.data.meshes.new(cutter_name)
        cutter_obj = bpy.data.objects.new(cutter_name, mesh)
        bpy.context.collection.objects.link(cutter_obj)
        cutter_obj.hide_viewport = True
        cutter_obj.hide_render = True
        cutter_obj.display_type = 'WIRE'
        
    cutter_obj.matrix_world = obj.matrix_world.copy()
        
    mod = obj.modifiers.get("PlankCuts")
    if not mod:
        mod = obj.modifiers.new("PlankCuts", 'BOOLEAN')
    mod.operation = 'DIFFERENCE'
    mod.object = cutter_obj
    mod.solver = 'FAST'

        



        

    bm = bmesh.new()

    random.seed(hash(obj.name))

    

    # 1. Wall Planks

    if gen_wall:

        plank_h = getattr(props, 'plank_height', 8.0)

        cut_w = getattr(props, 'plank_cut_width', 1.5)

        lap_depth = getattr(props, 'lapstrake_depth', 1.5)

        cut_depth = lap_depth + 1.0 # Only slightly deeper than the lapstrake step to prevent breaching the inner hull

        density = getattr(props, 'plank_cut_density', 0.3)

        

        num_planks = int(h / plank_h) + 1

        for p in range(num_planks):

            z_start = p * plank_h

            z_end = min((p + 1) * plank_h, h)

            if z_end - z_start < 0.1: continue

            z_c = (z_start + z_end) / 2.0

            

            length = 2 * l2

            expected_cuts = max(0, int((length / 30.0) * density * 2))

            

            for _ in range(expected_cuts):

                y_pos = random.uniform(-l2 + 2.0, l2 - 2.0)

                

                if z_c >= base_h:
                    w_at_z = top_w2
                elif z_c >= mid_h:
                    d_z = base_h - mid_h
                    w_at_z = mid_w2 + (z_c - mid_h) * ((top_w2 - mid_w2) / d_z) if d_z > 0 else top_w2
                else:
                    d_z = mid_h
                    w_at_z = bot_w2 + z_c * ((mid_w2 - bot_w2) / d_z) if d_z > 0 else bot_w2

                    

                if props.section_type == 'MID':

                    x_val = w_at_z

                    angle = 0

                    sc = 1.0

                elif props.section_type == 'BOW':

                    t = (y_pos + l2) / (2 * l2)

                    sc = 1.0 + (0.01 - 1.0) * t

                    x_val = w_at_z * sc

                    dx = w_at_z * 0.01 - w_at_z

                    dy = 2 * l2

                    angle = -math.atan2(dx, dy)

                elif props.section_type == 'STERN':

                    t = (y_pos + l2) / (2 * l2)

                    sc = 0.7 + (1.0 - 0.7) * t

                    x_val = w_at_z * sc

                    dx = w_at_z * 1.0 - w_at_z * 0.7

                    dy = 2 * l2

                    angle = -math.atan2(dx, dy)

                else:

                    x_val = w_at_z

                    angle = 0

                    sc = 1.0

                    

                x_val += lap_depth / 2.0 * sc
                
                if x_val < 3.0:
                    continue  

                ret = bmesh.ops.create_cube(bm, size=1.0)

                bmesh.ops.scale(bm, vec=(cut_depth, cut_w, z_end - z_start + 0.2), verts=ret['verts'])

                if angle != 0:


                    rot = mathutils.Matrix.Rotation(angle, 4, 'Z')

                    bmesh.ops.transform(bm, matrix=rot, verts=ret['verts'])

                bmesh.ops.translate(bm, vec=(x_val, y_pos, z_c), verts=ret['verts'])

                

                ret = bmesh.ops.create_cube(bm, size=1.0)

                bmesh.ops.scale(bm, vec=(cut_depth, cut_w, z_end - z_start + 0.2), verts=ret['verts'])

                if angle != 0:


                    rot = mathutils.Matrix.Rotation(-angle, 4, 'Z')

                    bmesh.ops.transform(bm, matrix=rot, verts=ret['verts'])

                bmesh.ops.translate(bm, vec=(-x_val, y_pos, z_c), verts=ret['verts'])

                

    # 2. Floor Planks

    if gen_floor:
        fp_w = getattr(props, 'floor_plank_width', 10.0)
        fp_l = getattr(props, 'floor_plank_length', 40.0)
        fc_w = 1.0 # 1mm groove width
        
        t = props.wall_thickness
        ft = props.floor_thickness
        dz_lower = mid_h
        dx_lower = mid_w2 - bot_w2
        if dz_lower > 0:
            inner_floor_x = (bot_w2 - t) + ft * (dx_lower / dz_lower)
        else:
            inner_floor_x = bot_w2 - t
            
        scale_front = 1.0
        scale_back = 1.0
        if props.section_type == 'STERN':
            scale_front = 1.0
            scale_back = 0.7
        elif props.section_type == 'BOW':
            scale_front = 0.0
            scale_back = 1.0
            
        num_boards_x = int((bot_w2 * 2.0 * 2.0) / fp_w)
        
        for ix in range(-num_boards_x, num_boards_x + 1):
            x_center = ix * fp_w
            x_line = x_center + fp_w/2.0
            
            max_w2 = inner_floor_x * max(scale_front, scale_back)
            min_w2 = inner_floor_x * min(scale_front, scale_back)
            
            # Vertical cut line along Y
            if abs(x_line) < max_w2 - 1.0:
                y_start_line = -l2
                y_end_line = l2
                if props.section_type == 'STERN':
                    y_start_line = -l2 + t
                elif props.section_type == 'BOW':
                    y_end_line = l2 - t
                if abs(x_line) > min_w2 and scale_front != scale_back:
                    y_cross = (abs(x_line) / inner_floor_x - scale_back) / (scale_front - scale_back) * (2 * l2) - l2
                    if scale_front > scale_back: # STERN
                        y_start_line = y_cross
                    else: # BOW
                        y_end_line = y_cross
                        
                line_len = y_end_line - y_start_line
                if line_len > 1.0:
                    y_center_line = (y_start_line + y_end_line) / 2.0
                    ret = bmesh.ops.create_cube(bm, size=1.0)
                    bmesh.ops.scale(bm, vec=(fc_w, line_len, 0.4), verts=ret['verts'])
                    bmesh.ops.translate(bm, vec=(x_line, y_center_line, props.floor_thickness), verts=ret['verts'])
            
            # Horizontal staggered cuts along X
            y_start = -l2
            if props.section_type == 'STERN':
                y_start = -l2 + t
            while y_start < l2:
                board_len = fp_l * random.uniform(0.6, 1.4)
                y_cut = y_start + board_len
                
                if props.section_type == 'BOW' and y_cut > l2 - t:
                    break
                    
                if y_cut < l2 - 2.0:
                    p_y = (y_cut - (-l2)) / (2 * l2) if l2 > 0 else 0
                    s_y = scale_back + (scale_front - scale_back) * p_y
                    allowed_w2 = inner_floor_x * s_y
                    
                    if abs(x_center) + fp_w/2.0 <= allowed_w2 - 1.0:
                        ret = bmesh.ops.create_cube(bm, size=1.0)
                        bmesh.ops.scale(bm, vec=(fp_w - fc_w - 0.05, fc_w, 0.4), verts=ret['verts'])
                        bmesh.ops.translate(bm, vec=(x_center, y_cut, props.floor_thickness), verts=ret['verts'])
                y_start = y_cut

                

    ft = props.floor_thickness

    mast_td_z = ft

    deck_z = h - 2.0 if props.generate_top_deck else h

    if props.generate_top_deck:

        mast_td_z = deck_z



    if getattr(props, 'has_mast', False) and not props.generate_top_deck:
        sock_h = getattr(props, 'mast_socket_height', 15.0)
        sock_d = getattr(props, 'mast_diameter', 8.0)
        y_off = getattr(props, 'mast_y_offset', 0.0)
        
        # Cutter for the mast hole. Should only go down to the deck floor (mast_td_z)
        cut_h = sock_h + 4.0 # Cuts through the socket and slightly into the floor
        ret = bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=32, radius1=sock_d/2.0, radius2=sock_d/2.0, depth=cut_h)
        # Center of the cutter so that its bottom is at mast_td_z - 2.0
        center_z = (mast_td_z - 2.0) + (cut_h / 2.0)
        bmesh.ops.translate(bm, vec=(0, y_off, center_z), verts=ret['verts'])

    for acc in props.accessories:
        if acc.level == 'BODEGA' or (acc.level in ('MAIN', 'CASTLE') and not props.generate_top_deck):
            cut_h = acc.snap_depth + 4.0
            ret = bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=16, radius1=acc.snap_radius, radius2=acc.snap_radius, depth=cut_h)
            center_z = ft - (cut_h / 2.0) + 2.0 # Ensure it starts at floor and goes down
            bmesh.ops.translate(bm, vec=(acc.offset_x, acc.offset_y, center_z), verts=ret['verts'])

    if getattr(props, 'has_trapdoor', False) and not props.generate_top_deck:
        td_size = getattr(props, 'trapdoor_size', 1.0) * 25.4 # Convert squares to mm
        y_off = getattr(props, 'trapdoor_y_offset', 0.0)
        
        # Cube for trapdoor hole. Needs to penetrate perfectly.
        ret = bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=(td_size, td_size, props.floor_thickness + 2.0), verts=ret['verts'])
        # Center of the cutter matches the center of the lid
        bmesh.ops.translate(bm, vec=(0, y_off, mast_td_z + props.floor_thickness / 2.0), verts=ret['verts'])

    if getattr(props, 'generate_stairs', False) and props.generate_top_deck:
        needs_hull_stair_cut = False
        if props.section_type == 'STERN' and getattr(props, 'has_quarterdeck', False):
            needs_hull_stair_cut = True
        elif props.section_type == 'BOW' and getattr(props, 'has_forecastle', False):
            needs_hull_stair_cut = True
            
        if needs_hull_stair_cut:
            t_wall = props.wall_thickness
            for stair in props.stairs:
                # Do not cut the castle wall if the stair is from the hold
                if getattr(stair, 'level', 'BODEGA_MAIN') == 'BODEGA_MAIN':
                    continue
                    
                off_y = getattr(stair, 'offset_y', 0.0)
                # Only cut the wall if the stair actually touches/intersects the wall
                if abs(off_y) >= t_wall:
                    continue
                
                race_scale = 1.0
                if hasattr(props, 'creator_race'):
                    if props.creator_race == 'HALFLING': race_scale = 0.75
                    elif props.creator_race == 'GIANT': race_scale = 1.5
                    elif props.creator_race == 'TITAN': race_scale = 2.0
                    
                s_width = getattr(stair, 'width', 20.0) * race_scale
                off_x = getattr(stair, 'offset_x', 0.0)
                rot_z = getattr(stair, 'rotation_z', 0.0)
                
                tol = getattr(props, 'tolerance', 0.2)
                hole_len = t_wall + 2.0 # Keep this to fully penetrate the wall
                hole_w = s_width + (tol * 2.0)
                hole_h = h - base_h + 4.0
                
                if props.section_type == 'STERN':
                    cy = l2 - t_wall / 2.0
                else:
                    cy = -l2 + t_wall / 2.0
                    
                cx = off_x
                cz = base_h + (h - base_h) / 2.0
                
                ret = bmesh.ops.create_cube(bm, size=1.0)
                bmesh.ops.scale(bm, vec=(hole_w, hole_len, hole_h), verts=ret['verts'])
                if rot_z != 0.0:
                    rot_mat = mathutils.Matrix.Rotation(math.radians(rot_z), 4, 'Z')
                    bmesh.ops.transform(bm, matrix=rot_mat, verts=ret['verts'])
                bmesh.ops.translate(bm, vec=(cx, cy, cz), verts=ret['verts'])





















    # 4. Connector Slots
    peg_l2 = 10.0
    slot_verts = [
        (-2.6667, -0.5, 0),
        (-5.3333, 3.5, 0),
        (5.3333, 3.5, 0),
        (2.6667, -0.5, 0)
    ]
    def add_continuous_slot_cutter():
        if not props.generate_connector_slot:
            return
            
        if props.section_type == 'MID':
            y_back = -l2 - 0.1
            y_front = l2 + 0.1
        elif props.section_type == 'BOW':
            y_back = -l2 - 0.1
            y_front = 0.123
        elif props.section_type == 'STERN':
            y_back = -l2 - 0.1
            y_front = l2 + 0.1
        else:
            return
            
        slot_cutter_name = obj.name + "_SlotCuts"
        slot_cutter_obj = bpy.data.objects.get(slot_cutter_name)
        if not slot_cutter_obj:
            slot_mesh = bpy.data.meshes.new(slot_cutter_name)
            slot_cutter_obj = bpy.data.objects.new(slot_cutter_name, slot_mesh)
            bpy.context.collection.objects.link(slot_cutter_obj)
            slot_cutter_obj.hide_viewport = True
            slot_cutter_obj.hide_render = True
            
        slot_cutter_obj.matrix_world = obj.matrix_world.copy()
            
        bm_slot = bmesh.new()
            
        p_back = [bm_slot.verts.new((c[0], y_back, c[1])) for c in slot_verts]
        p_front = [bm_slot.verts.new((c[0], y_front, c[1])) for c in slot_verts]
        
        bm_slot.faces.new((p_back[0], p_back[3], p_back[2], p_back[1])) # CW -> Outwards (-Y)
        bm_slot.faces.new((p_front[0], p_front[1], p_front[2], p_front[3])) # CCW -> Outwards (+Y)
        for i in range(4):
            bm_slot.faces.new((p_back[i], p_back[(i+1)%4], p_front[(i+1)%4], p_front[i]))
            
        bm_slot.to_mesh(slot_cutter_obj.data)
        bm_slot.free()
        
        mod = obj.modifiers.get("SlotCuts")
        if not mod:
            mod = obj.modifiers.new("SlotCuts", 'BOOLEAN')
        mod.operation = 'DIFFERENCE'
        mod.object = slot_cutter_obj
        mod.solver = 'EXACT'
        if hasattr(mod, 'use_hole_tolerant'): mod.use_hole_tolerant = True

    add_continuous_slot_cutter()
        
    # The geometry is now fully manifold and cutter depths have been adjusted.
    # We NO LONGER apply a microscopic offset/rotation, as near-misses actually crash the EXACT solver in Blender 3.0.
    
    bm.to_mesh(cutter_obj.data)
    bm.free()
    
    apply_modifier_safely(obj, "PlankCuts")
    apply_modifier_safely(obj, "SlotCuts")
    
    deck_obj = bpy.data.objects.get(obj.name + "_Deck")
    if deck_obj:
        apply_modifier_safely(deck_obj, "DeckCuts")
        
    # CRITICAL CLEANUP: Now that the modifiers are applied and the geometry is baked,
    # the cutter objects are no longer needed. We MUST delete them so they don't 
    # linger in the scene as solid meshes, which causes them to be exported to STL 
    # and occasionally appear in the viewport.
    if cutter_obj:
        bpy.data.objects.remove(cutter_obj, do_unlink=True)
        
    slot_cutter_name = obj.name + "_SlotCuts"
    slot_cutter_obj = bpy.data.objects.get(slot_cutter_name)
    if slot_cutter_obj:
        bpy.data.objects.remove(slot_cutter_obj, do_unlink=True)
        
    # deck_cutter_obj might not be in local scope if it wasn't generated this frame,
    # so we fetch it by name to be absolutely sure we delete it if it exists.
    deck_cutter_name = obj.name + "_DeckCuts"
    deck_cutter_obj = bpy.data.objects.get(deck_cutter_name)
    if deck_cutter_obj:
        bpy.data.objects.remove(deck_cutter_obj, do_unlink=True)
    




