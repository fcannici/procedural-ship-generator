import bpy

_updating_all = False

def _realign_ship(context):
    bows = []
    mids = []
    sterns = []
    
    for o in list(context.view_layer.objects):
        if o and o.type == 'MESH' and hasattr(o, 'ship_generator') and o.ship_generator.is_ship:
            t = o.ship_generator.section_type
            if t == 'BOW': bows.append(o)
            elif t == 'MID': mids.append(o)
            elif t == 'STERN': sterns.append(o)
            
    if not (bows or mids or sterns):
        return
        
    bows.sort(key=lambda x: x.location.y, reverse=True)
    mids.sort(key=lambda x: x.location.y, reverse=True)
    sterns.sort(key=lambda x: x.location.y, reverse=True)
    
    sequence = bows + mids + sterns
    
    if mids:
        anchor = mids[0]
    elif bows:
        anchor = bows[0]
    else:
        anchor = sterns[0]
        
    grid_size = 25.4
    anchor_idx = sequence.index(anchor)
    
    current_y = anchor.location.y + (anchor.ship_generator.tiles_length * grid_size) / 2.0
    for i in range(anchor_idx - 1, -1, -1):
        obj = sequence[i]
        l = obj.ship_generator.tiles_length * grid_size
        obj.location.y = current_y + l / 2.0
        current_y += l
        
    current_y = anchor.location.y - (anchor.ship_generator.tiles_length * grid_size) / 2.0
    for i in range(anchor_idx + 1, len(sequence)):
        obj = sequence[i]
        l = obj.ship_generator.tiles_length * grid_size
        obj.location.y = current_y - l / 2.0
        current_y -= l

def update_no_sync(self, context):
    import bpy
    from .ship_generator import rebuild_ship_mesh
    obj = self.id_data
    if obj and obj.parent and hasattr(obj.parent, "ship_generator") and obj.parent.ship_generator.is_ship:
        obj = obj.parent
    if obj is not None and getattr(obj, 'type', '') == 'MESH':
        def deferred_update():
            try:
                rebuild_ship_mesh(obj)
                if hasattr(bpy.context.scene, 'ship_generator_error'):
                    bpy.context.scene.ship_generator_error = ""
            except Exception as e:
                import traceback, sys
                exc_type, exc_value, exc_traceback = sys.exc_info()
                tb = traceback.extract_tb(exc_traceback)
                if tb:
                    last_frame = tb[-1]
                    error_str = f"Error in {last_frame.name} (line {last_frame.lineno}): {exc_type.__name__}: {exc_value}"
                else:
                    error_str = f"{exc_type.__name__}: {exc_value}"
                print("CRASH IN REBUILD:", error_str)
                try: bpy.context.scene.ship_generator_error = error_str
                except: pass
            return None
        if not bpy.app.timers.is_registered(deferred_update):
            bpy.app.timers.register(deferred_update, first_interval=0.1)

def update_accessory_no_sync(self, context):
    from .ship_generator import rebuild_ship_mesh
    obj = self.id_data
    if obj and obj.type == 'MESH':
        try:
            rebuild_ship_mesh(obj)
        except Exception as e:
            import traceback
            traceback.print_exc()
            def draw(self, context):
                self.layout.label(text=f"Error al generar: {str(e)}")
            context.window_manager.popup_menu(draw, title="Error en Procedural Ship", icon='ERROR')
    _realign_ship(context)

def update_stair_level(self, context):
    update_no_sync(self, context)

