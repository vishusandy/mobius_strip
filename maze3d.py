from ast import Num
from maze import RectCell, RectGrid
from typing import Callable
import copy
import maze
import random
import sys
# import unittest
# import pytest
from PIL import Image, ImageDraw, ImageFont


class VertState:
    def __init__(self, log=False):
        self.log = log
        self.verts = []
        self.vdict = {}

    def lookup(self, v):
        i = self.vdict.get(v)
        if i == None:
            if self.log:
                print(f'adding {v}')
            self.verts.append(v)
            pos = len(self.verts)-1
            self.vdict[v] = pos
            if self.log:
                print(f'verts={self.verts}')
                print(f'vdict={self.vdict}')
            return pos
        else:
            if self.log:
                print(f'found {v}')
            return i


class RectCell3d(RectCell):
    def __init__(self, rows, cols, levels, cap2d, cap3d, id, row, col, level, weight=1, masked=False, clear=False, inset=0):
        assert inset >= 0 and inset <= 0.45
        self.id = id
        self.row = row
        self.col = col
        self.level = level
        self.links = []
        self.masked = masked
        self.weight = weight
        self.inset = inset
        self.calc_neighbors_3d(rows, cols, levels, cap2d)
        if clear:
            self.links.extend(self.neighbors_3d())

    def flatten_cell(self, inset=0.0):
        new = copy.copy(self)
        new.level = 0
        new.inset = inset
        new.above = None
        new.below = None
        return new

    def string(self):
        return f'''id={self.id} row={self.row} col={self.col} level={self.level} links={self.links} masked={self.masked} weight={self.weight}
        n={self.north} e={self.east} s={self.south} w={self.west} above={self.above} below={self.below}'''

    def calc_neighbors_3d(self, rows, cols, levels, cap2d):
        n = self.id - cols  # was using rows here, why?
        e = self.id + 1
        s = self.id + cols  # was using rows here, why?
        w = self.id - 1
        a = self.id + cap2d
        b = self.id - cap2d
        self.north = n if self.row > 0 else None
        self.east = e if not self.col >= cols-1 else None
        self.south = s if not self.row >= rows-1 else None
        self.west = w if self.col > 0 else None
        self.above = a if self.level < levels - 1 else None
        self.below = b if self.level > 0 else None

    # Neighbor Methods

    def neighbors_3d(self):
        return list(filter(lambda d: d != None, [
            self.north, self.east, self.south, self.west, self.above, self.below]))

    def neighbors_2d(self):
        return list(filter(lambda d: not d is None, [
            self.north, self.east, self.south, self.west]))

    def neighbors(self):
        return self.neighbors_3d()

    # Link methods

    def linked_above(self):
        return self.linked_to(self.above)

    def linked_below(self):
        return self.linked_to(self.below)

    def has_links(self):
        return self.north in self.links or self.east in self.links or self.south in self.links or self.west in self.links

    def has_links_3d(self):
        return len(self.links) != 0

    def show_above_wall(self):
        return self.above == None or not self.linked_to(self.above)

    def show_below_wall(self):
        return self.below == None or not self.linked_to(self.below)

    def has_neighbor_at(self, dir):
        match dir:
            case 'above': return self.above != None
            case 'below': return self.below != None
            case 'north': return self.north != None
            case 'east': return self.east != None
            case 'south': return self.south != None
            case 'west': return self.west != None

    def linked_at(self, dir):
        match dir:
            case 'above': return self.linked_above()
            case 'below': return self.linked_below()
            case 'north': return self.linked_north()
            case 'east': return self.linked_east()
            case 'south': return self.linked_south()
            case 'west': return self.linked_west()

    def is_edge(self, grid, dir):
        match dir:
            case 'above': return self.level == grid.levels - 1
            case 'below': return self.level == 0
            case 'north': return self.row == 0
            case 'east': return self.col == grid.cols - 1
            case 'south': return self.row == grid.rows - 1
            case 'west': return self.col == 0

    def show_wall(self, dir):
        match dir:
            case 'above': return self.show_above_wall()
            case 'below': return self.show_below_wall()
            case 'north': return self.show_north_wall()
            case 'east': return self.show_east_wall()
            case 'south': return self.show_south_wall()
            case 'west': return self.show_west_wall()

    # Verticies

    def vswb(self):
        return vert_pos(self.col, self.row+1, self.level)

    def vseb(self):
        return vert_pos(self.col+1, self.row+1, self.level)

    def vswa(self):
        return vert_pos(self.col, self.row+1, self.level+1)

    def vsea(self):
        return vert_pos(self.col+1, self.row+1, self.level+1)

    def vnwb(self):
        return vert_pos(self.col, self.row, self.level)

    def vneb(self):
        return vert_pos(self.col+1, self.row, self.level)

    def vnwa(self):
        return vert_pos(self.col, self.row, self.level+1)

    def vnea(self):
        return vert_pos(self.col+1, self.row, self.level+1)

    # Inset verticies

    def vix0(self):
        return self.col
        # return self.neg0(self.col, self.inset)

    def vix1(self):
        return self.col + self.inset
        # return self.neg1(self.col, self.inset)

    def vix2(self):
        return self.col + 1 - self.inset
        # return self.neg2(self.col, self.inset)

    def vix3(self):
        return self.col + 1
        # # return self.neg3(self.col, self.inset)

    def viy0(self):
        # return self.row
        return self.neg0(self.row, self.inset)

    def viy1(self):
        # return self.row + self.inset
        return self.neg1(self.row, self.inset)

    def viy2(self):
        # return self.row + 1 - self.inset
        return self.neg2(self.row, self.inset)

    def viy3(self):
        # return self.row + 1
        return self.neg3(self.row, self.inset)

    def viz0(self):
        return self.level

    def viz1(self):
        return self.level + self.inset

    def viz2(self):
        return self.level + 1 - self.inset

    def viz3(self):
        return self.level + 1

    def vx_left_inner(self):
        return self.vix1()

    def vx_right_inner(self):
        return self.vix2()

    def vx_left_outer(self):
        return self.vix0()

    def vx_right_outer(self):
        return self.vix3()

    def vy_top_inner(self):
        return self.viy1()

    def vy_bottom_inner(self):
        return self.viy2()

    def vy_top_outer(self):
        return self.viy0()

    def vy_bottom_outer(self):
        return self.viy3()

    def vz_top_inner(self):
        return self.viz2()

    def vz_bottom_inner(self):
        return self.viz1()

    def vz_top_outer(self):
        return self.viz3()

    def vz_bottom_outer(self):
        return self.viz0()

    def neg0(self, loc, inset=0):
        return 0 - loc

    def neg1(self, loc, inset=0):
        return 0 - loc - self.inset

    def neg2(self, loc, inset=0):
        return 0 - loc - 1 + inset

    def neg3(self, loc, inset=0):
        return 0 - loc - 1

    # Face methods (that reference verticies in a list by their index position, which is found via dicitonary)

    def face_below(self, vdict):
        return [vdict[self.vswb()], vdict[self.vseb()], vdict[self.vneb()], vdict[self.vnwb()]]

    def face_above(self, vdict):
        return [vdict[self.vswa()], vdict[self.vsea()], vdict[self.vnea()], vdict[self.vnwa()]]

    def face_north(self, vdict):
        return [vdict[self.vnwb()], vdict[self.vneb()], vdict[self.vnea()], vdict[self.vnwa()]]

    def face_south(self, vdict):
        return [vdict[self.vswb()], vdict[self.vseb()], vdict[self.vsea()], vdict[self.vswa()]]

    def face_west(self, vdict):
        return [vdict[self.vswb()], vdict[self.vswa()], vdict[self.vnwa()], vdict[self.vnwb()]]

    def face_east(self, vdict):
        return [vdict[self.vseb()], vdict[self.vsea()], vdict[self.vnea()], vdict[self.vneb()]]

    def side_below(self, state):
        return [
            state.lookup(
                (self.vx_left_outer(), self.vy_top_outer(), self.vz_top_outer())),
            state.lookup(
                (self.vx_right_outer(), self.vy_top_outer(), self.vz_top_outer())),
            state.lookup(
                (self.vx_right_outer(), self.vy_bottom_outer(), self.vz_top_outer())),
            state.lookup(
                (self.vx_left_outer(), self.vy_bottom_outer(), self.vz_top_outer())),
        ]

    def side_above(self, state):
        return [
            state.lookup(
                (self.vx_left_outer(), self.vy_top_outer(), self.vz_top_outer())),
            state.lookup(
                (self.vx_right_outer(), self.vy_top_outer(), self.vz_top_outer())),
            state.lookup(
                (self.vx_right_outer(), self.vy_bottom_outer(), self.vz_top_outer())),
            state.lookup(
                (self.vx_left_outer(), self.vy_bottom_outer(), self.vz_top_outer())),
        ]

    def side_west(self, state):
        return [
            state.lookup(
                (self.vx_left_outer(), self.vy_top_outer(), self.vz_top_outer())),
            state.lookup(
                (self.vx_left_outer(), self.vy_bottom_outer(), self.vz_top_outer())),
            state.lookup(
                (self.vx_left_outer(), self.vy_bottom_outer(), self.vz_bottom_outer())),
            state.lookup(
                (self.vx_left_outer(), self.vy_top_outer(), self.vz_bottom_outer())),
        ]

    def side_east(self, state):
        return [
            state.lookup(
                (self.vx_right_outer(), self.vy_top_outer(), self.vz_top_outer())),
            state.lookup(
                (self.vx_right_outer(), self.vy_bottom_outer(), self.vz_top_outer())),
            state.lookup(
                (self.vx_right_outer(), self.vy_bottom_outer(), self.vz_bottom_outer())),
            state.lookup(
                (self.vx_right_outer(), self.vy_top_outer(), self.vz_bottom_outer())),
        ]

    def side_north(self, state):
        return [
            state.lookup(
                (self.vx_left_outer(), self.vy_top_outer(), self.vz_top_outer())),
            state.lookup(
                (self.vx_right_outer(), self.vy_top_outer(), self.vz_top_outer())),
            state.lookup(
                (self.vx_right_outer(), self.vy_top_outer(), self.vz_bottom_outer())),
            state.lookup(
                (self.vx_left_outer(), self.vy_top_outer(), self.vz_bottom_outer())),
        ]

    def side_south(self, state):
        return [
            state.lookup(
                (self.vx_left_outer(), self.vy_bottom_outer(), self.vz_top_outer())),
            state.lookup(
                (self.vx_right_outer(), self.vy_bottom_outer(), self.vz_top_outer())),
            state.lookup(
                (self.vx_right_outer(), self.vy_bottom_outer(), self.vz_bottom_outer())),
            state.lookup(
                (self.vx_left_outer(), self.vy_bottom_outer(), self.vz_bottom_outer())),
        ]

    # Inset face methods

    def inset_faces_above(self, state):
        w = [
            state.lookup(
                (self.vx_left_inner(), self.vy_top_inner(), self.vz_top_inner())),
            state.lookup(
                (self.vx_left_inner(), self.vy_bottom_inner(), self.vz_top_inner())),
            state.lookup(
                (self.vx_left_inner(), self.vy_bottom_inner(), self.vz_top_outer())),
            state.lookup(
                (self.vx_left_inner(), self.vy_top_inner(), self.vz_top_outer())),
        ]

        e = [
            state.lookup(
                (self.vx_right_inner(), self.vy_top_inner(), self.vz_top_inner())),
            state.lookup(
                (self.vx_right_inner(), self.vy_bottom_inner(), self.vz_top_inner())),
            state.lookup(
                (self.vx_right_inner(), self.vy_bottom_inner(), self.vz_top_outer())),
            state.lookup(
                (self.vx_right_inner(), self.vy_top_inner(), self.vz_top_outer())),
        ]

        n = [
            state.lookup(
                (self.vx_left_inner(), self.vy_top_inner(), self.vz_top_inner())),
            state.lookup(
                (self.vx_right_inner(), self.vy_top_inner(), self.vz_top_inner())),
            state.lookup(
                (self.vx_right_inner(), self.vy_top_inner(), self.vz_top_outer())),
            state.lookup(
                (self.vx_left_inner(), self.vy_top_inner(), self.vz_top_outer())),
        ]

        s = [
            state.lookup(
                (self.vx_left_inner(), self.vy_bottom_inner(), self.vz_top_inner())),
            state.lookup(
                (self.vx_right_inner(), self.vy_bottom_inner(), self.vz_top_inner())),
            state.lookup(
                (self.vx_right_inner(), self.vy_bottom_inner(), self.vz_top_outer())),
            state.lookup(
                (self.vx_left_inner(), self.vy_bottom_inner(), self.vz_top_outer())),
        ]

        return [w, e, n, s]

    def inset_faces_below(self, state):
        w = [
            state.lookup(
                (self.vx_left_inner(), self.vy_top_inner(), self.vz_bottom_inner())),
            state.lookup(
                (self.vx_left_inner(), self.vy_bottom_inner(), self.vz_bottom_inner())),
            state.lookup(
                (self.vx_left_inner(), self.vy_bottom_inner(), self.vz_bottom_outer())),
            state.lookup(
                (self.vx_left_inner(), self.vy_top_inner(), self.vz_bottom_outer())),
        ]

        e = [
            state.lookup(
                (self.vx_right_inner(), self.vy_top_inner(), self.vz_bottom_inner())),
            state.lookup(
                (self.vx_right_inner(), self.vy_bottom_inner(), self.vz_bottom_inner())),
            state.lookup(
                (self.vx_right_inner(), self.vy_bottom_inner(), self.vz_bottom_outer())),
            state.lookup(
                (self.vx_right_inner(), self.vy_top_inner(), self.vz_bottom_outer())),
        ]

        n = [
            state.lookup(
                (self.vx_left_inner(), self.vy_top_inner(), self.vz_bottom_inner())),
            state.lookup(
                (self.vx_right_inner(), self.vy_top_inner(), self.vz_bottom_inner())),
            state.lookup(
                (self.vx_right_inner(), self.vy_top_inner(), self.vz_bottom_outer())),
            state.lookup(
                (self.vx_left_inner(), self.vy_top_inner(), self.vz_bottom_outer())),
        ]

        s = [
            state.lookup(
                (self.vx_left_inner(), self.vy_bottom_inner(), self.vz_bottom_inner())),
            state.lookup(
                (self.vx_right_inner(), self.vy_bottom_inner(), self.vz_bottom_inner())),
            state.lookup(
                (self.vx_right_inner(), self.vy_bottom_inner(), self.vz_bottom_outer())),
            state.lookup(
                (self.vx_left_inner(), self.vy_bottom_inner(), self.vz_bottom_outer())),
        ]

        return [w, e, n, s]

    def inset_faces_west(self, state):
        n = [
            state.lookup(
                (self.vx_left_outer(), self.vy_top_inner(), self.vz_bottom_inner())),
            state.lookup(
                (self.vx_left_inner(), self.vy_top_inner(), self.vz_bottom_inner())),
            state.lookup(
                (self.vx_left_inner(), self.vy_top_inner(), self.vz_top_inner())),
            state.lookup(
                (self.vx_left_outer(), self.vy_top_inner(), self.vz_top_inner())),
        ]

        s = [
            state.lookup(
                (self.vx_left_outer(), self.vy_bottom_inner(), self.vz_bottom_inner())),
            state.lookup(
                (self.vx_left_inner(), self.vy_bottom_inner(), self.vz_bottom_inner())),
            state.lookup(
                (self.vx_left_inner(), self.vy_bottom_inner(), self.vz_top_inner())),
            state.lookup(
                (self.vx_left_outer(), self.vy_bottom_inner(), self.vz_top_inner())),
        ]

        a = [
            state.lookup(
                (self.vx_left_outer(), self.vy_top_inner(), self.vz_top_inner())),
            state.lookup(
                (self.vx_left_inner(), self.vy_top_inner(), self.vz_top_inner())),
            state.lookup(
                (self.vx_left_inner(), self.vy_bottom_inner(), self.vz_top_inner())),
            state.lookup(
                (self.vx_left_outer(), self.vy_bottom_inner(), self.vz_top_inner())),
        ]

        b = [
            state.lookup(
                (self.vx_left_outer(), self.vy_top_inner(), self.vz_bottom_inner())),
            state.lookup(
                (self.vx_left_inner(), self.vy_top_inner(), self.vz_bottom_inner())),
            state.lookup(
                (self.vx_left_inner(), self.vy_bottom_inner(), self.vz_bottom_inner())),
            state.lookup(
                (self.vx_left_outer(), self.vy_bottom_inner(), self.vz_bottom_inner())),
        ]

        return [n, s, a, b]

    def inset_faces_east(self, state):
        n = [
            state.lookup(
                (self.vx_right_outer(), self.vy_top_inner(), self.vz_bottom_inner())),
            state.lookup(
                (self.vx_right_inner(), self.vy_top_inner(), self.vz_bottom_inner())),
            state.lookup(
                (self.vx_right_inner(), self.vy_top_inner(), self.vz_top_inner())),
            state.lookup(
                (self.vx_right_outer(), self.vy_top_inner(), self.vz_top_inner())),
        ]

        s = [
            state.lookup(
                (self.vx_right_outer(), self.vy_bottom_inner(), self.vz_bottom_inner())),
            state.lookup(
                (self.vx_right_inner(), self.vy_bottom_inner(), self.vz_bottom_inner())),
            state.lookup(
                (self.vx_right_inner(), self.vy_bottom_inner(), self.vz_top_inner())),
            state.lookup(
                (self.vx_right_outer(), self.vy_bottom_inner(), self.vz_top_inner())),
        ]

        a = [
            state.lookup(
                (self.vx_right_outer(), self.vy_top_inner(), self.vz_top_inner())),
            state.lookup(
                (self.vx_right_inner(), self.vy_top_inner(), self.vz_top_inner())),
            state.lookup(
                (self.vx_right_inner(), self.vy_bottom_inner(), self.vz_top_inner())),
            state.lookup(
                (self.vx_right_outer(), self.vy_bottom_inner(), self.vz_top_inner())),
        ]

        b = [
            state.lookup(
                (self.vx_right_outer(), self.vy_top_inner(), self.vz_bottom_inner())),
            state.lookup(
                (self.vx_right_inner(), self.vy_top_inner(), self.vz_bottom_inner())),
            state.lookup(
                (self.vx_right_inner(), self.vy_bottom_inner(), self.vz_bottom_inner())),
            state.lookup(
                (self.vx_right_outer(), self.vy_bottom_inner(), self.vz_bottom_inner())),
        ]

        return [n, s, a, b]

    def inset_faces_north(self, state):
        w = [
            state.lookup(
                (self.vx_left_inner(), self.vy_top_outer(), self.vz_top_inner())),
            state.lookup(
                (self.vx_left_inner(), self.vy_top_inner(), self.vz_top_inner())),
            state.lookup(
                (self.vx_left_inner(), self.vy_top_inner(), self.vz_bottom_inner())),
            state.lookup(
                (self.vx_left_inner(), self.vy_top_outer(), self.vz_bottom_inner())),
        ]

        e = [
            state.lookup(
                (self.vx_right_inner(), self.vy_top_outer(), self.vz_top_inner())),
            state.lookup(
                (self.vx_right_inner(), self.vy_top_inner(), self.vz_top_inner())),
            state.lookup(
                (self.vx_right_inner(), self.vy_top_inner(), self.vz_bottom_inner())),
            state.lookup(
                (self.vx_right_inner(), self.vy_top_outer(), self.vz_bottom_inner())),
        ]

        a = [
            state.lookup(
                (self.vx_left_inner(), self.vy_top_outer(), self.vz_top_inner())),
            state.lookup(
                (self.vx_right_inner(), self.vy_top_outer(), self.vz_top_inner())),
            state.lookup(
                (self.vx_right_inner(), self.vy_top_inner(), self.vz_top_inner())),
            state.lookup(
                (self.vx_left_inner(), self.vy_top_inner(), self.vz_top_inner())),
        ]

        b = [
            state.lookup(
                (self.vx_left_inner(), self.vy_top_outer(), self.vz_bottom_inner())),
            state.lookup(
                (self.vx_right_inner(), self.vy_top_outer(), self.vz_bottom_inner())),
            state.lookup(
                (self.vx_right_inner(), self.vy_top_inner(), self.vz_bottom_inner())),
            state.lookup(
                (self.vx_left_inner(), self.vy_top_inner(), self.vz_bottom_inner())),
        ]

        return [w, e, a, b]

    def inset_faces_south(self, state):
        w = [
            state.lookup(
                (self.vx_left_inner(), self.vy_bottom_inner(), self.vz_top_inner())),
            state.lookup(
                (self.vx_left_inner(), self.vy_bottom_outer(), self.vz_top_inner())),
            state.lookup(
                (self.vx_left_inner(), self.vy_bottom_outer(), self.vz_bottom_inner())),
            state.lookup(
                (self.vx_left_inner(), self.vy_bottom_inner(), self.vz_bottom_inner())),
        ]

        e = [
            state.lookup(
                (self.vx_right_inner(), self.vy_bottom_inner(), self.vz_top_inner())),
            state.lookup(
                (self.vx_right_inner(), self.vy_bottom_outer(), self.vz_top_inner())),
            state.lookup(
                (self.vx_right_inner(), self.vy_bottom_outer(), self.vz_bottom_inner())),
            state.lookup(
                (self.vx_right_inner(), self.vy_bottom_inner(), self.vz_bottom_inner())),
        ]

        a = [
            state.lookup(
                (self.vx_left_inner(), self.vy_bottom_inner(), self.vz_top_inner())),
            state.lookup(
                (self.vx_right_inner(), self.vy_bottom_inner(), self.vz_top_inner())),
            state.lookup(
                (self.vx_right_inner(), self.vy_bottom_outer(), self.vz_top_inner())),
            state.lookup(
                (self.vx_left_inner(), self.vy_bottom_outer(), self.vz_top_inner())),
        ]

        b = [
            state.lookup(
                (self.vx_left_inner(), self.vy_bottom_inner(), self.vz_bottom_inner())),
            state.lookup(
                (self.vx_right_inner(), self.vy_bottom_inner(), self.vz_bottom_inner())),
            state.lookup(
                (self.vx_right_inner(), self.vy_bottom_outer(), self.vz_bottom_inner())),
            state.lookup(
                (self.vx_left_inner(), self.vy_bottom_outer(), self.vz_bottom_inner())),
        ]

        return [w, e, a, b]

    def inset_faces_inner(self, state):
        return [self.inset_side_above(state), self.inset_side_below(state), self.inset_side_west(state), self.inset_side_east(state), self.inset_side_north(state), self.inset_side_south(state)]

    # Inner inset sides

    def inset_side_above(self, state):
        return [
            state.lookup(
                (self.vx_left_inner(), self.vy_top_inner(), self.vz_top_inner())),
            state.lookup(
                (self.vx_right_inner(), self.vy_top_inner(), self.vz_top_inner())),
            state.lookup(
                (self.vx_right_inner(), self.vy_bottom_inner(), self.vz_top_inner())),
            state.lookup(
                (self.vx_left_inner(), self.vy_bottom_inner(), self.vz_top_inner())),
        ]

    def inset_side_below(self, state):
        return [
            state.lookup(
                (self.vx_left_inner(), self.vy_top_inner(), self.vz_bottom_inner())),
            state.lookup(
                (self.vx_right_inner(), self.vy_top_inner(), self.vz_bottom_inner())),
            state.lookup(
                (self.vx_right_inner(), self.vy_bottom_inner(), self.vz_bottom_inner())),
            state.lookup(
                (self.vx_left_inner(), self.vy_bottom_inner(), self.vz_bottom_inner())),
        ]

    def inset_side_west(self, state):
        return [
            state.lookup(
                (self.vx_left_inner(), self.vy_top_inner(), self.vz_top_inner())),
            state.lookup(
                (self.vx_left_inner(), self.vy_bottom_inner(), self.vz_top_inner())),
            state.lookup(
                (self.vx_left_inner(), self.vy_bottom_inner(), self.vz_bottom_inner())),
            state.lookup(
                (self.vx_left_inner(), self.vy_top_inner(), self.vz_bottom_inner())),
        ]

    def inset_side_east(self, state):
        return [
            state.lookup(
                (self.vx_right_inner(), self.vy_top_inner(), self.vz_top_inner())),
            state.lookup(
                (self.vx_right_inner(), self.vy_bottom_inner(), self.vz_top_inner())),
            state.lookup(
                (self.vx_right_inner(), self.vy_bottom_inner(), self.vz_bottom_inner())),
            state.lookup(
                (self.vx_right_inner(), self.vy_top_inner(), self.vz_bottom_inner())),
        ]

    def inset_side_north(self, state):
        return [
            state.lookup(
                (self.vx_left_inner(), self.vy_top_inner(), self.vz_top_inner())),
            state.lookup(
                (self.vx_right_inner(), self.vy_top_inner(), self.vz_top_inner())),
            state.lookup(
                (self.vx_right_inner(), self.vy_top_inner(), self.vz_bottom_inner())),
            state.lookup(
                (self.vx_left_inner(), self.vy_top_inner(), self.vz_bottom_inner())),
        ]

    def inset_side_south(self, state):
        return [
            state.lookup(
                (self.vx_left_inner(), self.vy_bottom_inner(), self.vz_top_inner())),
            state.lookup(
                (self.vx_right_inner(), self.vy_bottom_inner(), self.vz_top_inner())),
            state.lookup(
                (self.vx_right_inner(), self.vy_bottom_inner(), self.vz_bottom_inner())),
            state.lookup(
                (self.vx_left_inner(), self.vy_bottom_inner(), self.vz_bottom_inner())),
        ]

    def draw_inset(self, dir, state):
        if self.show_wall(dir):
            return [self.inset_side(dir, state)]
        else:
            return self.inset_faces(dir, state)

    def inset_side(self, dir, state):
        match dir:
            case 'above': return self.inset_side_above(state)
            case 'below': return self.inset_side_below(state)
            case 'north': return self.inset_side_north(state)
            case 'east': return self.inset_side_east(state)
            case 'south': return self.inset_side_south(state)
            case 'west': return self.inset_side_west(state)

    def inset_faces(self, dir, state):
        match dir:
            case 'above': return self.inset_faces_above(state)
            case 'below': return self.inset_faces_below(state)
            case 'north': return self.inset_faces_north(state)
            case 'east': return self.inset_faces_east(state)
            case 'south': return self.inset_faces_south(state)
            case 'west': return self.inset_faces_west(state)

    def outside_connection_west(self, state, show_outer_faces=False):
        outer = copy.copy(self)
        outer.col -= 1
        faces = []
        # extend outer inset faces
        faces.extend(outer.inset_faces_east(state))
        faces.extend(outer.inset_faces_below(state))
        # append inner faces
        faces.append(outer.inset_side_north(state))
        faces.append(outer.inset_side_south(state))
        faces.append(outer.inset_side_above(state))
        faces.append(outer.inset_side_west(state))
        # else:
        #     # todo: add outside connections for non-inset cells
        #     # if show_outer_faces:
        #     #     faces.append(outer.side_north(state))
        #     #     faces.append(outer.side_south(state))
        #     # faces.append(outer.side_above(state))
        #     # faces.append(outer.side_east(state))
        #     pass
        return faces

    def outside_connection_east(self, state, show_outer_faces=False):
        outer = copy.copy(self)
        outer.col += 1
        faces = []
        # extend outer inset faces
        faces.extend(outer.inset_faces_west(state))
        faces.extend(outer.inset_faces_below(state))
        # append inner faces
        faces.append(outer.inset_side_north(state))
        faces.append(outer.inset_side_south(state))
        faces.append(outer.inset_side_above(state))
        faces.append(outer.inset_side_east(state))
        # else:
        #     # todo: add outside connections for non-inset cells
        #     # if show_outer_faces:
        #     #     faces.append(outer.side_north(state))
        #     #     faces.append(outer.side_south(state))
        #     # faces.append(outer.side_above(state))
        #     # faces.append(outer.side_west(state))
        #     pass
        return faces

    def outside_connection_north(self, state, show_outer_faces=False):
        outer = copy.copy(self)
        outer.row -= 1
        faces = []
        # extend outer inset faces
        faces.extend(outer.inset_faces_south(state))
        faces.extend(outer.inset_faces_below(state))
        # append inner faces
        faces.append(outer.inset_side_north(state))
        faces.append(outer.inset_side_above(state))
        faces.append(outer.inset_side_west(state))
        faces.append(outer.inset_side_east(state))
        # else:
        #     # todo: add outside connections for non-inset cells
        #     # if show_outer_faces:
        #     #     faces.append(outer.side_north(state))
        #     #     faces.append(outer.side_above(state))
        #     # faces.append(outer.side_west(state))
        #     # faces.append(outer.side_east(state))
        #     pass
        return faces

    def outside_connection_south(self, state, show_outer_faces=False):
        outer = copy.copy(self)
        outer.row += 1
        faces = []
        # extend outer inset faces
        faces.extend(outer.inset_faces_north(state))
        faces.extend(outer.inset_faces_below(state))
        # append inner faces
        faces.append(outer.inset_side_south(state))
        faces.append(outer.inset_side_above(state))
        faces.append(outer.inset_side_west(state))
        faces.append(outer.inset_side_east(state))
        # else:
        #     # todo: add outside connections for non-inset cells
        #     # if show_outer_faces:
        #     #     faces.append(outer.side_south(state))
        #     #     faces.append(outer.side_above(state))
        #     # faces.append(outer.side_west(state))
        #     # faces.append(outer.side_east(state))
        #     pass
        return faces

    def outside_connections(self, face, rows, cols, state, show_outer_faces=False):
        faces = []
        match face:
            case 4:
                if self.col == 0 and self.linked_west():
                    faces.extend(self.outside_connection_west(state))
                if self.row == 0 and self.linked_north():
                    faces.extend(self.outside_connection_north(state))
                if self.col == cols - 1 and self.linked_east():
                    faces.extend(self.outside_connection_east(state))
                if self.row == rows - 1 and self.linked_south():
                    faces.extend(self.outside_connection_south(state))
                pass
            case 5:
                pass
            case _:
                if self.col == cols - 1 and self.linked_east():
                    faces.extend(self.outside_connection_east(
                        state, show_outer_faces))
                if self.row == rows - 1 and self.linked_south():
                    faces.extend(self.outside_connection_south(
                        state, show_outer_faces))
        return faces


