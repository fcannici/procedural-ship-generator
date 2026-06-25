import bpy

_updating_all = False

def _sync_and_realign_ship(self, context):
    global _updating_all
    if _updating_all:
        return
        
    _updating_all = True
    try:
        obj = self.id_data
        
        # Primero, sincronizar propiedades
        for other in context.view_layer.objects:
            if other != obj and other.type == 'MESH' and hasattr(other, 'ship_generator') and other.ship_generator.is_ship:
                props = other.ship_generator
                props.tiles_length = self.tiles_length
                props.tiles_width = self.tiles_width
                props.wall_height = self.wall_height
                props.wall_thickness = self.wall_thickness
                props.floor_thickness = self.floor_thickness
                props.has_grid = self.has_grid
                props.generate_top_deck = self.generate_top_deck
                props.tolerance = self.tolerance
                
        # Segundo, realinear posiciones
        mid = None
        bows = []
        sterns = []
        
        for o in context.view_layer.objects:
            if o.type == 'MESH' and hasattr(o, 'ship_generator') and o.ship_generator.is_ship:
                if o.ship_generator.section_type == 'MID':
                    mid = o
                elif o.ship_generator.section_type == 'BOW':
                    bows.append(o)
                elif o.ship_generator.section_type == 'STERN':
                    sterns.append(o)
                    
        if mid:
            grid_size = 25.4
            mid_len = mid.ship_generator.tiles_length * grid_size
            
            for bow in bows:
                bow_len = bow.ship_generator.tiles_length * grid_size
                bow.location.y = mid.location.y + (mid_len / 2.0) + (bow_len / 2.0)
                
            for stern in sterns:
                stern_len = stern.ship_generator.tiles_length * grid_size
                stern.location.y = mid.location.y - (mid_len / 2.0) - (stern_len / 2.0)
                
    finally:
        _updating_all = False

def update_ship_geometry(self, context):
    # This prevents the rebuild from running recursively or on undo if we aren't careful,
    # but for parametric objects, we usually want it to just call the generator.
    # To avoid circular imports, we import the generator function here.
    from .ship_generator import rebuild_ship_mesh
    obj = self.id_data
    if obj and obj.type == 'MESH':
        rebuild_ship_mesh(obj)
        _sync_and_realign_ship(self, context)

class ShipGeneratorProperties(bpy.types.PropertyGroup):
    is_ship: bpy.props.BoolProperty(
        name="Es un barco procedural",
        default=False
    )
    
    is_connector_clip: bpy.props.BoolProperty(
        name="Es un clip de unión",
        default=False
    )
    
    section_type: bpy.props.EnumProperty(
        name="Tipo de Sección",
        description="El módulo del barco a generar",
        items=[
            ('BOW', "Proa", "Parte delantera del barco"),
            ('MID', "Centro", "Sección central modular"),
            ('STERN', "Popa", "Parte trasera del barco")
        ],
        default='MID',
        update=update_ship_geometry
    )
    
    tiles_length: bpy.props.FloatProperty(
        name="Largo (Casillas)",
        description="Largo de la sección en casillas de 1 pulgada (25.4mm)",
        default=4.0,
        min=1.0,
        step=50,
        update=update_ship_geometry
    )
    
    tiles_width: bpy.props.FloatProperty(
        name="Ancho interno (Casillas)",
        description="Ancho del piso interno en casillas de 1 pulgada",
        default=4.0,
        min=2.0,
        step=50,
        update=update_ship_geometry
    )
    
    wall_height: bpy.props.FloatProperty(
        name="Altura de Pared",
        description="Altura de las paredes del casco",
        default=40.0,
        min=10.0,
        update=update_ship_geometry
    )
    
    wall_thickness: bpy.props.FloatProperty(
        name="Grosor de Pared",
        description="Grosor de las paredes para impresión 3D",
        default=5.0,
        min=1.0,
        update=update_ship_geometry
    )
    
    has_quarterdeck: bpy.props.BoolProperty(
        name="Castillo de Popa",
        description="Eleva la cubierta trasera para crear un cuarto de mando",
        default=False,
        update=update_ship_geometry
    )
    
    has_forecastle: bpy.props.BoolProperty(
        name="Castillo de Proa",
        description="Eleva la cubierta delantera",
        default=False,
        update=update_ship_geometry
    )
    
    deck_elevation: bpy.props.FloatProperty(
        name="Elevación (mm)",
        description="Altura adicional para los castillos",
        default=25.0,
        min=10.0,
        update=update_ship_geometry
    )
    
    generate_stairs: bpy.props.BoolProperty(
        name="Generar Escaleras",
        description="Añade escaleras integradas a los castillos para las miniaturas",
        default=True,
        update=update_ship_geometry
    )
    
    floor_thickness: bpy.props.FloatProperty(
        name="Grosor de Suelo",
        description="Grosor sólido del piso en mm",
        default=6.0,
        min=1.0,
        update=update_ship_geometry
    )
    
    has_grid: bpy.props.BoolProperty(
        name="Generar Cuadrícula",
        description="Esculpe una cuadrícula de 1 pulgada en el suelo",
        default=True,
        update=update_ship_geometry
    )
    
    generate_top_deck: bpy.props.BoolProperty(
        name="Cubierta Removible",
        description="Genera la tapa superior como geometría adicional",
        default=True,
        update=update_ship_geometry
    )
    
    tolerance: bpy.props.FloatProperty(
        name="Tolerancia FDM (mm)",
        description="Tolerancia para encastres",
        default=0.2,
        min=0.0,
        step=1,
        precision=2,
        update=update_ship_geometry
    )

classes = [
    ShipGeneratorProperties
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