def _sync_prop(self, context, prop_name):
    global _updating_all
    from .ship_generator import rebuild_ship_mesh
    obj = self.id_data
    if obj and obj.parent and hasattr(obj.parent, "ship_generator") and obj.parent.ship_generator.is_ship:
        obj = obj.parent

    if not _updating_all:
        _updating_all = True
        try:
            val = getattr(self, prop_name)
            for other in list(context.view_layer.objects):
                if other is not None and getattr(other, 'type', '') == 'MESH' and hasattr(other, 'ship_generator') and other.ship_generator.is_ship:
                    setattr(other.ship_generator, prop_name, val)
                    def deferred_update(tgt=other):
                        try:
                            rebuild_ship_mesh(tgt)
                            if hasattr(bpy.context.scene, 'ship_generator_error'):
                                bpy.context.scene.ship_generator_error = ""
                        except Exception as e:
                            import traceback, sys
                            exc_type, exc_value, exc_traceback = sys.exc_info()
                            tb = traceback.extract_tb(exc_traceback)
                            if tb:
                                last_frame = tb[-1]
                                error_str = f"Error in {last_frame.name} (line {last_frame.lineno}): {exc_type.__name__}: {exc_value}"
                            else:
                                error_str = f"{exc_type.__name__}: {exc_value}"
                            try: bpy.context.scene.ship_generator_error = error_str
                            except: pass
                        return None
                    import bpy
                    if not bpy.app.timers.is_registered(deferred_update):
                        bpy.app.timers.register(deferred_update, first_interval=0.1)
        finally:
            _updating_all = False

    if obj is not None and getattr(obj, 'type', '') == 'MESH':
        def deferred_update_self():
            try: rebuild_ship_mesh(obj)
            except: pass
            return None
        import bpy
        if not bpy.app.timers.is_registered(deferred_update_self):
            bpy.app.timers.register(deferred_update_self, first_interval=0.1)

    _realign_ship(context)

def update_tiles_width(self, context): _sync_prop(self, context, 'tiles_width')
def update_wall_height(self, context): _sync_prop(self, context, 'wall_height')
def update_wall_thickness(self, context): _sync_prop(self, context, 'wall_thickness')
def update_floor_thickness(self, context): _sync_prop(self, context, 'floor_thickness')
def update_deck_width_offset(self, context): _sync_prop(self, context, 'deck_width_offset')
def update_has_grid(self, context): _sync_prop(self, context, 'has_grid')
def update_tolerance(self, context): _sync_prop(self, context, 'tolerance')
def update_clip_tightness(self, context): _sync_prop(self, context, 'clip_tightness')
def update_clip_length_offset(self, context): _sync_prop(self, context, 'clip_length_offset')
def update_plank_height(self, context): _sync_prop(self, context, 'plank_height')
def update_lapstrake_depth(self, context): _sync_prop(self, context, 'lapstrake_depth')
def update_generate_plank_cuts(self, context): _sync_prop(self, context, 'generate_plank_cuts')
def update_plank_cut_width(self, context): _sync_prop(self, context, 'plank_cut_width')
def update_plank_cut_density(self, context): _sync_prop(self, context, 'plank_cut_density')

def update_generate_floor_planks(self, context): _sync_prop(self, context, 'generate_floor_planks')
def update_floor_plank_width(self, context): _sync_prop(self, context, 'floor_plank_width')
def update_floor_plank_length(self, context): _sync_prop(self, context, 'floor_plank_length')

def update_generate_connector_slot(self, context): _sync_prop(self, context, 'generate_connector_slot')

class StairItem(bpy.types.PropertyGroup):
    level: bpy.props.EnumProperty(
        name="Nivel",
        description="Niveles que conecta la escalera",
        items=[
            ('BODEGA_MAIN', "Bodega a Principal", "Conecta la bodega con la cubierta principal"),
            ('MAIN_CASTLE', "Principal a Castillo", "Conecta la cubierta principal con el castillo (si existe)")
        ],
        default='BODEGA_MAIN',
        update=update_stair_level
    )
    direction: bpy.props.EnumProperty(
        name="Dirección",
        description="Hacia dónde se extiende la escalera",
        items=[
            ('INWARD', "Hacia Adentro", "La escalera se construye hacia el interior del módulo"),
            ('OUTWARD', "Hacia Afuera", "La escalera sobresale hacia el módulo adyacente")
        ],
        default='INWARD',
        update=update_no_sync
    )
    offset_x: bpy.props.FloatProperty(
        name="Offset X Escalera",
        description="Mueve las escaleras lateralmente",
        default=0.0,
        update=update_no_sync
    )
    offset_y: bpy.props.FloatProperty(
        name="Offset Y Escalera",
        description="Mueve las escaleras longitudinalmente",
        default=0.0,
        update=update_no_sync
    )
    rotation_z: bpy.props.FloatProperty(
        name="Rotación Z Escalera",
        description="Rota las escaleras sobre el eje Z (en grados)",
        default=0.0,
        update=update_no_sync
    )
    width: bpy.props.FloatProperty(
        name="Ancho Escalera",
        description="Define el ancho de la escalera",
        default=20.0,
        min=5.0,
        update=update_no_sync
    )
    length: bpy.props.FloatProperty(
        name="Largo Escalera",
        description="Define qué tan lejos llegan los escalones",
        default=40.0,
        min=10.0,
        update=update_no_sync
    )