def vert_pos(row, col, level):
    return (row, -col, level)


class RectGrid3d(RectGrid):
    col_block = RectGrid.col_block
    col_border = RectGrid.col_border
    col_grid = RectGrid.col_grid
    col_text = RectGrid.col_text
    col_above = (255, 192, 0, 255)
    col_below = (255, 98, 0, 255)
    col_above_and_below = (192, 255, 0, 255)

    def __init__(self, rows=10, cols=10, levels=3, weight=1, masked=False, clear=False, inset=0, cells=None):
        assert inset >= 0 and inset <= 0.45
        self.inset = inset
        cap2d = rows * cols
        cap3d = cap2d * levels
        self.cap = cap3d
        self.cap2d = cap2d
        self.cap3d = cap3d
        self.rows = rows
        self.cols = cols
        self.levels = levels
        if cells == None:
            self.cells = []
            for level in range(levels):
                for row in range(rows):
                    for col in range(cols):
                        id = self.calc_id(row, col, level)
                        cell = RectCell3d(
                            rows, cols, levels, cap2d, cap3d, id, row, col, level, weight, masked, clear, inset)
                        self.cells.append(cell)
        else:
            self.cells = cells

    def calc_id(self, row, col, level):
        return level * self.cap2d + row * self.cols + col

    def get(self, row, col, level):
        return self.cells[self.calc_id(row, col, level)]

    def connect_above(self, cell, above):
        a = self.cells[above]
        b = self.cells[cell]
        if a.level - b.level == 1:
            b.above = above
            a.below = cell
        else:
            print(
                f'Could not link above (below={cell} with above={above}): incompatible levels')

    def connect_below(self, cell, below):
        a = self.cells[cell]
        b = self.cells[below]
        if abs(a.level - b.level) == 1:
            a.below = below
            b.above = cell
        else:
            print(
                f'Could not link below (below={below} with above={cell}): incompatible levels')

    def row(self, level, row):
        return filter(lambda cell: cell.level == level, super.row(self, row))

    def col(self, level, col):
        return filter(lambda cell: cell.level == level, super.col(self, col))

    def level(self, level):
        return filter(lambda cell: cell.level == level, self.cells)

    def random_cell(self):
        return random.choice(self.cells)

    def random_cell_on_level(self, level):
        return random.choice(list(filter(lambda cell: cell.level == level, self.cells)))

    def render2d(self, filename, block_size=70, frame_size=10, border_color=col_border, block_color=col_block, grid_bg=col_grid, text_color=col_text, show_labels=True, font=ImageFont.truetype("assets/DejaVuSansMono.ttf", 12)):
        for level in range(self.levels):
            parts = filename.rpartition(".")
            file = f'{parts[0]}_{level}{parts[1]}{parts[2]}'
            cells = list(self.level(level))

            custom_bgs = {}
            custom_text = {}

            for cell in filter(lambda c: c.linked_to(c.below), cells):
                custom_bgs[cell.id] = RectGrid3d.col_below
            for cell in filter(lambda c: c.linked_to(c.above), cells):
                custom_bgs[cell.id] = RectGrid3d.col_above if custom_bgs.get(
                    cell.id) == None else RectGrid3d.col_above_and_below

            RectGrid.render2d(self, file, block_size, frame_size, border_color,
                              block_color, grid_bg, text_color, show_labels, font, cells, custom_bgs, custom_text)

    def vertex_indicies(self):
        verts = []
        vdict = {}
        pos = 0
        for x in range(self.cols+1):
            for y in range(self.rows+1):
                for z in range(self.levels+1):
                    verts.append(vert_pos(x, y, z))
                    vdict[vert_pos(x, y, z)] = pos
                    pos += 1
        return (verts, vdict)

    # def generate_model_inset(self, show_outer_faces=False):
    def generate_model(self, show_outer_faces=False):
        # NOTE: show_outer_faces is ignored if `inset == 0`
        state = VertState()
        faces = []

        if self.inset != 0:
            for cell in self.cells:
                for dir in ['above', 'below', 'north', 'east', 'south', 'west']:
                    f = cell.draw_inset(dir, state)
                    faces.extend(f)
        else:
            for cell in self.cells:
                if cell.show_above_wall() and (cell.level != self.levels - 1 or show_outer_faces == True):
                    faces.append(cell.inset_side_above(state))
                if cell.show_north_wall() and (cell.row != 0 or show_outer_faces == True):
                    faces.append(cell.inset_side_north(state))
                if cell.show_east_wall() and (cell.col != self.cols - 1 or show_outer_faces == True):
                    faces.append(cell.inset_side_east(state))
                if cell.level == 0 and show_outer_faces:
                    faces.append(cell.inset_side_below(state))
                if cell.row == self.rows - 1 and show_outer_faces:
                    faces.append(cell.inset_side_south(state))
                if cell.col == 0 and show_outer_faces:
                    faces.append(cell.inset_side_west(state))

        return (state.verts, faces)

    # Takes a list of vertifices for a maze.  Verticies should be centered around (0,0,0)
    def reorient_cube_face(self, face: int, verts: list):
        offset = 0.5
        x = self.rows / 2 + offset
        y = self.cols / 2 + offset
        z = self.levels / 2 + offset
        match face:
            case 0:
                # rotate_yz_ccw
                # shift x by (1-(rows/2))
                # verts = list(map(lambda p: rotate_yz_ccw(p), verts))
                verts = map_verts(rotate_yz_ccw, verts)
                verts = move_y(verts, -x)
                return verts
            case 1:
                verts = map_verts(rotate_yz_ccw, verts)
                verts = move_y(verts, -x)
                verts = map_verts(rotate_xy_ccw, verts)
                return verts
            case 2:
                verts = map_verts(rotate_yz_ccw, verts)
                verts = move_y(verts, -x)
                verts = map_verts(rotate_xy_ccw, verts)
                verts = map_verts(rotate_xy_ccw, verts)
                return verts
            case 3:
                verts = map_verts(rotate_yz_ccw, verts)
                verts = move_y(verts, -y)
                verts = map_verts(rotate_xy_cw, verts)
                return verts
            case 4:
                verts = move_z(verts, x)
                verts = map_verts(rotate_xy_ccw, verts)
                return verts
            case 5:
                verts = move_z(verts, x)
                verts = map_verts(rotate_xy_ccw, verts)
                verts = map_verts(mirror_x, verts)
                verts = map_verts(mirror_z, verts)
                return verts


