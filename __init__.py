bl_info = {
    "name": "Procedural Ship Generator",
    "author": "Jarvis",
    "version": (1, 12, 42),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > Procedural Ship",
    "description": "Generador de barcos D&D modulares, paramétricos y listos para FDM.",
    "warning": "",
    "category": "Add Mesh",
}

if "bpy" in locals():
    import importlib
    importlib.reload(ship_properties)
    importlib.reload(ui_panel)
    importlib.reload(ship_generator)
else:
    from . import ship_properties
    from . import ui_panel
    from . import ship_generator

import bpy

modules = [
    ship_properties,
    ship_generator,
    ui_panel,
]

def register():
    bpy.types.Scene.ship_generator_error = bpy.props.StringProperty(name="Last Error", default="")
    bpy.types.Scene.ship_default_race = bpy.props.EnumProperty(
        name="Raza por Defecto",
        description="Selecciona la raza base antes de generar el barco",
        items=[
            ('SMALL', "Mediano / Aasimar Peq. (25mm)", "Escala 0.68x"),
            ('GNOME', "Gnomo (27mm)", "Escala 0.73x"),
            ('DWARF', "Enano (32mm)", "Escala 0.86x"),
            ('HUMAN', "Humano / Elfo (37mm)", "Escala 1.0x base"),
            ('LARGE', "SemiOrco / Tiefling (40mm)", "Escala 1.08x"),
            ('GOLIATH', "Goliath (42mm)", "Escala 1.14x")
        ],
        default='HUMAN'
    )
    for mod in modules:
        if hasattr(mod, 'register'):
            mod.register()
        
    bpy.types.Object.ship_generator = bpy.props.PointerProperty(type=ship_properties.ShipGeneratorProperties)

def unregister():
    if hasattr(bpy.types.Scene, 'ship_generator_error'):
        del bpy.types.Scene.ship_generator_error
    if hasattr(bpy.types.Scene, 'ship_default_race'):
        del bpy.types.Scene.ship_default_race
    del bpy.types.Object.ship_generator
    
    for mod in reversed(modules):
        if hasattr(mod, 'unregister'):
            mod.unregister()

if __name__ == "__main__":
    register()




















