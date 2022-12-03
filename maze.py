import random
import sys
from PIL import Image, ImageDraw, ImageFont

# deterministic = True
# if deterministic:
#     random.seed(1778)


class RectCell:
    def __init__(self, rows, cols, cap, id, row, col, weight=1, masked=False, clear=False):
        self.id = id
        self.row = row
        self.col = col
        self.links = []
        self.masked = masked
        self.weight = weight
        self.level = None
        # self.north = None
        # self.east = None
        # self.south = None
        # self.west = None
        self.calc_neighbors(rows, cols)
        if clear:
            self.links.extend(self.neighbors())

    def string(self):
        return f'id={self.id} row={self.row} col={self.col} links={self.links} masked={self.masked} weight={self.weight}\n\tn={self.n} e={self.e} s={self.s} w={self.w}'

    def calc_neighbors(self, rows, cols):
        n = self.id - cols
        e = self.id + 1
        s = self.id + cols
        w = self.id - 1
        self.north = n if self.row != 0 else None
        self.east = e if not self.col >= cols-1 else None
        self.south = s if not self.row >= rows-1 else None
        self.west = w if self.col != 0 else None
        # n = self.id - rows
        # e = self.id + 1
        # s = self.id + rows
        # w = self.id - 1
        # self.north = n if self.row != 0 else None
        # self.east = e if not self.col >= cols-1 else None
        # self.south = s if not self.row >= rows-1 else None
        # self.west = w if self.col != 0 else None

    def neighbors(self):
        return list(filter(lambda d: not d is None, [
            self.north, self.east, self.south, self.west]))

    def linked_to(self, n):
        return n in self.links

    def has_links(self):
        return len(self.links) != 0

    def linked_west(self):
        return self.linked_to(self.west)

    def linked_east(self):
        return self.linked_to(self.east)

    def linked_north(self):
        return self.linked_to(self.north)

    def linked_south(self):
        return self.linked_to(self.south)

    def show_north_wall(self):
        return self.north == None or not self.linked_to(self.north)

    def show_east_wall(self):
        return self.east == None or not self.linked_to(self.east)

    def show_south_wall(self):
        return self.south == None or not self.linked_to(self.south)

    def show_west_wall(self):
        return self.west == None or not self.linked_to(self.west)

    def border_west(self):
        return self.west == None

    def border_east(self):
        return self.east == None

    def border_north(self):
        return self.north == None

    def border_south(self):
        return self.south == None

    def random_neighbor(self):
        return random.choice(self.neighbors())

    def random_link(self):
        return random.choice(self.links)


