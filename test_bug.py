import bpy
import sys
import os

# Add addon path to sys.path so we can import it
addon_dir = r"C:\agente_threadwell\blender addons\procedural_ship_generator"
if addon_dir not in sys.path:
    sys.path.append(addon_dir)

from procedural_ship_generator import ship_generator

class MockProps:
    ship_length = 4.0
    tiles_width = 2.90
    tiles_length = 4.0
    wall_height = 40.0
    wall_thickness = 5.0
    floor_thickness = 5.0
    deck_elevation = 25.0
    tolerance = 0.4
    generate_plank_cuts = False
    generate_floor_planks = True
    generate_top_deck = True
    generate_railings = True
    railing_height = 12.0
    railing_thickness = 2.5
    railing_spacing = 20.0
    generate_stairs = False
    has_forecastle = False
    has_quarterdeck = False
    has_mast = False
    has_trapdoor = False
    has_grid = True
    section_type = 'MID'

try:
    mesh = bpy.data.meshes.new("Test_Mesh")
    obj = bpy.data.objects.new("Test", mesh)
    bpy.context.collection.objects.link(obj)
    
    # We need to monkey-patch the props since it reads from obj.ship_generator
    # Actually obj.ship_generator doesn't exist unless the addon is enabled
    # We can just mock the whole rebuild_ship_mesh logic by passing MockProps!
    # Wait, rebuild_ship_mesh expects obj, and reads obj.ship_generator
    # So let's patch rebuild_ship_mesh to read our mock props!
    
    # We can just change ship_generator.py temporarily? No, don't touch it.
    # We can enable the addon in blender first!
    bpy.ops.preferences.addon_enable(module="procedural_ship_generator")
    
    obj.ship_generator.is_ship = True
    obj.ship_generator.tiles_width = 2.90
    obj.ship_generator.generate_top_deck = False
    obj.ship_generator.generate_floor_planks = True
    obj.ship_generator.generate_railings = True
    
    ship_generator.rebuild_ship_mesh(obj)
    print("SUCCESS")
except Exception as e:
    import traceback
    traceback.print_exc()
    print("FAILED")