class CubeCell(RectCell3d):
    def __init__(self, grid, id, row, col, level, weight=1, clear=False):
        self.id = id
        self.row = row
        self.col = col
        self.level = level
        self.weight = weight
        self.calc_neighbors(grid)
        self.links = [] if not clear else list[filter(
            lambda d: d != None, [self.north, self.east, self.south, self.west])]
        pass

    def calc_neighbors(self, grid):
        n = self.id - grid.cols
        e = self.id + 1
        s = self.id + grid.cols
        w = self.id - 1
        self.north = n if self.row > 0 else None
        self.east = e if not self.col >= grid.cols - 1 else None
        self.south = s if not self.row >= grid.rows - 1 else None
        self.west = w if self.col > 0 else None

        last_row = grid.rows - 1
        last_col = grid.cols - 1
        levels = grid.levels
        rows = grid.rows
        cols = grid.cols
        cap = grid.levels * grid.rows * grid.cols
        last_id = cap - 1

        c = grid.calc_id
        row = self.row
        col = self.col
        level = self.level
        match level:
            case 0:
                if col == 0:
                    self.west = c(3, row, last_col)
                if col == last_col:
                    self.east = c(1, row, 0)
                if row == 0:
                    self.north = c(4, col, 0)
                if row == last_row:
                    self.south = c(5, cols-col-1, 0)
            case 1:
                if col == 0:
                    self.west = c(0, row, last_col)
                if col == last_col:
                    self.east = c(2, row, 0)
                if row == 0:
                    self.north = c(4, last_row, col)
                if row == last_row:
                    self.south = c(5, 0, col)
            case 2:
                if col == 0:
                    self.west = c(1, row, last_col)
                if col == last_col:
                    self.east = c(3, row, 0)
                if row == 0:
                    self.north = c(4, cols - col - 1, last_col)
                if row == last_row:
                    self.south = c(5, col, last_col)
            case 3:
                if col == 0:
                    self.west = c(2, row, last_col)
                if col == last_col:
                    self.east = c(0, row, 0)
                if row == 0:
                    self.north = c(4, 0, cols - 1 - col)
                if row == last_row:
                    self.south = c(5, last_row, cols - col - 1)
            case 4:
                if col == 0:
                    self.west = c(0, 0, row)
                if col == last_col:
                    self.east = c(2, 0, rows - row - 1)
                if row == 0:
                    self.north = c(3, 0, cols - col - 1)
                if row == last_row:
                    self.south = c(1, 0, col)
            case 5:
                if col == 0:
                    self.west = c(0, last_row, rows - row - 1)
                if col == last_col:
                    self.east = c(2, last_row, row)
                if row == 0:
                    self.north = c(1, last_row, col)
                if row == last_row:
                    self.south = c(3, last_row, cols - col - 1)

    def neighbors(self):
        return list(filter(lambda d: not d is None, [
            self.north, self.east, self.south, self.west]))

    def neighbors_3d(self):
        self.neighbors()


