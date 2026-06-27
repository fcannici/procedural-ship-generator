import bpy
import bmesh
import math
import mathutils
import random

def create_grid(bm, x_min, x_max, y_min, y_max, z, grid_size=25.4, depth=0.5, width=1.0):
    # This function will sculpt the 1x1 grid lines on the floor
    pass

def build_hull(bm, props):
    """
    Builds the main hull base
    """
    pass

def rebuild_ship_mesh(obj):
    print("START REBUILD")
    if not obj or obj.type != 'MESH':
        return
        
    props = obj.ship_generator
    if not props.is_ship and not props.is_connector_clip:
        return
        
    if bpy.context.object and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
        
    bm = bmesh.new()
    
    if props.is_connector_clip:
        tol = props.tolerance
        peg_l2 = 10.0 # 20mm length
        p_verts = [
            (-3.0 + tol, 0, 0),
            (-5.0 + tol, 3.0 - tol, 0),
            (5.0 - tol, 3.0 - tol, 0),
            (3.0 - tol, 0, 0)
        ]
        p_back = [bm.verts.new((c[0], -peg_l2, c[1])) for c in p_verts]
        p_front = [bm.verts.new((c[0], peg_l2, c[1])) for c in p_verts]
        
        bm.faces.new((p_back[0], p_back[3], p_back[2], p_back[1])) # CW
        bm.faces.new((p_front[0], p_front[1], p_front[2], p_front[3])) # CCW
        
        for i in range(4):
            bm.faces.new((p_back[i], p_front[i], p_front[(i+1)%4], p_back[(i+1)%4]))
            
        bm.normal_update()
        bm.to_mesh(obj.data)
        bm.free()
        return

    grid_size = 25.4
    l2 = (props.tiles_length * grid_size) / 2.0
    base_h = props.wall_height
    h = base_h
    t = props.wall_thickness
    ft = props.floor_thickness
    
    if props.section_type == 'STERN' and props.has_quarterdeck:
        h += props.deck_elevation
        ft += props.deck_elevation
    elif props.section_type == 'BOW' and props.has_forecastle:
        h += props.deck_elevation
        ft += props.deck_elevation
    
    bot_w2 = (props.tiles_width * grid_size) / 2.0 + t
    w2 = bot_w2 * 2.0
    
    mid_w2 = w2 * 0.8
    mid_h = base_h * 0.4
    tol = props.tolerance
    
    # Calculate top widths to maintain perfectly collinear slopes with the base hull
    dz = base_h - mid_h
    if dz > 0:
        dx = w2 - mid_w2
        top_w2 = mid_w2 + (h - mid_h) * (dx / dz)
    else:
        top_w2 = w2

    plank_h = props.plank_height
    lapstrake_depth = props.lapstrake_depth
    
    def generate_outer_profile(bw, mw, tw, bz, mz, tz):
        pts = []
        
        # Bottom section: from bz to mz
        z_current = bz
        while z_current < mz - 0.001:
            z_next = min(z_current + plank_h, mz)
            
            p0 = (z_current - bz) / (mz - bz) if mz > bz else 0
            p1 = (z_next - bz) / (mz - bz) if mz > bz else 0
            
            x0 = bw + (mw - bw) * p0
            x1 = bw + (mw - bw) * p1
            
            pts.append((x0, z_current))
            pts.append((x1 + lapstrake_depth, z_next))
            
            z_current = z_next

        # Top section: from mz to tz
        z_current = mz
        while z_current < tz - 0.001:
            z_next = min(z_current + plank_h, tz)
            
            p0 = (z_current - mz) / (tz - mz) if tz > mz else 0
            p1 = (z_next - mz) / (tz - mz) if tz > mz else 0
            
            x0 = mw + (tw - mw) * p0
            x1 = mw + (tw - mw) * p1
            
            pts.append((x0, z_current))
            pts.append((x1 + lapstrake_depth, z_next))
            
            z_current = z_next
            
        return pts

    outer_right_profile = generate_outer_profile(bot_w2, mid_w2, top_w2, 0, mid_h, h)
    
    outer_left = [(-p[0], p[1], 0) for p in reversed(outer_right_profile)]
    
    floor_bottom = [
        (-bot_w2, 0, 0),
        (bot_w2, 0, 0)
    ]
    
    outer_right = [(p[0], p[1], 0) for p in outer_right_profile]
    
    # Calculate intersection of the floor with the inner hull
    if ft >= mid_h:
        dz_upper = h - mid_h
        dx_upper = top_w2 - mid_w2
        if dz_upper > 0:
            inner_floor_x = (mid_w2 - t) + (ft - mid_h) * (dx_upper / dz_upper)
        else:
            inner_floor_x = top_w2 - t
    else:
        dz_lower = mid_h
        dx_lower = mid_w2 - bot_w2
        if dz_lower > 0:
            inner_floor_x = (bot_w2 - t) + ft * (dx_lower / dz_lower)
        else:
            inner_floor_x = bot_w2 - t
            
    inner_right = []
    for p in reversed(outer_right_profile):
        z = p[1]
        if z <= ft:
            continue
            
        if z >= mid_h:
            dz_upper = h - mid_h
            dx_upper = top_w2 - mid_w2
            if dz_upper > 0:
                ix = (mid_w2 - t) + (z - mid_h) * (dx_upper / dz_upper)
            else:
                ix = top_w2 - t
        else:
            dz_lower = mid_h
            dx_lower = mid_w2 - bot_w2
            if dz_lower > 0:
                ix = (bot_w2 - t) + z * (dx_lower / dz_lower)
            else:
                ix = bot_w2 - t
                
        inner_right.append((ix, z, 0))
        
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
        
        # Manual quad caps for walls to prevent triangulator tearing on deep lapstrake zigzags
        M = len_outer_left + 1 # Number of vertices in outer_right_profile
        K = len_inner_right - 1 # Number of corresponding valid inner vertices above the floor
        
        for i in range(M - 1):
            # Left Wall indices
            o1_idx = i
            o2_idx = i + 1
            i1_local = max(0, K - i)
            i2_local = max(0, K - (i + 1))
            i1_idx = idx_inner_left + i1_local
            i2_idx = idx_inner_left + i2_local
            
            if i1_local == i2_local:
                # Back (CW)
                bm.faces.new((segments[0][o1_idx], segments[0][i1_idx], segments[0][o2_idx]))
                # Front (CCW)
                bm.faces.new((segments[-1][o1_idx], segments[-1][o2_idx], segments[-1][i1_idx]))
            else:
                # Back (CW)
                bm.faces.new((segments[0][o1_idx], segments[0][i1_idx], segments[0][i2_idx], segments[0][o2_idx]))
                # Front (CCW)
                bm.faces.new((segments[-1][o1_idx], segments[-1][o2_idx], segments[-1][i2_idx], segments[-1][i1_idx]))
            
            # Right Wall indices
            ro1_idx = idx_outer_right + i
            ro2_idx = idx_outer_right + i + 1
            ri1_local = M - 1 - i if i >= M - K else K
            ri2_local = M - 1 - (i + 1) if (i + 1) >= M - K else K
            ri1_idx = idx_inner_right + ri1_local
            ri2_idx = idx_inner_right + ri2_local
            
            if ri1_local == ri2_local:
                # Back (CW)
                bm.faces.new((segments[0][ro1_idx], segments[0][ri1_idx], segments[0][ro2_idx]))
                # Front (CCW)
                bm.faces.new((segments[-1][ro1_idx], segments[-1][ro2_idx], segments[-1][ri1_idx]))
            else:
                # Back (CW)
                bm.faces.new((segments[0][ro1_idx], segments[0][ri1_idx], segments[0][ri2_idx], segments[0][ro2_idx]))
                # Front (CCW)
                bm.faces.new((segments[-1][ro1_idx], segments[-1][ro2_idx], segments[-1][ri2_idx], segments[-1][ri1_idx]))

        # === Solid Plugs to Close the Ship's Interior ===
        plug_coords = [verts_coords[i] for i in range(idx_inner_right, len(verts_coords))]
        
        def add_solid_plug(y_back, y_front):
            p_prog_b = (y_back - (-l2)) / (2 * l2) if l2 > 0 else 0
            p_prog_f = (y_front - (-l2)) / (2 * l2) if l2 > 0 else 0
            s_b = scale_back + (scale_front - scale_back) * p_prog_b
            s_f = scale_back + (scale_front - scale_back) * p_prog_f
            
            pb_verts = []
            for c in plug_coords:
                x = c[0] * s_b
                z = c[1]
                if x > 0.1: x += 0.1
                elif x < -0.1: x -= 0.1
                if z < props.floor_thickness + 0.1: z -= 0.1
                pb_verts.append(bm.verts.new((x, y_back, z)))
            
            pf_verts = []
            for c in plug_coords:
                x = c[0] * s_f
                z = c[1]
                if x > 0.1: x += 0.1
                elif x < -0.1: x -= 0.1
                if z < props.floor_thickness + 0.1: z -= 0.1
                pf_verts.append(bm.verts.new((x, y_front, z)))
            
            f_pb = bm.faces.new(pb_verts[::-1]) # CW
            f_pf = bm.faces.new(pf_verts)       # CCW
            bmesh.ops.triangulate(bm, faces=[f_pb, f_pf])
            
            for i in range(len(plug_coords)):
                bm.faces.new((pb_verts[i], pb_verts[(i+1)%len(plug_coords)], pf_verts[(i+1)%len(plug_coords)], pf_verts[i]))
        
        if props.section_type == 'STERN':
            add_solid_plug(-l2, -l2 + props.wall_thickness) # Transom plug
            if props.has_quarterdeck:
                add_solid_plug(l2 - props.wall_thickness, l2) # Front wall facing MID
        elif props.section_type == 'BOW':
            add_solid_plug(l2 - props.wall_thickness, l2) # Tip plug
            if props.has_forecastle:
                add_solid_plug(-l2, -l2 + props.wall_thickness) # Back wall facing MID
                
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
                    allowed_w2_start = inner_floor_x * (1.0 - progress_start)
                    allowed_w2_end = inner_floor_x * (1.0 - progress_end)
                    allowed_w2 = min(allowed_w2_start, allowed_w2_end)
                elif props.section_type == 'STERN':
                    progress_start = (valid_ty1 - (-l2)) / (2*l2)
                    progress_end = (valid_ty2 - (-l2)) / (2*l2)
                    allowed_w2_start = inner_floor_x * (0.7 + 0.3 * progress_start)
                    allowed_w2_end = inner_floor_x * (0.7 + 0.3 * progress_end)
                    allowed_w2 = min(allowed_w2_start, allowed_w2_end)
                else:
                    allowed_w2 = inner_floor_x
                    
                valid_tx1 = max(tx1, -allowed_w2 + groove_width)
                valid_tx2 = min(tx2, allowed_w2 - groove_width)
                
                if valid_tx1 >= valid_tx2:
                    continue
                    
                plank_gap = 0.4
                total_w = valid_tx2 - valid_tx1
                
                if total_w <= 0:
                    continue
                    
                num_main_planks = 2
                pw = total_w / num_main_planks
                planks = []
                
                if iy % 2 == 0:
                    for p in range(num_main_planks):
                        px1 = valid_tx1 + p * pw
                        px2 = valid_tx1 + (p + 1) * pw - plank_gap
                        planks.append((px1, px2))
                else:
                    px1 = valid_tx1
                    px2 = valid_tx1 + pw / 2 - plank_gap
                    planks.append((px1, px2))
                    for p in range(num_main_planks - 1):
                        px1 = valid_tx1 + pw / 2 + p * pw
                        px2 = valid_tx1 + pw / 2 + (p + 1) * pw - plank_gap
                        planks.append((px1, px2))
                    px1 = valid_tx1 + pw / 2 + (num_main_planks - 1) * pw
                    px2 = valid_tx2 - plank_gap
                    planks.append((px1, px2))
                
                for px1, px2 in planks:
                    if px2 <= px1: continue
                    
                    v1 = bm.verts.new((px1, valid_ty1, ft - 0.2))
                    v2 = bm.verts.new((px2, valid_ty1, ft - 0.2))
                    v3 = bm.verts.new((px2, valid_ty2, ft - 0.2))
                    v4 = bm.verts.new((px1, valid_ty2, ft - 0.2))
                    f_tile = bm.faces.new((v1, v2, v3, v4))
                    
                    geom = bmesh.ops.extrude_face_region(bm, geom=[f_tile])
                    extruded_verts = [v for v in geom['geom'] if isinstance(v, bmesh.types.BMVert)]
                    bmesh.ops.translate(bm, vec=(0, 0, tile_height + 0.2), verts=extruded_verts)

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
        deck_w2 = (top_w2 - t) - tol
        
        deck_start_y = -l2
        deck_end_y = l2
        scale_front_deck = 1.0
        scale_back_deck = 1.0
        
        if props.section_type == 'BOW':
            scale_front_deck = 0.01
        elif props.section_type == 'STERN':
            scale_front_deck = 1.0
            scale_back_deck = 0.7
            
        deck_y_segments = max(1, int((deck_end_y - deck_start_y) / 25.4))
        seg_len = (deck_end_y - deck_start_y) / deck_y_segments
        
        num_deck_planks = 4
        plank_gap = 0.5
        pw = (deck_w2 * 2) / num_deck_planks
        
        for iy in range(deck_y_segments):
            sy1 = deck_start_y + iy * seg_len + 0.2
            sy2 = deck_start_y + (iy + 1) * seg_len - 0.2
            
            planks = []
            if iy % 2 == 0:
                for p in range(num_deck_planks):
                    px1 = -deck_w2 + p * pw
                    px2 = -deck_w2 + (p + 1) * pw - plank_gap
                    planks.append((px1, px2))
            else:
                px1 = -deck_w2
                px2 = -deck_w2 + pw / 2 - plank_gap
                planks.append((px1, px2))
                for p in range(num_deck_planks - 1):
                    px1 = -deck_w2 + pw / 2 + p * pw
                    px2 = -deck_w2 + pw / 2 + (p + 1) * pw - plank_gap
                    planks.append((px1, px2))
                px1 = -deck_w2 + pw / 2 + (num_deck_planks - 1) * pw
                px2 = deck_w2 - plank_gap
                planks.append((px1, px2))
            
            for px1, px2 in planks:
                if px2 <= px1: continue
                
                d_verts = [
                    (px1, deck_z, 0),
                    (px2, deck_z, 0),
                    (px2, deck_z + deck_thickness, 0),
                    (px1, deck_z + deck_thickness, 0)
                ]
                
                if props.section_type == 'STERN':
                    p_sy1 = (sy1 - (-l2)) / (2*l2)
                    p_sy2 = (sy2 - (-l2)) / (2*l2)
                    sc1 = scale_back_deck + (scale_front_deck - scale_back_deck) * p_sy1
                    sc2 = scale_back_deck + (scale_front_deck - scale_back_deck) * p_sy2
                elif props.section_type == 'BOW':
                    p_sy1 = (sy1 - (-l2)) / (2*l2)
                    p_sy2 = (sy2 - (-l2)) / (2*l2)
                    sc1 = scale_back_deck + (scale_front_deck - scale_back_deck) * p_sy1
                    sc2 = scale_back_deck + (scale_front_deck - scale_back_deck) * p_sy2
                else:
                    sc1 = 1.0
                    sc2 = 1.0
                
                d_back = [bm_deck.verts.new((c[0] * sc1, sy1, c[1])) for c in d_verts]
                d_front = [bm_deck.verts.new((c[0] * sc2, sy2, c[1])) for c in d_verts]
                
                bm_deck.faces.new((d_back[0], d_back[3], d_back[2], d_back[1])) # CW
                bm_deck.faces.new((d_front[0], d_front[1], d_front[2], d_front[3])) # CCW
                
                for i in range(4):
                    bm_deck.faces.new((d_back[i], d_back[(i+1)%4], d_front[(i+1)%4], d_front[i]))
                    
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

    bm.normal_update()
    bm.to_mesh(obj.data)
    bm.free()
    
    # --- Separate Deck Cutter ---
    deck_cutter_name = obj.name + "_DeckCuts"
    deck_cutter_obj = bpy.data.objects.get(deck_cutter_name)
    
    needs_deck_cuts = False
    if props.generate_top_deck:
        if getattr(props, 'generate_stairs', False) and props.section_type in ['STERN', 'BOW']:
            needs_deck_cuts = True
        if getattr(props, 'has_trapdoor', False) or getattr(props, 'has_mast', False):
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
        
        if getattr(props, 'generate_stairs', False) and props.section_type in ['STERN', 'BOW']:
            y_start = l2 if props.section_type == 'STERN' else -l2
            s_width = getattr(props, 'stairs_width', 20.0)
            s_length = getattr(props, 'stairs_length', 40.0)
            off_x = getattr(props, 'stairs_offset_x', 0.0)
            off_y = getattr(props, 'stairs_offset_y', 0.0)
            y_dir = -1.0 if props.section_type == 'STERN' else 1.0
            
            hole_len = s_length + 2.0
            hole_w = s_width + 2.0
            hole_h = 6.0 
            
            cy = y_start + (off_y * y_dir) + (s_length / 2.0 * y_dir)
            cx = off_x
            cz = h - 1.0
            
            ret = bmesh.ops.create_cube(bm_deck_cutter, size=1.0)
            bmesh.ops.scale(bm_deck_cutter, vec=(hole_w, hole_len, hole_h), verts=ret['verts'])
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
    else:
        if deck_cutter_obj:
            bpy.data.objects.remove(deck_cutter_obj, do_unlink=True)
        deck_obj = bpy.data.objects.get(obj.name + "_Deck")
        if deck_obj:
            mod_deck = deck_obj.modifiers.get("DeckCuts")
            if mod_deck:
                deck_obj.modifiers.remove(mod_deck)
    # ----------------------------

    ensure_cutter(obj, props, l2, bot_w2, mid_w2, top_w2, mid_h, h)

    # Post-boolean additions: Railings and Mast (placed in a separate object to avoid exact solver bugs)
    rail_name = obj.name + "_Accesorios"
    rail_obj = bpy.data.objects.get(rail_name)
    
    if getattr(props, 'generate_railings', False) or getattr(props, 'has_mast', False):
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
            if props.section_type in ['STERN', 'BOW']:
                y_start = l2 if props.section_type == 'STERN' else -l2
                
                s_width = getattr(props, 'stairs_width', 20.0)
                stair_w2 = s_width / 2.0
                
                s_length = getattr(props, 'stairs_length', 40.0)
                
                off_x = getattr(props, 'stairs_offset_x', 0.0)
                off_y = getattr(props, 'stairs_offset_y', 0.0)
                
                step_height = 5.0
                
                # Stairs from Bodega (ft) to Main Deck (h)
                # Note: We go up to 'h' so it reaches the top surface of the deck without a gap.
                target_z = h
                elev_lower = target_z - ft
                if elev_lower > 0:
                    num_steps = int(math.ceil(elev_lower / step_height))
                    step_depth = s_length / float(num_steps)
                    
                    y_dir = -1.0 if props.section_type == 'STERN' else 1.0
                    
                    for i in range(num_steps):
                        z0 = ft + i * step_height
                        z1 = ft + (i + 1) * step_height
                        if i == num_steps - 1:
                            z1 = target_z # Ensure exact match on last step
                        
                        dist = num_steps - 1 - i
                        y0 = y_start + dist * step_depth * y_dir + (off_y * y_dir)
                        y1 = y_start + (dist + 1) * step_depth * y_dir + (off_y * y_dir)
                        
                        x0 = -stair_w2 + off_x
                        x1 = stair_w2 + off_x
                        
                        sv = [
                            bm_final.verts.new((x0, y0, z0)),
                            bm_final.verts.new((x1, y0, z0)),
                            bm_final.verts.new((x1, y0, z1)),
                            bm_final.verts.new((x0, y0, z1)),
                            bm_final.verts.new((x0, y1, z0)),
                            bm_final.verts.new((x1, y1, z0)),
                            bm_final.verts.new((x1, y1, z1)),
                            bm_final.verts.new((x0, y1, z1))
                        ]
                        
                        bm_final.faces.new((sv[0], sv[3], sv[2], sv[1]))
                        bm_final.faces.new((sv[4], sv[5], sv[6], sv[7]))
                        bm_final.faces.new((sv[0], sv[1], sv[5], sv[4]))
                        bm_final.faces.new((sv[3], sv[7], sv[6], sv[2]))
                        bm_final.faces.new((sv[0], sv[4], sv[7], sv[3]))
                        bm_final.faces.new((sv[1], sv[2], sv[6], sv[5]))



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
    
            # Center the railing exactly on the top wall edge
            x_bl = -top_w2 * sc_back - 0.15
            x_fl = -top_w2 * sc_front - 0.15
            x_br = top_w2 * sc_back + 0.15
            x_fr = top_w2 * sc_front + 0.15
            
            y_fl = l2
            y_fr = l2
            
            if x_fl > 0 and x_bl < 0:
                t = (0 - x_bl) / (x_fl - x_bl)
                y_fl = -l2 + t * (2 * l2)
                x_fl = 0.0
                
            if x_fr < 0 and x_br > 0:
                t = (0 - x_br) / (x_fr - x_br)
                y_fr = -l2 + t * (2 * l2)
                x_fr = 0.0
            
            # Center the back railing on the back wall (thickness = 1.2, center = 0.6)
            trim_s = 0.6 if props.section_type == 'STERN' else 0.0
            trim_e = 0.0
            
            if props.section_type == 'BOW':
                # Add a capping post at the tip
                ret = bmesh.ops.create_cube(bm_final, size=1.0)
                bmesh.ops.scale(bm_final, vec=(rt, rt, rh), verts=ret['verts'])
                bmesh.ops.translate(bm_final, vec=(0, l2, h + rh/2.0), verts=ret['verts'])
                
                # Trim the side railings so their handrails end exactly inside the post
                # The handrail extends rt/2 past the end point, so we trim by rt/2
                trim_e = rt / 2.0
            
            add_railing_line(bm_final, x_bl, -l2, x_fl, y_fl, h, trim_start=trim_s, trim_end=trim_e)
            add_railing_line(bm_final, x_br, -l2, x_fr, y_fr, h, trim_start=trim_s, trim_end=trim_e)
            if props.section_type == 'STERN':
                add_railing_line(bm_final, x_br, -l2 + 0.6, x_bl, -l2 + 0.6, h, is_back=True)
                
        if getattr(props, 'has_mast', False):
            sock_h = getattr(props, 'mast_socket_height', 15.0)
            sock_d = getattr(props, 'mast_diameter', 8.0) + 6.0
            y_off = getattr(props, 'mast_y_offset', 0.0)
            ret = bmesh.ops.create_cone(bm_final, cap_ends=True, cap_tris=False, segments=32, radius1=sock_d/2.0, radius2=sock_d/2.0, depth=sock_h)
            bmesh.ops.translate(bm_final, vec=(0, y_off, mast_td_z + sock_h/2.0), verts=ret['verts'])
            
        bm_final.normal_update()
        rail_obj.data.clear_geometry()
        bm_final.to_mesh(rail_obj.data)
        bm_final.free()
    else:
        if rail_obj:
            bpy.data.objects.remove(rail_obj, do_unlink=True)

