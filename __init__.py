bl_info = {
    "name": "Procedural Ship Generator",
    "author": "Jarvis",
    "version": (1, 10, 20),
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
    for mod in modules:
        if hasattr(mod, 'register'):
            mod.register()
        
    bpy.types.Object.ship_generator = bpy.props.PointerProperty(type=ship_properties.ShipGeneratorProperties)

def unregister():
    del bpy.types.Object.ship_generator
    
    for mod in reversed(modules):
        if hasattr(mod, 'unregister'):
            mod.unregister()

if __name__ == "__main__":
    register()