class AccessoryItem(bpy.types.PropertyGroup):
    acc_type: bpy.props.EnumProperty(
        name="Tipo",
        items=[
            ('HELM', "Timón", "Timón de mando"),
            ('MAST_MAIN', "Mástil Mayor", "Mástil central"),
            ('MAST_FORE', "Mástil Trinquete (Proa)", "Mástil delantero"),
            ('MAST_MIZZEN', "Mástil Mesana (Popa)", "Mástil trasero"),
            ('BOWSPRIT', "Bauprés", "Mástil de proa inclinado"),
            ('CUSTOM', "Personalizado", "Punto de encastre genérico")
        ],
        default='HELM',
        update=update_accessory_no_sync
    )
    level: bpy.props.EnumProperty(
        name="Cubierta",
        items=[
            ('CASTLE', "Castillo", "Cubierta elevada (Castillo)"),
            ('MAIN', "Principal", "Cubierta principal"),
            ('BODEGA', "Bodega (Fondo)", "Piso de la bodega")
        ],
        default='CASTLE',
        update=update_accessory_no_sync
    )
    offset_x: bpy.props.FloatProperty(
        name="Offset X",
        default=0.0,
        update=update_accessory_no_sync
    )
    offset_y: bpy.props.FloatProperty(
        name="Offset Y",
        default=0.0,
        update=update_accessory_no_sync
    )
    rotation_z: bpy.props.FloatProperty(
        name="Rotación Z",
        default=0.0,
        update=update_accessory_no_sync
    )
    snap_radius: bpy.props.FloatProperty(
        name="Radio de Encastre (mm)",
        default=3.0,
        update=update_accessory_no_sync
    )
    snap_depth: bpy.props.FloatProperty(
        name="Profundidad de Encastre (mm)",
        default=5.0,
        update=update_accessory_no_sync
    )

