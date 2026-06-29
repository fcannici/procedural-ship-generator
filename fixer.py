import re
import os

with open('ship_generator.py', 'r', encoding='utf-8') as f:
    content = f.read()
    
# Remove all imports from the body
content = re.sub(r'^[ \t]*import (math|bmesh|mathutils|random|bpy)\r?\n', '', content, flags=re.MULTILINE)

# Find where the duplicate ensure_cutter starts inside rebuild_ship_mesh
# It starts right after ensure_cutter(obj, props, l2, bot_w2, mid_w2, top_w2, mid_h, h)
match = re.search(r'    ensure_cutter\(obj, props, l2, bot_w2, mid_w2, top_w2, mid_h, h\)\r?\n', content)
if match:
    end_of_call = match.end()
    
    # Everything after this is the body of ensure_cutter
    cutter_body = content[end_of_call:]
    
    # We remove this body from inside rebuild_ship_mesh
    content = content[:end_of_call]
    
    # Now we construct the proper function definition for ensure_cutter
    cutter_def = '''

def ensure_cutter(obj, props, l2, bot_w2, mid_w2, top_w2, mid_h, h):
    def apply_modifier_safely(target_obj, mod_name):
        mod = target_obj.modifiers.get(mod_name)
        if not mod: return
        depsgraph = bpy.context.evaluated_depsgraph_get()
        depsgraph.update()
        target_eval = target_obj.evaluated_get(depsgraph)
        mesh_eval = target_eval.to_mesh()
        target_obj.modifiers.remove(mod)
        bm_eval = bmesh.new()
        bm_eval.from_mesh(mesh_eval)
        target_obj.data.clear_geometry()
        bm_eval.to_mesh(target_obj.data)
        bm_eval.free()
        target_eval.to_mesh_clear()
'''
    
    content = content + cutter_def + cutter_body

# Add imports to the top
imports = 'import bpy\nimport bmesh\nimport math\nimport mathutils\nimport random\n'
content = imports + content

with open('ship_generator.py', 'w', encoding='utf-8') as f:
    f.write(content)