class Cube(RectGrid3d):
    col_block = RectGrid.col_block
    col_border = RectGrid.col_border
    col_grid = RectGrid.col_grid
    col_text = RectGrid.col_text
    col_above = (255, 192, 0, 255)
    col_below = (255, 98, 0, 255)
    col_above_and_below = (192, 255, 0, 255)

    def __init__(self, rows=10, cols=10, weight=1, masked=False, clear=False):
        assert rows == cols
        self.levels = 6
        super().__init__(rows, cols, self.levels, weight, masked, clear, inset=0)
        self.cells = []
        for level in range(6):
            for row in range(rows):
                for col in range(cols):
                    id = self.calc_id(level, row, col)
                    self.cells.append(
                        CubeCell(self, id, row, col, level, weight, clear))

    def calc_id(self, level, row, col):
        return self.rows * self.cols * level + row * self.cols + col

    def wrap_neighbors(self):
        pass

    def lookup(self, id):
        return self.cells[id]

    def get(self, level, row, col):
        return self.cells[level*self.rows*self.cols + row * self.cols + col]

    def render2d(self, filename, block_size=70, frame_size=10, border_color=col_border, block_color=col_block, grid_bg=col_grid, text_color=col_text, show_labels=True, font=ImageFont.truetype("assets/DejaVuSansMono.ttf", 12)):
        cap = self.rows * self.cols
        for level in range(self.levels):
            parts = filename.rpartition(".")
            file = f'{parts[0]}_{level}{parts[1]}{parts[2]}'
            cells = self.cells[level*cap:level*cap+cap]

            custom_bgs = {}
            custom_text = {}

            RectGrid.render2d(self, file, block_size, frame_size, border_color,
                              block_color, grid_bg, text_color, show_labels, font, cells, custom_bgs, custom_text)

    def split_cube(self, inset=0.25):
        if inset < 0.05:
            inset = 0.05
        grids = []
        cap = self.rows * self.cols
        for face in range(6):
            cells = self.cells[face*cap:face*cap+cap]
            cells = list(
                map(lambda cell: cell.flatten_cell(inset), cells))
            grid = CubePlane(face=face, rows=self.rows,
                             cols=self.cols, inset=inset, cells=cells)
            grids.append(grid)
        return tuple(grids)


