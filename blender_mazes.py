import bpy
import sys
import os

#https://b3d.interplanety.org/en/how-to-create-mesh-through-the-blender-python-api/

# https://blenderartists.org/t/another-import-error-no-module-named-problem/586049/5
sys.path.append('/home/andrew/Code/Python/maze_algos/')
#maze = bpy.data.texts["maze.py"].as_module()
#maze3d = bpy.data.texts["maze3d.py"].as_module()
import maze
import maze3d
import random
#random.seed(1780)
random.seed(7331)




def add_mesh(name, verticies, edges=[], faces=[]):
    new_mesh = bpy.data.meshes.new(name)
    new_mesh.from_pydata(verticies, edges, faces)
    if new_mesh.validate():
        print('Invalid mesh')
        return
    new_mesh.update()
    new_object = bpy.data.objects.new(name, new_mesh)
    new_collection = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(new_collection)
    new_collection.objects.link(new_object)




def create_mesh(name, verts=[], edges=[], faces=[], validate=True):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, edges, faces)
    if validate:
        if mesh.validate():
            print('Invalid mesh')
            return
    return mesh


def attach_mesh(name, mesh):
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return obj


def new_mesh_obj(mesh_name, verts, edges=[], faces=[], obj_name=None, validate=True):
    if not obj_name:
        obj_name = mesh_name
    mesh = create_mesh(mesh_name, verts, edges, faces, validate)
    obj = attach_mesh(obj_name, mesh)
    return obj

# Expects 6 maze grids, which must all have the same number of rows and columns
def create_cubic_maze(cube: maze3d.Cube, name="cubic_maze", show_outer_faces=False, joined=True, inner_cube=True, inset=0.0):
    grids = cube.split_cube(inset)
    assert len(grids) == 6
    assert grids[0].rows == grids[1].cols
    for i in range(5):
        assert grids[i].rows == grids[i+1].rows
        assert grids[i].cols == grids[i+1].cols
    
    rows = grids[0].rows
    cols = grids[0].cols
    midx = cols / 2
    midy = rows / 2
    
    objs = []
    
    for i, grid in enumerate(grids):
        verts, faces = grid.generate_cube_face(show_outer_faces)
        verts = maze3d.center_maze(grid, verts)
        verts = grid.reorient_cube_face(i, verts)
        mesh = new_mesh_obj(name+'__face_'+str(i), verts=verts, faces=faces)
        objs.append(mesh)
    if inner_cube:
        bpy.ops.mesh.primitive_cube_add(size=grids[0].rows)
        cube = bpy.context.selected_objects[0]
        cube.name = name + '__inner_cube'        
        objs.append(cube)
    if not joined:
        return objs
    else:
        join_meshes(objs)
        return 

def join_meshes(objs: list):
    ctx = bpy.context.copy()
    ctx['active_object'] = objs[0]
    ctx['selected_editable_objects'] = objs
    result = bpy.ops.object.join(ctx)
    name = objs[0].name.rsplit('__face_0', 1)
    name = ''.join(name)
    objs[0].name = name
    return result

rows = 6
cols = 6
grid = maze3d.Cube(rows=rows, cols=cols, clear=False)
maze.growing_tree(grid)
grid.render2d('/home/andrew/Code/Python/maze_algos/imgs/cube.png', frame_size=0,
              border_color=(0, 0, 0, 255),
              block_color=(255, 255, 255, 0),
              grid_bg=(255, 255, 255, 0),
              text_color=(55, 55, 55, 100))
# grids = grid.split_cube(inset=0.25)
objs = create_cubic_maze(grid, show_outer_faces=False, joined=True, inner_cube=False, inset=0.0)
#grid = maze3d.RectGrid3d()
#maze.growing_tree(grid)
#verts, faces = grid.generate_model(show_outer_faces=True)
#new_mesh_obj('cube3d', verts, [], faces)


