import bpy

class VIEW3D_PT_procedural_ship(bpy.types.Panel):
    bl_label = "Generador de Barcos D&D"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Ship Gen"

    def draw(self, context):
        layout = self.layout
        
        layout.operator("object.generate_ship_section", text="Agregar Sección Extra (Centro)", icon='MESH_CUBE')
        layout.operator("object.generate_full_ship", text="Generar Barco Inicial (3 Partes)", icon='GROUP')
        layout.operator("object.generate_connector_clip", text="Generar Clip de Unión", icon='LINKED')
        
        obj = context.active_object
        if obj is not None and obj.type == 'MESH' and hasattr(obj, "ship_generator"):
            props = obj.ship_generator
            if props.is_ship:
                
                box = layout.box()
                box.label(text="Dimensiones Base", icon='OBJECT_DATA')
                box.prop(props, "section_type")
                box.prop(props, "tiles_length")
                box.prop(props, "tiles_width")
                box.prop(props, "wall_height")
                
                box = layout.box()
                box.label(text="Textura de Casco (Tablones)", icon='TEXTURE')
                box.prop(props, "plank_height")
                box.prop(props, "lapstrake_depth")
                
                box = layout.box()
                box.label(text="Textura de Cubierta (Piso)", icon='MATPLANE')
                box.prop(props, "generate_floor_planks")
                if props.generate_floor_planks:
                    box.prop(props, "floor_plank_width")
                    box.prop(props, "floor_plank_length")
                    
                box = layout.box()
                box.label(text="Conectores Inferiores", icon='LINKED')
                box.prop(props, "generate_connector_slot")
                
                box = layout.box()
                box.label(text="Arquitectura Multinivel", icon='GROUP_VERTEX')
                if props.section_type == 'STERN':
                    box.prop(props, "has_quarterdeck")
                    if props.has_quarterdeck:
                        box.prop(props, "quarterdeck_closed_front")
                elif props.section_type == 'BOW':
                    box.prop(props, "has_forecastle")
                    if props.has_forecastle:
                        box.prop(props, "forecastle_closed_back")
                box.prop(props, "generate_stairs")
                if props.generate_stairs:
                    # If empty, maybe add one? The user can just click add.
                    row = box.row()
                    row.operator("object.add_ship_stair", text="Añadir Escalera", icon='ADD')
                    row.operator("object.remove_ship_stair", text="Eliminar", icon='REMOVE')
                    
                    if len(props.stairs) > 0:
                        box.prop(props, "active_stair_idx", text=f"Escalera ({len(props.stairs)})")
                        idx = props.active_stair_idx
                        if 0 <= idx < len(props.stairs):
                            st = props.stairs[idx]
                            sbox = box.box()
                            sbox.prop(st, "level")
                            sbox.prop(st, "direction")
                            sbox.prop(st, "offset_x")
                            sbox.prop(st, "offset_y")
                            sbox.prop(st, "rotation_z")
                            sbox.prop(st, "width")
                            sbox.prop(st, "length")
                    
                if props.has_quarterdeck or props.has_forecastle:
                    box.prop(props, "deck_elevation")
                
                box = layout.box()
                box.label(text="Barandas", icon='MOD_WIREFRAME')
                box.prop(props, "generate_railings")
                if props.generate_railings:
                    box.prop(props, "railing_height")
                    box.prop(props, "railing_thickness")
                    box.prop(props, "railing_offset_inward")
                    box.prop(props, "railing_spacing")
                
                box = layout.box()
                box.label(text="Accesorios Funcionales", icon='MOD_BOOLEAN')
                box.prop(props, "has_mast")
                if props.has_mast:
                    box.prop(props, "mast_diameter")
                    box.prop(props, "mast_socket_height")
                    box.prop(props, "mast_y_offset")
                box.prop(props, "has_trapdoor")
                if props.has_trapdoor:
                    box.prop(props, "trapdoor_size")
                    box.prop(props, "trapdoor_y_offset")
                
                box = layout.box()
                box.label(text="Impresión FDM", icon='MESH_DATA')
                box.prop(props, "wall_thickness")
                box.prop(props, "floor_thickness")
                box.prop(props, "tolerance")
                
                box = layout.box()
                box.label(text="Interiores", icon='FACESEL')
                box.prop(props, "has_grid")
                box.prop(props, "generate_top_deck")
            else:
                box = layout.box()
                box.label(text="Configuración del Clip", icon='MODIFIER')
                box.prop(props, "tolerance")

