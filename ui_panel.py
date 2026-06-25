import bpy

class VIEW3D_PT_procedural_ship(bpy.types.Panel):
    bl_label = "Generador de Barcos D&D"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Ship Gen"

    def draw(self, context):
        layout = self.layout
        
        layout.operator("object.generate_ship_section", text="Generar Sección Nueva", icon='MESH_CUBE')
        layout.operator("object.generate_full_ship", text="Generar Barco Completo", icon='GROUP')
        layout.operator("object.generate_connector_clip", text="Generar Clip de Unión", icon='LINKED')
        
        obj = context.active_object
        if obj and (obj.ship_generator.is_ship or obj.ship_generator.is_connector_clip):
            props = obj.ship_generator
            
            if obj.ship_generator.is_ship:
                box = layout.box()
                box.label(text="Configuración Paramétrica", icon='MODIFIER')
                box.prop(props, "section_type")
                box.prop(props, "tiles_length")
                box.prop(props, "tiles_width")
                box.prop(props, "wall_height")
                
                box = layout.box()
                box.label(text="Arquitectura Multinivel", icon='OUTLINER_OB_LATTICE')
                if props.section_type == 'STERN':
                    box.prop(props, "has_quarterdeck")
                elif props.section_type == 'BOW':
                    box.prop(props, "has_forecastle")
                    
                if (props.section_type == 'STERN' and props.has_quarterdeck) or (props.section_type == 'BOW' and props.has_forecastle):
                    box.prop(props, "deck_elevation")
                    box.prop(props, "generate_stairs")
                
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
    bl_label = "Generar Sección de Barco"
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
        
        # Mark it as a ship and trigger the first generation
        obj.ship_generator.is_ship = True
        
        # Force an update by touching a property
        from .ship_generator import rebuild_ship_mesh
        rebuild_ship_mesh(obj)
        
        return {'FINISHED'}

class OBJECT_OT_generate_full_ship(bpy.types.Operator):
    bl_idname = "object.generate_full_ship"
    bl_label = "Generar Barco Completo"
    bl_description = "Genera Proa, Centro y Popa perfectamente alineados"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        from .ship_generator import rebuild_ship_mesh
        
        def make_section(name, stype, y_offset):
            mesh = bpy.data.meshes.new(name + "_Mesh")
            obj = bpy.data.objects.new(name, mesh)
            context.collection.objects.link(obj)
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
        
        make_section("Popa", 'STERN', -physical_length)
        mid = make_section("Centro", 'MID', 0)
        make_section("Proa", 'BOW', physical_length)
        
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
    OBJECT_OT_generate_full_ship,
    OBJECT_OT_generate_connector_clip
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