class RectGrid:
    col_block = (255, 255, 255, 255)
    col_border = (0, 0, 0, 255)
    col_grid = (255, 255, 255, 127)
    col_text = (55, 55, 55, 255)

    def __init__(self, rows=10, cols=10, clear=False):
        cap = rows * cols
        self.cap = cap
        self.rows = rows
        self.cols = cols
        self.cells = list(
            map(lambda i: RectCell(rows, cols, cap, i, i // cols, i % cols, clear=clear), range(cap)))

    def row(self, row: int):
        return filter(lambda cell: cell.row == row, self.cell_rows)

    def col(self, col: int):
        return filter(lambda cell: cell.row == col, self.cell_cols)

    def get(self, row: int, col: int):
        return self.cells[row*self.cols + col]

    def lookup(self, id: int):
        return self.cells[id]

    def random_cell(self):
        return random.choice(self.cells)

    def link(self, a, b):
        if a == None or b == None:
            return
        if not b in self.cells[a].links:
            self.cells[a].links.append(b)
        if not a in self.cells[b].links:
            self.cells[b].links.append(a)

    def unlink(self, a, b):
        if a == None or b == None:
            return
        if b in self.cells[a].links:
            self.cells[a].links.remove(b)
        if a in self.cells[b].links:
            self.cells[b].links.remove(a)

    def link_all(self, id: int):
        cell = self.cells[id]
        for neighbor in cell.neighbors():
            self.link(cell.id, neighbor)

    def unlink_all(self, id: int):
        cell = self.cells[id]
        for neighbor in cell.neighbors():
            self.unlink(cell.id, neighbor)

    def block(self, cell, frame_size, block_size):
        top = frame_size + cell.row * block_size
        bottom = top + block_size
        left = frame_size + cell.col * block_size
        right = left + block_size
        return Block(left, right, top, bottom)

    def render2d(self, filename, block_size=70, frame_size=10, border_color=col_border, block_color=col_block, grid_bg=col_grid, text_color=col_text, show_labels=True, font=ImageFont.truetype("assets/DejaVuSansMono.ttf", 12), cells=None, custom_bgs={}, custom_text={}):
        if cells == None:
            cells = self.cells
        width = self.cols * block_size + frame_size * 2
        height = self.rows * block_size + frame_size * 2
        img = Image.new('RGBA', (width+1, height+1), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.rectangle([(0 + frame_size, 0 + frame_size),
                       (width-frame_size, height-frame_size)], fill=grid_bg)
        for cell in cells:
            block = self.block(cell, frame_size, block_size)
            block_bg = custom_bgs.get(cell.id, block_color)
            block.draw_bg(draw, block_bg)
            if not cell.linked_west():
                block.draw_west(draw, border_color)
            if not cell.linked_east():
                block.draw_east(draw, border_color)
            if not cell.linked_north():
                block.draw_north(draw, border_color)
            if not cell.linked_south():
                block.draw_south(draw, border_color)
            if show_labels:
                block_text = custom_text.get(cell.id, str(cell.id))
                block.draw_text(draw, block_text, text_color, font)

        img.save(filename, "PNG")


class Cylinder(RectGrid):
    def __init__(self, rows=10, cols=10, clear=False):
        super().__init__(rows, cols, clear)
        for cell in filter(lambda cell: cell.col == self.cols - 1, self.cells):
            cell.east = cell.id + 1 - self.cols
            print(f'id={cell.id}: east = {cell.east}')
        for cell in filter(lambda cell: cell.col == 0, self.cells):
            cell.west = cell.id + self.cols - 1
            print(f'id={cell.id}: west = {cell.west}')

    def get(self, row, col):
        return self.cells[row*self.cols + (col % self.cols)]


# Note: Mobius grids should have many more rows than columns.
#         Rows and columns are switched here when compared with other grids
class Mobius(RectGrid):
    col_block = RectGrid.col_block
    col_border = RectGrid.col_border
    col_grid = RectGrid.col_grid
    col_text = RectGrid.col_text
    col_above = (255, 192, 0, 255)
    col_below = (255, 98, 0, 255)
    col_above_and_below = (192, 255, 0, 255)

    def __init__(self, rows=54, cols=6, clear=False):
        assert rows % 2 == 0
        cap = rows*cols
        super().__init__(rows, cols, clear)
        last_row = rows - 1
        for first_col in range(cols):
            last_col = cols-1-first_col
            begin = self.get(row=0, col=first_col)
            end = self.get(row=last_row, col=last_col)
            begin.north = end.id
            end.south = begin.id
            if clear:
                begin.links = begin.neighbors()
                end.links = end.neighbors()
            # connect first column's west neighbor to last column's east, but in reverse order column-wise


class Block:
    def __init__(self, left, right, top, bottom):
        self.left = left
        self.right = right
        self.top = top
        self.bottom = bottom
        self.cx = (left + right) / 2
        self.cy = (top + bottom) / 2

    def draw_west(self, draw, border_color, width=1):
        draw.line([(self.left, self.top), (self.left, self.bottom)],
                  fill=border_color, width=width)

    def draw_east(self, draw, border_color, width=1):
        draw.line([(self.right, self.top), (self.right, self.bottom)],
                  fill=border_color, width=1)

    def draw_north(self, draw, border_color, width=1):
        draw.line([(self.left, self.top), (self.right, self.top)],
                  fill=border_color, width=1)

    def draw_south(self, draw, border_color, width=1):
        draw.line([(self.left, self.bottom), (self.right, self.bottom)],
                  fill=border_color, width=1)

    def draw_bg(self, draw, block_color):
        draw.rectangle([(self.left+1, self.top+1), (self.right-1, self.bottom-1)],
                       fill=block_color)

    def draw_text(self, draw, text, color, font):
        draw.text((self.cx, self.cy), text, fill=color, font=font, anchor='mm')


def growing_tree(grid, choose_active=None, find_available_neighbors=None, choose_neighbor=None, start=None):
    if choose_active == None:
        choose_active = choose_active_random_cell
    if start == None:
        start = grid.random_cell()
    if choose_neighbor == None:
        choose_neighbor = choose_random_neighbor
    if find_available_neighbors == None:
        find_available_neighbors = list_all_available_neighbors
    cell = start
    active = []
    active.append(cell.id)
    iteration = 0
    while len(active) > 0:
        chosen = choose_active(grid, active, cell.level)
        cell = grid.lookup(chosen)
        available = find_available_neighbors(grid, cell, cell.level)
        if len(available) > 0:
            neighbor = choose_neighbor(grid, cell, available, cell.level)
            grid.link(cell.id, neighbor)
            active.append(neighbor)
        else:
            active.remove(cell.id)
        iteration += 1


def choose_active_random_cell(grid, active, level=None):
    return random.choice(active)


def choose_active_random_cell_same_level(grid, active, level=None):
    if level:
        return random.choice(list(filter(lambda n: grid.lookup(n).level == level, active)))
    else:
        return choose_active_random_cell(grid, active, level)


def list_all_available_neighbors(grid, cell, level=None):
    return list(filter(lambda n: not grid.lookup(n).has_links(), cell.neighbors()))


def list_same_level_available_neighbors(grid, cell, level=None):
    return list(filter(lambda n: grid.lookup(n).level == level and not grid.lookup(n).has_links(), cell.neighbors()))


def choose_random_neighbor(grid, cell, available, level=None):
    return random.choice(available)