class OBJECT_OT_generate_ship_section(bpy.types.Operator):
    bl_idname = "object.generate_ship_section"
    bl_label = "Agregar Sección Extra (Centro)"
    bl_description = "Crea un nuevo objeto de sección de barco procedural"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        # Create a new mesh and object
        mesh = bpy.data.meshes.new("ShipSection_Mesh")
        obj = bpy.data.objects.new("ShipSection", mesh)
        
        # Link it to the scene
        context.collection.objects.link(obj)
        
        # Select the new object
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        context.view_layer.objects.active = obj
        
        # Mark it as a ship
        obj.ship_generator.is_ship = True
        
        # Inherit settings from an existing ship piece if one exists
        existing = [o for o in context.view_layer.objects if o != obj and hasattr(o, 'ship_generator') and o.ship_generator.is_ship]
        if existing:
            src = next((o for o in existing if o.ship_generator.section_type == 'MID'), existing[0])
            for k, v in src.ship_generator.items():
                if k not in ['name', 'section_type']:
                    try:
                        obj.ship_generator[k] = v
                    except:
                        pass
        
        # Trigger the first generation
        from .ship_generator import rebuild_ship_mesh
        rebuild_ship_mesh(obj)
        
        from .ship_properties import _realign_ship
        _realign_ship(context)
        
        return {'FINISHED'}

class OBJECT_OT_add_ship_stair(bpy.types.Operator):
    bl_idname = "object.add_ship_stair"
    bl_label = "Añadir Escalera"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.active_object
        if obj and hasattr(obj, 'ship_generator'):
            props = obj.ship_generator
            props.stairs.add()
            props.active_stair_idx = len(props.stairs) - 1
            from .ship_generator import rebuild_ship_mesh
            rebuild_ship_mesh(obj)
        return {'FINISHED'}

class OBJECT_OT_remove_ship_stair(bpy.types.Operator):
    bl_idname = "object.remove_ship_stair"
    bl_label = "Eliminar Escalera"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.active_object
        if obj and hasattr(obj, 'ship_generator'):
            props = obj.ship_generator
            idx = props.active_stair_idx
            if 0 <= idx < len(props.stairs):
                props.stairs.remove(idx)
                props.active_stair_idx = max(0, idx - 1)
                from .ship_generator import rebuild_ship_mesh
                rebuild_ship_mesh(obj)
        return {'FINISHED'}

class OBJECT_OT_generate_full_ship(bpy.types.Operator):
    bl_idname = "object.generate_full_ship"
    bl_label = "Generar Barco Inicial (3 Partes)"
    bl_description = "Genera Proa, Centro y Popa perfectamente alineados"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        from .ship_generator import rebuild_ship_mesh
        
        def make_section(name, stype, y_offset, source_obj=None):
            mesh = bpy.data.meshes.new(name + "_Mesh")
            obj = bpy.data.objects.new(name, mesh)
            context.collection.objects.link(obj)
            
            if source_obj and source_obj.ship_generator.is_ship:
                # Copy properties
                for k, v in source_obj.ship_generator.items():
                    if k not in ['name', 'section_type']:
                        try:
                            obj.ship_generator[k] = v
                        except:
                            pass
                            
            obj.ship_generator.is_ship = True
            obj.ship_generator.section_type = stype
            obj.location = (0, y_offset, 0)
            rebuild_ship_mesh(obj)
            return obj
            
        tiles_len = 4.0
        active = context.active_object
        if active and active.ship_generator.is_ship:
            tiles_len = active.ship_generator.tiles_length
            
        bpy.ops.object.select_all(action='DESELECT')
        
        physical_length = tiles_len * 25.4
        
        make_section("Popa", 'STERN', -physical_length, active)
        mid = make_section("Centro", 'MID', 0, active)
        make_section("Proa", 'BOW', physical_length, active)
        
        mid.select_set(True)
        context.view_layer.objects.active = mid
        
        return {'FINISHED'}

class OBJECT_OT_generate_connector_clip(bpy.types.Operator):
    bl_idname = "object.generate_connector_clip"
    bl_label = "Generar Clip de Unión"
    bl_description = "Crea el clip de encastre (Cola de milano) para unir las secciones del barco"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        mesh = bpy.data.meshes.new("ClipDovetail_Mesh")
        obj = bpy.data.objects.new("ClipDovetail", mesh)
        
        context.collection.objects.link(obj)
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        context.view_layer.objects.active = obj
        
        obj.ship_generator.is_connector_clip = True
        
        from .ship_generator import rebuild_ship_mesh
        rebuild_ship_mesh(obj)
        
        return {'FINISHED'}

classes = [
    VIEW3D_PT_procedural_ship,
    OBJECT_OT_generate_ship_section,
    OBJECT_OT_add_ship_stair,
    OBJECT_OT_remove_ship_stair,
    OBJECT_OT_generate_full_ship,
    OBJECT_OT_generate_connector_clip
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

