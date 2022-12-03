

'''
Based on: https://blender.stackexchange.com/a/168967
  which was an answer to this stackexchange question: https://blender.stackexchange.com/questions/82480/how-to-make-a-mobius-strip
  and which was based on: https://blender.stackexchange.com/a/82489
    which can also be found at: http://web.purplefrog.com/%7Ethoth/blender/python-cookbook/mobius-strip.html
'''
import math
import random
import maze3d
import maze
import bpy
from math import *
from mathutils import *
import sys
import os
sys.path.append(os.path.join(os.path.expanduser('~'),
                'Code', 'Python', 'maze_algos'))

stop_row = 9

# Take a MobiusGrid and produce a 3d mesh
#   Both sides of the mobius strip are iterated simultaneously.  Row iteration should
#   begin at 0 and rows/2 in order to add both sides in one step.


def mobius_maze_mesh(grid, major_radius=5, minor_radius=1, thick=0.1, height=0.25, validate=True, smooth=False):
    # resolution must be an odd number because there are an even number of faces on the mesh
    rows = grid.rows
    cols = grid.cols
    assert rows % 2 == 0
    assert cols >= 2
    assert rows > cols

    half = int(rows / 2)
    resolution = half
    w = minor_radius * 2 / cols
    c1 = Vector([major_radius, 0, 0])
    verts = []
    faces = []
    # number of wall verticies added for each loop iteration (outer floor, outer ceiling, inner floor, inner ceiling)
    col_verts = 4

    # Each loop iteration step generates two rows of the maze (one on the front of the strip and one on the back)
    #   Moves in a counter-clockwise direction starting at (major_radius, 0, 0) in the 3d coordinate space
    for i in range(resolution):
        row0 = i
        row1 = half + i
        not_at_last_row = i+1 < resolution

        # See also: Spherical Coordinate System
        #   https://en.wikipedia.org/wiki/Spherical_coordinate_system
        theta = 2*pi * i/resolution  # Theta goes along major radius
        phi = pi * i/resolution     # Phi goes along minor radius
        # Rotates along major radius
        rot_theta = Matrix.Rotation(theta, 3, [0, 0, 1])
        # Rotates along minor radius
        rot_phi = Matrix.Rotation(phi, 3, [0, 1, 0])

        # Verticies for external wall floors
        # Inner base top vert
        v0 = apply(rot_theta, c1 + apply(rot_phi,
                   Vector((-thick / 2, 0, minor_radius))))
        # Outer base top vert
        v1 = apply(
            rot_theta, (c1 + apply(rot_phi, Vector((thick / 2, 0, minor_radius)))))
        # Outer base bottom vert
        v2 = apply(
            rot_theta, (c1 + apply(rot_phi, Vector((thick / 2, 0, -minor_radius)))))
        # Inner base bottom vert
        v3 = apply(
            rot_theta, (c1 + apply(rot_phi, Vector((-thick / 2, 0, -minor_radius)))))
        # Verticies for external wall ceilings
        # Add external wall vert starting at inner top and ending at outer bottom - uses v1
        v4 = apply(rot_theta, (c1 + apply(rot_phi,
                   Vector((-thick / 2 - height, 0, minor_radius)))))
        # Add wall vert starting at outer top and ending at inner bottom - uses v2
        v5 = apply(
            rot_theta, (c1 + apply(rot_phi, Vector((thick / 2 + height, 0, minor_radius)))))
        # Add wall vert starting at outer bottom and ending at inner top - uses v3
        v6 = apply(rot_theta, (c1 + apply(rot_phi,
                   Vector((thick / 2 + height, 0, -minor_radius)))))
        # Add wall vert starting at inner bottom and ending at outer top - uses v4
        v7 = apply(rot_theta, (c1 + apply(rot_phi,
                   Vector((-thick / 2 - height, 0, -minor_radius)))))
        idx = len(verts)
        new_verts = [v0, v1, v2, v3, v4, v5, v6, v7]
        # number of verticies in the base of the mobius strip (excluding walls)
        base = len(new_verts)

        # Add verticies for internal walls
        for col in range(1, cols):
            offset = w * col
            # outer floors
            cv0 = apply(rot_theta, (c1 + apply(rot_phi,
                        Vector((-thick / 2, 0, minor_radius - offset)))))
            cv1 = apply(rot_theta, (c1 + apply(rot_phi, Vector((-thick /
                        2 - height, 0, minor_radius - offset)))))   # outer ceilings
            # inner floor
            cv2 = apply(
                rot_theta, (c1 + apply(rot_phi, Vector((thick / 2, 0, minor_radius - offset)))))
            cv3 = apply(rot_theta, (c1 + apply(rot_phi, Vector((thick /
                        2 + height, 0, minor_radius - offset)))))    # inner ceilings
            new_verts.extend([cv0, cv1, cv2, cv3])
        num = len(new_verts)    # total number of new verticies to add
        verts.extend(new_verts)

        # Find index positions of the new verts in the `verts[]` list
        i0 = idx+num+0 if not_at_last_row else 2
        i1 = idx+num+1 if not_at_last_row else 3
        i2 = idx+num+2 if not_at_last_row else 0
        i3 = idx+num+3 if not_at_last_row else 1
        i4 = idx+num+4 if not_at_last_row else 6
        i5 = idx+num+5 if not_at_last_row else 7
        i6 = idx+num+6 if not_at_last_row else 4
        i7 = idx+num+7 if not_at_last_row else 5

        # Add faces that are always rendered
        faces.append([idx+0, idx+1, i1, i0])  # base - edge thickness face top
        faces.append([idx+1, idx+2, i2, i1])  # base - outer face
        # base - edge thickness face bottom
        faces.append([idx+2, idx+3, i3, i2])
        faces.append([idx+3, idx+0, i0, i3])  # base - inner face
        faces.append([idx+5, idx+1, i1, i5])  # exterior wall - top outer
        faces.append([idx+6, idx+2, i2, i6])  # exterior wall - bottom outer
        faces.append([idx+0, idx+4, i4, i0])  # exterior wall - top inner
        faces.append([idx+3, idx+7, i7, i3])  # exterior wall - bottom inner

        # Conditional wall faces
        cn = idx + num - col_verts
        if i == stop_row:
            # iterate outer cells in reverse column order
            outer_cell = grid.get(row=row0, col=cols-1)
            inner_cell = grid.get(row=row1, col=0)
            print(f'stopping: outer={outer_cell.id} inner={inner_cell.id}')
            continue
        for col in range(cols):
            col_offset = col * col_verts
            c0 = ((cols-col) * col_verts)
            cv0 = idx + base + ((col-1)*col_verts)  # next column offset
            c = idx + base + col_offset             # current row offset
            n = idx + base + col_offset + num       # next row offset
            match col:
                case 0:
                    outer_next_row = [idx+1, idx+5, idx+base+3, idx+base+2]
                    inner_next_row = [idx+0, idx+4, idx+base+1, idx+base+0]
                case x if x == cols-1:
                    outer_next_row = [idx+2, idx+6, cn+3, cn+2]
                    inner_next_row = [idx+3, idx+7, cn+1, cn+0]
                case _:
                    outer_next_row = [cv0+2, cv0+3, c+3, c+2]
                    inner_next_row = [cv0+0, cv0+1, c+1, c+0]
            match not_at_last_row:
                case True:
                    outer_next_col = [c+3, c+2, n+2, n+3]
                    inner_next_col = [c+1, c+0, n+0, n+1]
                case False:
                    outer_next_col = [c0+0, c0+1, c+3, c+2]
                    inner_next_col = [c0+3, c0+2, c+0, c+1]
            # iterate outer cells in reverse column order
            outer_cell = grid.get(row=row0, col=cols-1-col)
            inner_cell = grid.get(row=row1, col=col)
            if not outer_cell.linked_north():
                faces.append(outer_next_row)
            if not inner_cell.linked_north():
                faces.append(inner_next_row)
            if col != cols-1:
                outer_cell = grid.get(row=row0, col=cols-1-col-1)
                if not outer_cell.linked_east():
                    faces.append(outer_next_col)
                if not inner_cell.linked_east():
                    faces.append(inner_next_col)

    mesh = bpy.data.meshes.new("mobius")
    mesh.from_pydata(verts, [], faces)
    if validate:
        if mesh.validate():
            print('Invalid mesh')
            return

    if smooth:
        for p in mesh.polygons:
            p.use_smooth = True

    return mesh


def apply(matrix, vector):
    '''
    apply(matrix, vector) -> vector

    this function receives a matrix and a vector and returns
    the vector obtained by multipling both of them
    '''
    V_0 = vector @ matrix[0]
    V_1 = vector @ matrix[1]
    V_2 = vector @ matrix[2]
    return Vector((V_0, V_1, V_2))


def generate_mobius_maze(grid, rows, cols, major_radius=5, minor_radius=1, thick=0.1, height=0.25, validate=True, smooth=False):
    me = mobius_maze_mesh(grid, major_radius=major_radius,
                          minor_radius=minor_radius, thick=thick, height=height, validate=validate)
    ob = bpy.data.objects.new("Mobius Mesh", me)
    bpy.context.collection.objects.link(ob)


random.seed(1778)
rows = 108
res = 54
cols = 10

grid = maze.Mobius(rows=rows, cols=cols, clear=False)
maze.growing_tree(grid)
grid.render2d("imgs/mobius_2d_large.png")
generate_mobius_maze(grid, rows=rows, cols=cols,
                     minor_radius=2, height=0.05, smooth=True)