class CubePlane(RectGrid3d):
    def __init__(self, face: int, rows=10, cols=10, weight=1, masked=False, clear=False, inset=0, cells=None):
        super().__init__(rows, cols, 1, weight, masked, clear, inset, cells)
        self.face = face

    # def generate_model_inset(self, show_outer_faces=False):
    def generate_cube_face(self, show_outer_faces=False):
        # NOTE: show_outer_faces is ignored if `inset == 0`
        state = VertState()
        faces = []

        if self.inset != 0:
            for cell in self.cells:
                for dir in ['above', 'below', 'north', 'east', 'south', 'west']:
                    f = cell.draw_inset(dir, state)
                    faces.extend(f)
                faces.extend(cell.outside_connections(
                    self.face, self.rows, self.cols, state))
        else:
            for cell in self.cells:
                if cell.show_above_wall() and (cell.level != self.levels - 1 or show_outer_faces == True):
                    faces.append(cell.inset_side_above(state))
                if cell.show_north_wall() and (cell.row != 0 or show_outer_faces == True):
                    faces.append(cell.inset_side_north(state))
                if cell.show_east_wall() and (cell.col != self.cols - 1 or show_outer_faces == True):
                    faces.append(cell.inset_side_east(state))
                if cell.row == self.rows - 1 and show_outer_faces:
                    faces.append(cell.inset_side_south(state))
                if cell.col == 0 and show_outer_faces:
                    faces.append(cell.inset_side_west(state))
                faces.extend(cell.outside_connections(
                    self.face, self.rows, self.cols, state))
        return (state.verts, faces)