class ShipGeneratorProperties(bpy.types.PropertyGroup):
    creator_race: bpy.props.EnumProperty(
        name="Raza Creadora",
        description="Escala las proporciones arquitectónicas (no la cuadrícula) según la raza",
        items=[
            ('SMALL', "Mediano / Aasimar Peq. (25mm)", "Escala 0.68x"),
            ('GNOME', "Gnomo (27mm)", "Escala 0.73x"),
            ('DWARF', "Enano (32mm)", "Escala 0.86x"),
            ('HUMAN', "Humano / Elfo (37mm)", "Escala 1.0x base"),
            ('LARGE', "SemiOrco / Tiefling (40mm)", "Escala 1.08x"),
            ('GOLIATH', "Goliath (42mm)", "Escala 1.14x")
        ],
        default='HUMAN',
        update=update_no_sync
    )
    
    is_ship: bpy.props.BoolProperty(
        name="Es un barco procedural",
        default=False
    )
    
    is_connector_clip: bpy.props.BoolProperty(
        name="Índice de Escalera Activa",
        default=0
    )
    
    accessories: bpy.props.CollectionProperty(type=AccessoryItem)
    active_accessory_idx: bpy.props.IntProperty(
        name="Índice de Accesorio Activo",
        default=0
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
        update=update_no_sync
    )
    
    tiles_length: bpy.props.FloatProperty(
        name="Largo (Casillas)",
        description="Largo de la sección en casillas de 1 pulgada (25.4mm)",
        default=4.0,
        min=1.0,
        step=50,
        update=update_no_sync
    )
    
    tiles_width: bpy.props.FloatProperty(
        name="Ancho interno (Casillas)",
        description="Ancho del piso interno en casillas de 1 pulgada",
        default=4.0,
        min=2.0,
        step=50,
        update=update_tiles_width
    )
    
    wall_height: bpy.props.FloatProperty(
        name="Altura de Pared",
        description="Altura de las paredes del casco",
        default=40.0,
        min=10.0,
        update=update_wall_height
    )
    
    wall_thickness: bpy.props.FloatProperty(
        name="Grosor de Pared",
        description="Grosor de las paredes para impresión 3D",
        default=5.0,
        min=1.0,
        update=update_wall_thickness
    )
    
    has_quarterdeck: bpy.props.BoolProperty(
        name="Castillo de Popa",
        description="Eleva la cubierta trasera para crear un cuarto de mando",
        default=False,
        update=update_no_sync
    )
    
    quarterdeck_closed_front: bpy.props.BoolProperty(
        name="Cerrar Castillo de Popa",
        description="Cierra toda la pared frontal del castillo. Si está desactivado, deja un balcón abierto a la cubierta inferior.",
        default=False,
        update=update_no_sync
    )
    
    
    has_forecastle: bpy.props.BoolProperty(
        name="Castillo de Proa",
        description="Eleva la cubierta delantera",
        default=False,
        update=update_no_sync
    )
    
    forecastle_closed_back: bpy.props.BoolProperty(
        name="Cerrar Castillo de Proa",
        description="Cierra toda la pared trasera del castillo. Si está desactivado, deja un balcón abierto a la cubierta inferior.",
        default=False,
        update=update_no_sync
    )
    
    deck_elevation: bpy.props.FloatProperty(
        name="Alto de Pared del Castillo (mm)",
        description="Altura adicional para los castillos",
        default=25.0,
        min=10.0,
        update=update_no_sync
    )
    
    generate_deck_ledge: bpy.props.BoolProperty(
        name="Generar Soporte para Cubierta (Cuña)",
        description="Añade una cuña de 45 grados en el muro interior para que la cubierta descanse sin necesidad de soportes de impresión",
        default=True,
        update=update_no_sync
    )
    
    deck_ledge_width: bpy.props.FloatProperty(
        name="Ancho de la Cuña (mm)",
        description="Qué tanto sobresale la cuña hacia adentro",
        default=2.0,
        min=0.5,
        max=10.0,
        update=update_no_sync
    )
    
    generate_stairs: bpy.props.BoolProperty(
        name="Generar Escaleras",
        description="Añade escaleras integradas a los castillos para las miniaturas",
        default=True,
        update=update_no_sync
    )
    
    stairs: bpy.props.CollectionProperty(type=StairItem)
    active_stair_idx: bpy.props.IntProperty(
        name="Escalera Activa",
        default=0
    )
    
    floor_thickness: bpy.props.FloatProperty(
        name="Grosor de Suelo",
        description="Grosor sólido del piso en mm",
        default=6.0,
        min=1.0,
        update=update_floor_thickness
    )
    
    deck_width_offset: bpy.props.FloatProperty(
        name="Compensación Ancho Cubierta (mm)",
        description="Ajuste fino para el ancho de la cubierta (positivo = más ancho, negativo = más angosto)",
        default=0.0,
        min=-10.0,
        max=10.0,
        step=10,
        precision=2,
        update=update_deck_width_offset
    )
    
    has_grid: bpy.props.BoolProperty(
        name="Generar Cuadrícula",
        description="Esculpe una cuadrícula de 1 pulgada en el suelo",
        default=True,
        update=update_has_grid
    )
    
    generate_top_deck: bpy.props.BoolProperty(
        name="Cubierta Removible",
        description="Genera la tapa superior como geometría adicional",
        default=True,
        update=update_no_sync
    )
    
    tolerance: bpy.props.FloatProperty(
        name="Tolerancia FDM (mm)",
        description="Tolerancia general para encastres",
        default=0.2,
        min=0.0,
        step=1,
        precision=2,
        update=update_tolerance
    )
    
    clip_tightness: bpy.props.FloatProperty(
        name="Ajuste de Grosor (Apriete)",
        description="Aumentar para que el clip quede más gordo (apretado). Disminuir para más suelto.",
        default=0.0,
        min=-0.5,
        max=0.5,
        step=1,
        precision=2,
        update=update_clip_tightness
    )
    
    clip_length_offset: bpy.props.FloatProperty(
        name="Ajuste de Largo",
        description="Aumentar para hacer el clip más largo (eje Y). Disminuir para más corto.",
        default=0.0,
        min=-2.0,
        max=2.0,
        step=1,
        precision=2,
        update=update_clip_length_offset
    )
    
    plank_height: bpy.props.FloatProperty(
        name="Alto de Tablón",
        description="Altura de cada tablón horizontal en el casco",
        default=8.0,
        min=2.0,
        update=update_plank_height
    )
    
    lapstrake_depth: bpy.props.FloatProperty(
        name="Profundidad de Relieve",
        description="Profundidad del solapamiento entre tablones (Tingladillo)",
        default=1.5,
        min=0.0,
        update=update_lapstrake_depth
    )
    
    generate_plank_cuts: bpy.props.BoolProperty(
        name="Cortes Verticales",
        description="Genera cortes aleatorios para simular tablones individuales de distintos largos",
        default=False,
        update=update_generate_plank_cuts
    )
    
    plank_cut_width: bpy.props.FloatProperty(
        name="Grosor del Corte",
        description="Ancho de la hendidura vertical entre tablones",
        default=1.5,
        min=0.1,
        update=update_plank_cut_width
    )
    
    plank_cut_density: bpy.props.FloatProperty(
        name="Densidad de Cortes",
        description="Probabilidad de cortes (0 = tablones infinitos, 1 = fragmentados)",
        default=0.3,
        min=0.0,
        max=1.0,
        update=update_plank_cut_density
    )

    generate_floor_planks: bpy.props.BoolProperty(
        name="Tablones en el Piso",
        description="Genera textura de tablones separados en la cubierta",
        default=True,
        update=update_generate_floor_planks
    )
    
    generate_connector_slot: bpy.props.BoolProperty(
        name="Generar Canaleta (Zocalo)",
        description="Genera la canaleta inferior para conectar las piezas",
        default=True,
        update=update_generate_connector_slot
    )
    
    floor_plank_width: bpy.props.FloatProperty(
        name="Ancho de Tablones (Piso)",
        description="Ancho de cada tabla del piso (eje X)",
        default=10.0,
        min=2.0,
        update=update_floor_plank_width
    )
    
    floor_plank_length: bpy.props.FloatProperty(
        name="Largo Medio (Piso)",
        description="Largo promedio de los tablones del piso (eje Y)",
        default=40.0,
        min=5.0,
        update=update_floor_plank_length
    )

    # --- ACCESORIOS FUNCIONALES (FASE 4) ---
    has_mast: bpy.props.BoolProperty(
        name="Zócalo para Mástil",
        description="Genera un zócalo con orificio para insertar un mástil",
        default=False,
        update=update_no_sync
    )
    
    mast_diameter: bpy.props.FloatProperty(
        name="Diámetro del Mástil",
        description="Diámetro del agujero interno para el mástil (mm)",
        default=8.0,
        min=2.0,
        update=update_no_sync
    )
    
    mast_socket_height: bpy.props.FloatProperty(
        name="Altura del Zócalo",
        description="Altura del anillo de soporte del mástil sobre el piso (mm)",
        default=15.0,
        min=2.0,
        update=update_no_sync
    )
    
    mast_y_offset: bpy.props.FloatProperty(
        name="Desplazamiento Y (Mástil)",
        description="Desplaza el mástil hacia adelante o atrás",
        default=0.0,
        update=update_no_sync
    )
    
    generate_railings: bpy.props.BoolProperty(
        name="Generar Barandas",
        description="Genera barandas en la cubierta superior o en los bordes",
        default=True,
        update=update_no_sync
    )
    
    railing_height: bpy.props.FloatProperty(
        name="Altura de Baranda",
        description="Altura de la baranda en mm",
        default=12.0,
        min=5.0,
        update=update_no_sync
    )
    
    railing_thickness: bpy.props.FloatProperty(
        name="Grosor de Baranda",
        description="Grosor estructural de la baranda (ideal 2-3mm para FDM)",
        default=2.5,
        min=1.0,
        update=update_no_sync
    )
    
    railing_offset_inward: bpy.props.FloatProperty(
        name="Desplazamiento al Centro",
        description="Mueve las barandas hacia el centro para evitar que sobresalgan del casco",
        default=0.5,
        min=0.0,
        max=5.0,
        update=update_no_sync
    )
    
    railing_spacing: bpy.props.FloatProperty(
        name="Espaciado de Postes",
        description="Distancia entre postes verticales en mm",
        default=20.0,
        min=5.0,
        update=update_no_sync
    )

    has_trapdoor: bpy.props.BoolProperty(
        name="Trampilla a Bodega",
        description="Genera una perforación en el piso y una tapa para acceder a niveles inferiores",
        default=False,
        update=update_no_sync
    )
    
    trapdoor_size: bpy.props.FloatProperty(
        name="Tamaño (Casillas)",
        description="Tamaño de la trampilla medido en grilla de combate",
        default=1.0,
        min=0.5,
        update=update_no_sync
    )
    
    trapdoor_y_offset: bpy.props.FloatProperty(
        name="Desplazamiento Y (Trampilla)",
        description="Desplaza la trampilla hacia adelante o atrás",
        default=0.0,
        update=update_no_sync
    )

classes = [
    StairItem,
    AccessoryItem,
    ShipGeneratorProperties
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


