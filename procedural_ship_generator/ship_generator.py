import bpy
import bmesh
import math
import mathutils

def create_grid(bm, x_min, x_max, y_min, y_max, z, grid_size=25.4, depth=0.5, width=1.0):
    # This function will sculpt the 1x1 grid lines on the floor
    pass

def build_hull(bm, props):
    """
    Builds the main hull base
    """
    pass

def rebuild_ship_mesh(obj):
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
        (-5.0, 0, 0),
        (-3.0, 0, 0),
        (-5.0, 3.0, 0),
        (5.0, 3.0, 0),
        (3.0, 0, 0),
        (5.0, 0, 0),
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
        
    floor_top = [
        (5.0, ft, 0),
        (-5.0, ft, 0)
    ]
    
    verts_coords = outer_left[:-1] + floor_bottom + outer_right[1:] + inner_right + floor_top + inner_left
    
    idx_outer_left = 0
    len_outer_left = len(outer_left) - 1
    
    idx_floor_bot = len_outer_left
    len_floor_bot = len(floor_bottom)
    
    idx_outer_right = idx_floor_bot + len_floor_bot - 1
    
    idx_inner_right = idx_outer_right + len(outer_right)
    len_inner_right = len(inner_right)
    
    idx_floor_top = idx_inner_right + len_inner_right
    len_floor_top = len(floor_top)
    
    idx_inner_left = idx_floor_top + len_floor_top
    len_inner_left = len(inner_left)
    
    left_cap_indices = list(range(0, idx_floor_bot + 1)) + list(range(idx_inner_left, len(verts_coords)))
    right_cap_indices = list(range(idx_outer_right, idx_floor_top))
    floor_cap_indices = list(range(idx_floor_bot, idx_outer_right + 1)) + list(range(idx_inner_right + len_inner_right - 1, idx_inner_left + 1))

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
            
            pb_verts = [bm.verts.new((c[0] * s_b, y_back, c[1])) for c in plug_coords]
            pf_verts = [bm.verts.new((c[0] * s_f, y_front, c[1])) for c in plug_coords]
            
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
        
        deck_z = h + 15.0
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
            mast_td_z = h + 15.0

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

    if props.generate_stairs:
        if (props.section_type == 'STERN' and props.has_quarterdeck) or (props.section_type == 'BOW' and props.has_forecastle):
            # Stair geometry
            elev = props.deck_elevation
            base_z = props.floor_thickness # floor_thickness wasn't raised, wait!
            # ft was raised at the beginning of the function!
            # so base_z = ft - elev
            base_z = ft - elev
            stair_w2 = inner_floor_x * 0.4 # width of the stairs (40% of inner floor)
            step_height = 5.0
            step_depth = 8.0
            num_steps = int(math.ceil(elev / step_height))
            
            y_dir = 1.0 if props.section_type == 'STERN' else -1.0
            y_start = l2 if props.section_type == 'STERN' else -l2
            
            for i in range(num_steps):
                z0 = base_z + i * step_height
                z1 = min(base_z + (i + 1) * step_height, ft)
                
                y0 = y_start + (i * step_depth) * y_dir
                y1 = y_start + ((i + 1) * step_depth) * y_dir
                
                s_verts = [
                    (-stair_w2, z0, y0),
                    (stair_w2, z0, y0),
                    (stair_w2, z1, y0),
                    (-stair_w2, z1, y0),
                    (-stair_w2, z0, y1),
                    (stair_w2, z0, y1),
                    (stair_w2, z1, y1),
                    (-stair_w2, z1, y1)
                ]
                
                sv = [bm.verts.new((v[0], v[2], v[1])) for v in s_verts] # Y and Z are swapped in coordinates tuple! Wait, the tuple is (X, Z, Y) in my list above, but bm.verts.new takes (X, Y, Z). Let's fix that.
                
                # Correction:
                sv = [
                    bm.verts.new((-stair_w2, y0, z0)),
                    bm.verts.new((stair_w2, y0, z0)),
                    bm.verts.new((stair_w2, y0, z1)),
                    bm.verts.new((-stair_w2, y0, z1)),
                    bm.verts.new((-stair_w2, y1, z0)),
                    bm.verts.new((stair_w2, y1, z0)),
                    bm.verts.new((stair_w2, y1, z1)),
                    bm.verts.new((-stair_w2, y1, z1))
                ]
                
                bm.faces.new((sv[0], sv[3], sv[2], sv[1])) # Front
                bm.faces.new((sv[4], sv[5], sv[6], sv[7])) # Back
                bm.faces.new((sv[0], sv[1], sv[5], sv[4])) # Bottom
                bm.faces.new((sv[3], sv[7], sv[6], sv[2])) # Top
                bm.faces.new((sv[0], sv[4], sv[7], sv[3])) # Left
                bm.faces.new((sv[1], sv[2], sv[6], sv[5])) # Right

    mast_td_bm = bm
    mast_td_z = ft
    
    if props.generate_top_deck:
        mast_td_bm = bm_deck
        mast_td_z = deck_z

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
            
        def add_railing_line(bm, x1, y1, x2, y2, z, is_back=False):
            import math
            import bmesh
            import mathutils
            length = math.hypot(x2 - x1, y2 - y1)
            if length < 0.1: return
            
            num_posts = max(1, int(round(length / rs)))
            angle = math.atan2(y2 - y1, x2 - x1)
            
            # Handrail
            ret = bmesh.ops.create_cube(bm, size=1.0)
            bmesh.ops.scale(bm, vec=(length + rt, rt, rt), verts=ret['verts'])
            rot = mathutils.Matrix.Rotation(angle, 4, 'Z')
            bmesh.ops.transform(bm, matrix=rot, verts=ret['verts'])
            bmesh.ops.translate(bm, vec=((x1+x2)/2.0, (y1+y2)/2.0, z + rh - rt/2.0), verts=ret['verts'])
            
            # Posts
            for i in range(num_posts + 1):
                t = i / num_posts
                px = x1 + (x2 - x1) * t
                py = y1 + (y2 - y1) * t
                
                ret = bmesh.ops.create_cube(bm, size=1.0)
                bmesh.ops.scale(bm, vec=(rt, rt, rh), verts=ret['verts'])
                bmesh.ops.transform(bm, matrix=rot, verts=ret['verts'])
                bmesh.ops.translate(bm, vec=(px, py, z + rh/2.0), verts=ret['verts'])

        inset = rt / 2.0
        x_bl = -top_w2 * sc_back + inset
        x_fl = -top_w2 * sc_front + inset
        x_br = top_w2 * sc_back - inset
        x_fr = top_w2 * sc_front - inset
        
        # Left side
        add_railing_line(mast_td_bm, x_bl, -l2, x_fl, l2, mast_td_z)
        
        # Right side
        add_railing_line(mast_td_bm, x_br, -l2, x_fr, l2, mast_td_z)
        
        # Back side (STERN only)
        if props.section_type == 'STERN':
            add_railing_line(mast_td_bm, x_br, -l2 + inset, x_bl, -l2 + inset, mast_td_z, is_back=True)

    if getattr(props, 'has_mast', False):
        sock_h = getattr(props, 'mast_socket_height', 15.0)
        sock_d = getattr(props, 'mast_diameter', 8.0) + 6.0 # 3mm wall thickness
        y_off = getattr(props, 'mast_y_offset', 0.0)
        
        ret = bmesh.ops.create_cone(mast_td_bm, cap_ends=True, cap_tris=False, segments=32, radius1=sock_d/2.0, radius2=sock_d/2.0, depth=sock_h)
        bmesh.ops.translate(mast_td_bm, vec=(0, y_off, mast_td_z + sock_h/2.0), verts=ret['verts'])

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
    
    ensure_cutter(obj, props, l2, bot_w2, mid_w2, top_w2, mid_h, h)

    import math

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

                if mod.name == "PlankCuts":

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

        

        if props.generate_top_deck:

            deck_obj = bpy.data.objects.get(obj.name + "_Deck")

            if deck_obj:

                mod_deck = deck_obj.modifiers.get("DeckCuts")

                if not mod_deck:

                    mod_deck = deck_obj.modifiers.new("DeckCuts", 'BOOLEAN')

                mod_deck.operation = 'DIFFERENCE'

                mod_deck.object = cutter_obj

                mod_deck.solver = 'EXACT'

        

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

                    angle = math.atan2(dx, dy)

                elif props.section_type == 'STERN':

                    t = (y_pos + l2) / (2 * l2)

                    sc = 0.7 + (1.0 - 0.7) * t

                    x_val = w_at_z * sc

                    dx = w_at_z * 1.0 - w_at_z * 0.7

                    dy = 2 * l2

                    angle = math.atan2(dx, dy)

                else:

                    x_val = w_at_z

                    angle = 0

                    sc = 1.0

                    

                x_val += lap_depth / 2.0 * sc

                    

                ret = bmesh.ops.create_cube(bm, size=1.0)

                bmesh.ops.scale(bm, vec=(cut_depth, cut_w, z_end - z_start + 0.2), verts=ret['verts'])

                if angle != 0:

                    import mathutils

                    rot = mathutils.Matrix.Rotation(angle, 4, 'Z')

                    bmesh.ops.transform(bm, matrix=rot, verts=ret['verts'])

                bmesh.ops.translate(bm, vec=(x_val, y_pos, z_c), verts=ret['verts'])

                

                ret = bmesh.ops.create_cube(bm, size=1.0)

                bmesh.ops.scale(bm, vec=(cut_depth, cut_w, z_end - z_start + 0.2), verts=ret['verts'])

                if angle != 0:

                    import mathutils

                    rot = mathutils.Matrix.Rotation(-angle, 4, 'Z')

                    bmesh.ops.transform(bm, matrix=rot, verts=ret['verts'])

                bmesh.ops.translate(bm, vec=(-x_val, y_pos, z_c), verts=ret['verts'])

                

    # 2. Floor Planks

    if gen_floor:

        fp_w = getattr(props, 'floor_plank_width', 10.0)

        fp_l = getattr(props, 'floor_plank_length', 40.0)

        fc_w = 1.0 # 1mm groove width

        

        # Calculate how many boards fit in the floor width

        num_boards_x = int((bot_w2 * 2.0 * 2.0) / fp_w)

        

        for ix in range(-num_boards_x, num_boards_x + 1):

            x_center = ix * fp_w

            # Vertical cut line along Y

            ret = bmesh.ops.create_cube(bm, size=1.0)

            bmesh.ops.scale(bm, vec=(fc_w, l2 * 2.5, 2.0), verts=ret['verts'])

            bmesh.ops.translate(bm, vec=(x_center + fp_w/2.0, 0, 0), verts=ret['verts'])

            

            # Horizontal staggered cuts along X

            y_start = -l2

            while y_start < l2:

                board_len = fp_l * random.uniform(0.6, 1.4)

                y_cut = y_start + board_len

                if y_cut < l2 - 2.0:

                    ret = bmesh.ops.create_cube(bm, size=1.0)

                    bmesh.ops.scale(bm, vec=(fp_w + 0.2, fc_w, 2.0), verts=ret['verts'])

                    bmesh.ops.translate(bm, vec=(x_center, y_cut, 0), verts=ret['verts'])

                y_start = y_cut

                

    ft = props.floor_thickness

    mast_td_z = ft

    deck_z = h + 15.0 if props.generate_top_deck else h

    if props.generate_top_deck:

        mast_td_z = deck_z



    if getattr(props, 'has_mast', False):

        sock_h = getattr(props, 'mast_socket_height', 15.0)

        sock_d = getattr(props, 'mast_diameter', 8.0)

        y_off = getattr(props, 'mast_y_offset', 0.0)

        

        # Cutter for the mast hole. Should only go down to the deck floor (mast_td_z)

        cut_h = sock_h + 4.0 # Cuts through the socket and slightly into the floor

        ret = bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=32, radius1=sock_d/2.0, radius2=sock_d/2.0, depth=cut_h)

        # Center of the cutter so that its bottom is at mast_td_z - 2.0

        center_z = (mast_td_z - 2.0) + (cut_h / 2.0)

        bmesh.ops.translate(bm, vec=(0, y_off, center_z), verts=ret['verts'])



    if getattr(props, 'has_trapdoor', False):

        td_size = getattr(props, 'trapdoor_size', 1.0) * 25.4 # Convert squares to mm

        y_off = getattr(props, 'trapdoor_y_offset', 0.0)

        

        # Cube for trapdoor hole. Needs to penetrate perfectly.

        ret = bmesh.ops.create_cube(bm, size=1.0)

        bmesh.ops.scale(bm, vec=(td_size, td_size, props.floor_thickness + 2.0), verts=ret['verts'])

        # Center of the cutter matches the center of the lid

        bmesh.ops.translate(bm, vec=(0, y_off, mast_td_z + props.floor_thickness / 2.0), verts=ret['verts'])