# Rotations
#   https://calcworkshop.com/transformations/rotation-rules/
# rotations are around the center, (0, 0, 0)
def rotate_xy_ccw(p: tuple):
    x, y, z = p
    return (-y, x, z)


def rotate_xy_cw(p: tuple):
    x, y, z = p
    return (y, -x, z)


def rotate_xz_ccw(p: tuple):
    x, y, z = p
    return (-z, y, x)


def rotate_xz_cw(p: tuple):
    x, y, z = p
    return (z, y, -x)


def rotate_yz_ccw(p: tuple):
    x, y, z = p
    return (x, -z, y)


def roate_yz_cw(p: tuple):
    x, y, z = p
    return (x, z, -y)


def mirror_x(p: tuple):
    x, y, z = p
    return (-x, y, z)


def mirror_y(p: tuple):
    x, y, z = p
    return (x, -y, z)


def mirror_z(p: tuple):
    x, y, z = p
    return (x, y, -z)


def point_offset(p: tuple, ox, oy, oz):
    x, y, z = p
    return (x+ox, y+oy, z+oz)


# 180° rotation around xy
def flip_xy(p: tuple):
    x, y, z = p
    return (-y, -x, z)


# 180° rotation around xz
def flip_xz(p: tuple):
    x, y, z = p
    return (-z, y, -x)