def ensure_cutter(obj, props, l2, bot_w2, mid_w2, top_w2, mid_h, h):
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

    

    if not gen_wall and not gen_floor and not has_mast and not has_trapdoor:

        if cutter_obj:

            bpy.data.objects.remove(cutter_obj, do_unlink=True)

            for mod in obj.modifiers:

                if mod.name == "PlankCuts" or mod.name == cutter_name:

                    obj.modifiers.remove(mod)

        return

        

    if not cutter_obj:
        mesh = bpy.data.meshes.new(cutter_name)
        cutter_obj = bpy.data.objects.new(cutter_name, mesh)
        bpy.context.collection.objects.link(cutter_obj)
        cutter_obj.hide_viewport = True
        cutter_obj.hide_render = True
        cutter_obj.display_type = 'WIRE'
        
    mod = obj.modifiers.get("PlankCuts")
    if not mod:
        mod = obj.modifiers.new("PlankCuts", 'BOOLEAN')
    mod.operation = 'DIFFERENCE'
    mod.object = cutter_obj
    mod.solver = 'EXACT'
    if hasattr(mod, 'use_self'): mod.use_self = True
    if hasattr(mod, 'use_hole_tolerant'): mod.use_hole_tolerant = True

        



        

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

                

                if z_c < mid_h:

                    p0 = z_c / mid_h if mid_h > 0 else 0

                    w_at_z = bot_w2 + (mid_w2 - bot_w2) * p0

                else:

                    p0 = (z_c - mid_h) / (h - mid_h) if h > mid_h else 0

                    w_at_z = mid_w2 + (top_w2 - mid_w2) * p0

                    

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
            while y_start < l2:
                board_len = fp_l * random.uniform(0.6, 1.4)
                y_cut = y_start + board_len
                
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
            s_width = getattr(props, 'stairs_width', 20.0)
            off_x = getattr(props, 'stairs_offset_x', 0.0)
            
            # The hull's stair hole ONLY needs to cut the front wall plug (which is `props.wall_thickness` thick)
            # A full-length cutter floating in the hollow hull causes EXACT solver non-manifold errors.
            t_wall = props.wall_thickness
            hole_len = t_wall + 2.0
            hole_w = s_width + 2.0
            hole_h = h - deck_z + 4.0
            
            if props.section_type == 'STERN':
                cy = l2 - t_wall / 2.0
            else:
                cy = -l2 + t_wall / 2.0
                
            cx = off_x
            cz = deck_z + (h - deck_z) / 2.0
            
            ret = bmesh.ops.create_cube(bm, size=1.0)
            bmesh.ops.scale(bm, vec=(hole_w, hole_len, hole_h), verts=ret['verts'])
            bmesh.ops.translate(bm, vec=(cx, cy, cz), verts=ret['verts'])





















    # The geometry is now fully manifold and cutter depths have been adjusted.
    # We NO LONGER apply a microscopic offset/rotation, as near-misses actually crash the EXACT solver in Blender 3.0.
    
    bm.to_mesh(cutter_obj.data)
    bm.free()
    
    apply_modifier_safely(obj, "PlankCuts")
    
    deck_obj = bpy.data.objects.get(obj.name + "_Deck")
    if deck_obj:
        apply_modifier_safely(deck_obj, "DeckCuts")
        
    # CRITICAL CLEANUP: Now that the modifiers are applied and the geometry is baked,
    # the cutter objects are no longer needed. We MUST delete them so they don't 
    # linger in the scene as solid meshes, which causes them to be exported to STL 
    # and occasionally appear in the viewport.
    if cutter_obj:
        bpy.data.objects.remove(cutter_obj, do_unlink=True)
        
    # deck_cutter_obj might not be in local scope if it wasn't generated this frame,
    # so we fetch it by name to be absolutely sure we delete it if it exists.
    deck_cutter_name = obj.name + "_DeckCuts"
    deck_cutter_obj = bpy.data.objects.get(deck_cutter_name)
    if deck_cutter_obj:
        bpy.data.objects.remove(deck_cutter_obj, do_unlink=True)
    

