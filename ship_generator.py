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


    verts_coords = [
        (-top_w2, h, 0),             # 0: Outer left top
        (-mid_w2, mid_h, 0),     # 1: Outer left mid
        (-bot_w2, 0, 0),         # 2: Outer left bottom
        (-5.0, 0, 0),            # 3: Floor left split
        (-3.0, 0, 0),            # 4: Channel left bottom (narrow)
        (-5.0, 3.0, 0),          # 5: Channel left top (wide)
        (5.0, 3.0, 0),           # 6: Channel right top (wide)
        (3.0, 0, 0),             # 7: Channel right bottom (narrow)
        (5.0, 0, 0),             # 8: Floor right split
        (bot_w2, 0, 0),          # 9: Outer right bottom
        (mid_w2, mid_h, 0),      # 10: Outer right mid
        (top_w2, h, 0),              # 11: Outer right top
        (top_w2-t, h, 0),            # 12: Inner right top
        (mid_w2-t, mid_h, 0),    # 13: Inner right mid
        (bot_w2-t, ft, 0),       # 14: Inner right floor corner
        (5.0, ft, 0),            # 15: Inner right channel-align
        (-5.0, ft, 0),           # 16: Inner left channel-align
        (-bot_w2+t, ft, 0),      # 17: Inner left floor corner
        (-mid_w2+t, mid_h, 0),   # 18: Inner left mid
        (-top_w2+t, h, 0),           # 19: Inner left top
    ]

    def create_hull_segment(bm, start_y, end_y, scale_front=1.0, scale_back=1.0):
        back_verts = [bm.verts.new((c[0] * scale_back, start_y, c[1])) for c in verts_coords]
        front_verts = [bm.verts.new((c[0] * scale_front, end_y, c[1])) for c in verts_coords]
        
        left_cap_indices = [0, 1, 2, 17, 18, 19]
        right_cap_indices = [9, 10, 11, 12, 13, 14]
        floor_cap_indices = [2, 3, 4, 5, 6, 7, 8, 9, 14, 15, 16, 17]

        # Back caps (CW)
        bm.faces.new([back_verts[i] for i in left_cap_indices][::-1])
        bm.faces.new([back_verts[i] for i in right_cap_indices][::-1])
        bm.faces.new([back_verts[i] for i in floor_cap_indices][::-1])

        # Front caps (CCW)
        bm.faces.new([front_verts[i] for i in left_cap_indices])
        bm.faces.new([front_verts[i] for i in right_cap_indices])
        bm.faces.new([front_verts[i] for i in floor_cap_indices])

        # === Solid Plugs to Close the Ship's Interior ===
        plug_coords = [verts_coords[i] for i in range(12, 20)]
        if props.section_type == 'STERN':
            p_scale_back = scale_back
            p_y_back = -l2
            p_progress_front = props.wall_thickness / (2 * l2)
            p_scale_front = scale_back + (scale_front - scale_back) * p_progress_front
            p_y_front = -l2 + props.wall_thickness
            
            plug_back_verts = [bm.verts.new((c[0] * p_scale_back, p_y_back, c[1])) for c in plug_coords]
            plug_front_verts = [bm.verts.new((c[0] * p_scale_front, p_y_front, c[1])) for c in plug_coords]
            
            bm.faces.new(plug_back_verts[::-1]) # CW
            bm.faces.new(plug_front_verts)      # CCW
            for i in range(8):
                bm.faces.new((plug_back_verts[i], plug_back_verts[(i+1)%8], plug_front_verts[(i+1)%8], plug_front_verts[i]))
                
        elif props.section_type == 'BOW':
            p_scale_front = scale_front
            p_y_front = l2
            p_progress_back = (2 * l2 - props.wall_thickness) / (2 * l2)
            p_scale_back = scale_back + (scale_front - scale_back) * p_progress_back
            p_y_back = l2 - props.wall_thickness
            
            plug_back_verts = [bm.verts.new((c[0] * p_scale_back, p_y_back, c[1])) for c in plug_coords]
            plug_front_verts = [bm.verts.new((c[0] * p_scale_front, p_y_front, c[1])) for c in plug_coords]
            
            bm.faces.new(plug_back_verts[::-1]) # CW
            bm.faces.new(plug_front_verts)      # CCW
            for i in range(8):
                bm.faces.new((plug_back_verts[i], plug_back_verts[(i+1)%8], plug_front_verts[(i+1)%8], plug_front_verts[i]))
            
        num_verts = len(verts_coords)
        for i in range(num_verts):
            bm.faces.new((back_verts[i], back_verts[(i+1)%num_verts], front_verts[(i+1)%num_verts], front_verts[i]))
            
        return front_verts, back_verts

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
                    allowed_w2_start = (bot_w2 - t) * (1.0 - progress_start)
                    allowed_w2_end = (bot_w2 - t) * (1.0 - progress_end)
                    allowed_w2 = min(allowed_w2_start, allowed_w2_end)
                elif props.section_type == 'STERN':
                    progress_start = (valid_ty1 - (-l2)) / (2*l2)
                    progress_end = (valid_ty2 - (-l2)) / (2*l2)
                    allowed_w2_start = (bot_w2 - t) * (0.7 + 0.3 * progress_start)
                    allowed_w2_end = (bot_w2 - t) * (0.7 + 0.3 * progress_end)
                    allowed_w2 = min(allowed_w2_start, allowed_w2_end)
                else:
                    allowed_w2 = bot_w2 - t
                    
                valid_tx1 = max(tx1, -allowed_w2 + groove_width)
                valid_tx2 = min(tx2, allowed_w2 - groove_width)
                
                if valid_tx1 >= valid_tx2:
                    continue
                    
                v1 = bm.verts.new((valid_tx1, valid_ty1, ft - 0.2))
                v2 = bm.verts.new((valid_tx2, valid_ty1, ft - 0.2))
                v3 = bm.verts.new((valid_tx2, valid_ty2, ft - 0.2))
                v4 = bm.verts.new((valid_tx1, valid_ty2, ft - 0.2))
                f_tile = bm.faces.new((v1, v2, v3, v4))
                
                geom = bmesh.ops.extrude_face_region(bm, geom=[f_tile])
                extruded_verts = [v for v in geom['geom'] if isinstance(v, bmesh.types.BMVert)]
                bmesh.ops.translate(bm, vec=(0, 0, tile_height + 0.2), verts=extruded_verts)

    if props.generate_top_deck:
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
            
        d_verts = [
            (-deck_w2, deck_z, 0),
            (deck_w2, deck_z, 0),
            (deck_w2, deck_z + deck_thickness, 0),
            (-deck_w2, deck_z + deck_thickness, 0)
        ]
        
        d_back = [bm.verts.new((c[0] * scale_back_deck, deck_start_y, c[1])) for c in d_verts]
        d_front = [bm.verts.new((c[0] * scale_front_deck, deck_end_y, c[1])) for c in d_verts]
        
        bm.faces.new((d_back[0], d_back[3], d_back[2], d_back[1])) # CW
        bm.faces.new((d_front[0], d_front[1], d_front[2], d_front[3])) # CCW
        
        for i in range(4):
            bm.faces.new((d_back[i], d_back[(i+1)%4], d_front[(i+1)%4], d_front[i]))

    if props.generate_stairs:
        if (props.section_type == 'STERN' and props.has_quarterdeck) or (props.section_type == 'BOW' and props.has_forecastle):
            # Stair geometry
            elev = props.deck_elevation
            base_z = props.floor_thickness # floor_thickness wasn't raised, wait!
            # ft was raised at the beginning of the function!
            # so base_z = ft - elev
            base_z = ft - elev
            stair_w2 = (bot_w2 - t) * 0.4 # width of the stairs (40% of inner floor)
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

    bm.normal_update()
    bm.to_mesh(obj.data)
    bm.free()

def register():
    pass

def unregister():
    pass