# 180° rotation around yz
def flip_yz(p: tuple):
    x, y, z = p
    return (x, -z, -y)

# Expects a grid starting at (0,0,0) and ending at (x, -y, z)
#   In other words: x and z are positive, y is inverted


def center_maze(grid: RectGrid3d, verts: list):
    ox = - (grid.cols / 2)
    oy = (grid.rows / 2)
    oz = - (grid.levels / 2)
    return list(map(lambda v: point_offset(v, ox, oy, oz), verts))


def add_x(v: tuple, offset):
    return (v[0] + offset, v[1], v[2])


def add_y(v: tuple, offset):
    return (v[0], v[1] + offset, v[2])


def add_z(v: tuple, offset):
    return (v[0], v[1], v[2] + offset)


def move_x(verts: list, offset):
    return list(map(lambda v: add_x(v, offset), verts))
    # return list(map(lambda p: (p[0] + offset, p[1]. p[2]), verts))


def move_y(verts: list, offset):
    return list(map(lambda v: add_y(v, offset), verts))
    # return list(map(lambda p: (p[0], p[1] + offset. p[2]), verts))


def move_z(verts: list, offset):
    return list(map(lambda v: add_z(v, offset), verts))
    # return list(map(lambda p: (p[0], p[1]. p[2] + offset), verts))


def map_verts(func: Callable[[tuple], tuple], verts: list):
    return list(map(lambda v: func(v), verts))


def choose_same_level_random_neighbor(grid, cell, available, level=None):
    choices = list(filter(lambda a: grid.lookup(a).level == level, available))
    random.choice(choices)


def growing_tree_3d(grid, find_available_neighbors=None):
    if find_available_neighbors == None:
        find_available_neighbors = maze.list_same_level_available_neighbors
    for i in range(grid.levels):
        start = grid.random_cell_on_level(i)
        maze.growing_tree(
            grid, find_available_neighbors=find_available_neighbors, start=start)
        cell = grid.random_cell_on_level(i)
        if cell.above:
            grid.link(cell.id, cell.above)
