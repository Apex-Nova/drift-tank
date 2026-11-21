# =====================================================================
#  part3_world/maps.py  —  RANDOM BATTLE MAPS (tilted 3/4 pixel art)
# =====================================================================
#
# Every match builds a NEW map from a random seed: organic cliff edges,
# curvy roads with bridges, lakes / chasms, and clusters of rocks, trees,
# ruined walls, barricades, crates and barrels.
#
# FAIR BY DESIGN: the generator builds ONE quarter (24 x 18 tiles) and
# mirrors it left-right and top-bottom into a 48 x 36 map, so every spawn
# corner gets exactly the same cover, loot and paths.
# Host and clients build the same map from the same seed.
#
#   grid characters:
#   .  ground   ,  grass/flowers/snow drift   L  loot spot   S  spawn
#   #  stone wall      B  barricade        C  wood crate    M  metal crate
#   X  explosive barrel   R  rock   T  tree   b  bush (hide inside)
#   ~  lake / chasm (tanks can't cross, bullets can)   V  void (map edge)
#   H  bridge          i  ice (slippery)
# =====================================================================
import math
import random

import pygame
from pygame.math import Vector2

from part1_engine.view import shade, OUTLINE, YS, Camera
from part3_world.wall import Wall
from part4_ui import art

T = 32
QW, QH = 24, 18
COLS, ROWS = QW * 2, QH * 2
WORLD_W, WORLD_H = COLS * T, ROWS * T
VIEW_H = int(WORLD_H * YS)          # the baked floor is squashed to the tilted view
CLIFF_H = 26                        # how far map-edge cliffs drop

MAPS = [
    {"id": "canyon", "name": "Canyon Crossing", "theme": "canyon",
     "blurb": "Red-dirt canyon. Deep chasms, rock spires, ruins and barricades."},
    {"id": "valley", "name": "Green Valley", "theme": "valley",
     "blurb": "Lakes, bridges and thick forests. Bushes hide you."},
    {"id": "frost", "name": "Frostbite", "theme": "frost",
     "blurb": "Ice fields = huge drifts. Snowy pines and metal crates."},
    {"id": "scrap", "name": "Scrapyard", "theme": "scrap",
     "blurb": "Container mazes and stacks of explosive barrels. Chain reactions!"},
]
MAP_IDS = [m["id"] for m in MAPS]

THEMES = {
    "canyon": {"name": "canyon", "ground": (198, 114, 68), "speck": [(182, 102, 60), (214, 134, 86), (172, 94, 56)],
               "pebble": (230, 166, 116), "grass": (128, 150, 62), "grass_dark": (96, 118, 46), "road": (124, 114, 118),
               "road_edge": (96, 88, 92), "dash": (232, 226, 210), "pit": (64, 28, 36), "cliff": (178, 98, 60),
               "wall": ((178, 184, 172), (126, 132, 124)), "rock": (206, 128, 76), "leaf": (102, 152, 62),
               "bush": (116, 160, 62), "bg": (40, 18, 24), "water": False},
    "valley": {"name": "valley", "ground": (108, 162, 74), "speck": [(96, 150, 66), (122, 176, 84), (90, 140, 62)],
               "pebble": (156, 200, 116), "grass": (86, 140, 62), "grass_dark": (66, 114, 48), "road": (158, 124, 86),
               "road_edge": (124, 96, 66), "dash": None, "pit": (52, 112, 176), "cliff": (134, 98, 64),
               "wall": ((170, 176, 168), (118, 124, 118)), "rock": (150, 152, 144), "leaf": (72, 146, 66),
               "bush": (92, 164, 72), "bg": (14, 30, 24), "water": True},
    "frost": {"name": "frost", "ground": (226, 234, 244), "speck": [(212, 222, 236), (238, 244, 252), (200, 212, 230)],
              "pebble": (180, 196, 216), "grass": (246, 250, 255), "grass_dark": (204, 216, 236), "road": (150, 162, 182),
              "road_edge": (124, 136, 158), "dash": (232, 238, 246), "pit": (44, 86, 140), "cliff": (150, 170, 198),
              "wall": ((214, 226, 238), (146, 166, 190)), "rock": (164, 182, 206), "leaf": (64, 120, 100),
              "bush": (104, 150, 136), "bg": (12, 20, 36), "water": True},
    "scrap": {"name": "scrap", "ground": (118, 106, 94), "speck": [(104, 94, 84), (130, 118, 104), (92, 84, 78)],
              "pebble": (152, 142, 128), "grass": (100, 112, 72), "grass_dark": (78, 90, 56), "road": (78, 76, 84),
              "road_edge": (58, 56, 62), "dash": (228, 196, 70), "pit": (34, 28, 32), "cliff": (112, 98, 86),
              "wall": ((152, 152, 158), (102, 102, 110)), "rock": (126, 116, 106), "leaf": (92, 112, 60),
              "bush": (102, 122, 66), "bg": (14, 12, 16), "water": False},
}

# char -> (kind, hit points or None, blocks tanks, blocks bullets, explosive)
OBJECT_KINDS = {
    "#": ("wall", None, True, True, False),
    "B": ("barricade", 80, True, True, False),
    "C": ("crate", 45, True, True, False),
    "M": ("metal", 110, True, True, False),
    "X": ("barrel", 20, True, True, True),
    "R": ("rock", None, True, True, False),
    "T": ("tree", None, True, True, False),
    "b": ("bush", None, False, False, False),
}
WALKABLE = set(".,LSHib")


# =====================================================================
#  generator
# =====================================================================
def _catmull(points, step=0.2):
    """Smooth curve through points (tile coords)."""
    if len(points) < 2:
        return points
    pts = [points[0]] + points + [points[-1]]
    out = []
    for i in range(1, len(pts) - 2):
        p0, p1, p2, p3 = pts[i - 1], pts[i], pts[i + 1], pts[i + 2]
        n = max(2, int(math.dist(p1, p2) / step))
        for k in range(n):
            t = k / n
            t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * ((2 * p1[j]) + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2
                                    + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3) for j in (0, 1)))
    out.append(points[-1])
    return out


def generate(theme_name, seed):
    rng = random.Random(seed)
    q = [["." for _ in range(QW)] for _ in range(QH)]

    def free(c, r):
        return 0 <= c < QW and 0 <= r < QH and q[r][c] in ".,"

    # 1. organic map edge (void) on the outer sides + a rounded corner
    top_depth = [0] * QW
    d = rng.randint(0, 2)
    for c in range(QW):
        if c % 3 == 0:
            d = max(0, min(3, d + rng.choice((-1, 0, 1))))
        top_depth[c] = d
    left_depth = [0] * QH
    d = rng.randint(0, 2)
    for r in range(QH):
        if r % 3 == 0:
            d = max(0, min(3, d + rng.choice((-1, 0, 1))))
        left_depth[r] = d
    corner = rng.randint(4, 6)
    for r in range(QH):
        for c in range(QW):
            if r < top_depth[c] or c < left_depth[r] or c + r < corner:
                q[r][c] = "V"

    # 2. spawn: first free tile near the corner
    spawn = None
    for radius in range(3, 12):
        for r in range(QH):
            for c in range(QW):
                if q[r][c] == "." and abs(c - 5) + abs(r - 4) <= radius and spawn is None:
                    spawn = (c, r)
        if spawn:
            break
    sc, sr = spawn

    def near_spawn(c, r, dist=3):
        return abs(c - sc) <= dist and abs(r - sr) <= dist

    # 3. lakes / chasms (organic blobs)
    for _ in range(rng.randint(1, 2)):
        for _try in range(20):
            cx, cy = rng.uniform(5, 19), rng.uniform(4, 14)
            if math.dist((cx, cy), (sc, sr)) > 6 and math.dist((cx, cy), (QW, QH)) > 4:
                break
        rx, ry = rng.uniform(2.0, 3.8), rng.uniform(1.6, 3.0)
        phase = [rng.uniform(0, math.tau) for _ in range(3)]
        for r in range(QH):
            for c in range(QW):
                a = math.atan2(r - cy, c - cx)
                k = 1 + 0.22 * math.sin(3 * a + phase[0]) + 0.12 * math.sin(5 * a + phase[1])
                if ((c - cx) / (rx * k)) ** 2 + ((r - cy) / (ry * k)) ** 2 <= 1 and q[r][c] == "." and not near_spawn(c, r):
                    q[r][c] = "~"

    # 4. curvy roads: spawn -> right edge, spawn -> bottom edge (they connect with the mirrored quarters)
    road_curves = []
    exit_row = rng.randint(7, 15)
    exit_col = rng.randint(7, 20)
    for end in ((QW, exit_row + 0.5), (exit_col + 0.5, QH)):
        start = (sc + 0.5, sr + 0.5)
        pts = [start]
        for k in (0.25, 0.5, 0.75):
            bx = start[0] + (end[0] - start[0]) * k
            by = start[1] + (end[1] - start[1]) * k
            dx, dy = end[0] - start[0], end[1] - start[1]
            length = math.hypot(dx, dy) or 1
            wiggle = rng.uniform(-3.2, 3.2)
            pts.append((max(1.5, min(QW - 1, bx - dy / length * wiggle)), max(1.5, min(QH - 1, by + dx / length * wiggle))))
        if end[0] == QW:
            pts.append((QW - 1.5, end[1]))       # enter the mirror line straight, so halves join smoothly
        else:
            pts.append((end[0], QH - 1.5))
        pts.append(end)
        curve = _catmull(pts)
        road_curves.append(curve)
        for x, y in curve:
            for dc in (-1, 0, 1):
                for dr in (-1, 0, 1):
                    c, r = int(x + dc * 0.45), int(y + dr * 0.45)
                    if 0 <= c < QW and 0 <= r < QH:
                        if q[r][c] == "~":
                            q[r][c] = "H"            # bridge over the lake
                        elif q[r][c] == "V":
                            q[r][c] = "."
    road_cells = set()
    for curve in road_curves:
        for x, y in curve:
            road_cells.add((int(x), int(y)))

    def placeable(c, r, gap=0):
        if not free(c, r) or near_spawn(c, r, 3) or (c, r) in road_cells:
            return False
        if c >= QW - 1 and r >= QH - 1:
            return False
        return True

    def blob_cells(cx, cy, n):
        cells = [(cx, cy)]
        while len(cells) < n:
            c, r = rng.choice(cells)
            c, r = c + rng.choice((-1, 0, 1)), r + rng.choice((-1, 0, 1))
            if (c, r) not in cells:
                cells.append((c, r))
        return cells

    def place_cluster(char, count, size_range, extra=None):
        for _ in range(count):
            for _try in range(30):
                cx, cy = rng.randrange(1, QW - 1), rng.randrange(1, QH - 1)
                if placeable(cx, cy):
                    break
            for c, r in blob_cells(cx, cy, rng.randint(*size_range)):
                if placeable(c, r):
                    q[r][c] = char
                    if extra and rng.random() < 0.5:
                        ec, er = c + rng.choice((-1, 1)), r + rng.choice((-1, 0, 1))
                        if placeable(ec, er):
                            q[er][ec] = extra

    def place_line(char, count, length_range, gaps=True):
        for _ in range(count):
            for _try in range(30):
                c, r = rng.randrange(2, QW - 2), rng.randrange(2, QH - 2)
                if placeable(c, r):
                    break
            horizontal = rng.random() < 0.5
            length = rng.randint(*length_range)
            bend = rng.randint(2, length) if rng.random() < 0.5 else None
            for i in range(length):
                if bend is not None and i == bend:
                    horizontal = not horizontal
                if not (gaps and rng.random() < 0.12) and placeable(c, r):
                    q[r][c] = char
                if horizontal:
                    c += 1
                else:
                    r += 1

    def scatter(char, count):
        for _ in range(count):
            for _try in range(20):
                c, r = rng.randrange(QW), rng.randrange(QH)
                if placeable(c, r):
                    q[r][c] = char
                    break

    def ground_blobs(char, count, size_range):
        for _ in range(count):
            cx, cy = rng.randrange(QW), rng.randrange(QH)
            for c, r in blob_cells(cx, cy, rng.randint(*size_range)):
                if 0 <= c < QW and 0 <= r < QH and q[r][c] == ".":
                    q[r][c] = char

    if theme_name == "canyon":
        ground_blobs(",", 5, (4, 10))
        place_cluster("R", 4, (1, 4))
        place_line("#", 2, (3, 6))
        place_line("B", 2, (2, 4), gaps=False)
        place_cluster("C", 2, (1, 3))
        scatter("X", 3)
        scatter("T", 3)
        scatter("b", 3)
    elif theme_name == "valley":
        ground_blobs(",", 6, (3, 8))
        place_cluster("T", 4, (2, 5), extra="b")
        place_cluster("b", 3, (2, 4))
        place_line("#", 2, (2, 4))
        place_cluster("C", 2, (1, 2))
        place_cluster("R", 1, (1, 2))
        scatter("X", 2)
    elif theme_name == "frost":
        ground_blobs(",", 4, (4, 9))
        ground_blobs("i", 3, (8, 20))
        place_cluster("T", 3, (2, 4), extra="b")
        place_cluster("R", 2, (1, 3))
        place_cluster("M", 2, (2, 4))
        place_line("#", 2, (3, 5))
        scatter("X", 2)
    else:  # scrap
        ground_blobs(",", 4, (3, 7))
        place_cluster("M", 4, (2, 5))
        place_line("#", 3, (3, 6))
        place_line("B", 2, (2, 4), gaps=False)
        place_cluster("X", 3, (1, 3))
        place_cluster("C", 3, (1, 3))
        scatter("T", 2)

    # 5. loot spots, spread out
    spots = 0
    for _ in range(200):
        c, r = rng.randrange(2, QW), rng.randrange(2, QH)
        if q[r][c] in ".," and not near_spawn(c, r, 3) and all(abs(c - a) + abs(r - b) > 4 for a, b in
                                                              [(x, y) for y in range(QH) for x in range(QW) if q[y][x] == "L"]):
            q[r][c] = "L"
            spots += 1
            if spots >= 5:
                break

    # 6. make sure the spawn can drive to the middle of the map
    def path_exists():
        seen = {spawn}
        todo = [spawn]
        while todo:
            c, r = todo.pop()
            if c >= QW - 2 and r >= QH - 2:
                return True
            for dc, dr in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                n = (c + dc, r + dr)
                if 0 <= n[0] < QW and 0 <= n[1] < QH and n not in seen and q[n[1]][n[0]] in WALKABLE:
                    seen.add(n)
                    todo.append(n)
        return False
    if not path_exists():
        c, r = sc, sr
        while (c, r) != (QW - 1, QH - 1):
            if q[r][c] not in WALKABLE:
                q[r][c] = "H" if q[r][c] == "~" else "."
            if c < QW - 1 and (r >= QH - 1 or rng.random() < 0.55):
                c += 1
            else:
                r += 1
    q[sr][sc] = "S"
    # the 4x4 middle of the map stays open
    for r in range(QH - 2, QH):
        for c in range(QW - 2, QW):
            if q[r][c] not in "~H":
                q[r][c] = "."

    # mirror into the full map
    grid = []
    for r in range(ROWS):
        qr = r if r < QH else ROWS - 1 - r
        grid.append("".join(q[qr][c if c < QW else COLS - 1 - c] for c in range(COLS)))
    curves = []
    for curve in road_curves:
        for fx in (False, True):
            for fy in (False, True):
                curves.append([((COLS - x if fx else x) * T, (ROWS - y if fy else y) * T) for x, y in curve])
    return grid, curves


# =====================================================================
#  map objects
# =====================================================================
class MapObject(Wall):
    """A wall / crate / barrel / rock / tree. Extends Person 3's Wall (rect, destructible, hit, alive)."""

    def __init__(self, index, char, col, row, seed):
        kind, hp, blocks_tanks, blocks_bullets, explosive = OBJECT_KINDS[char]
        super().__init__(pygame.Rect(col * T, row * T, T, T), destructible=hp is not None)
        self.index = index
        self.kind = kind
        self.col, self.row = col, row
        self.max_health = hp
        self.health = hp
        self.blocks_tanks = blocks_tanks
        self.blocks_bullets = blocks_bullets
        self.explosive = explosive
        self.seed = seed
        self.joins = (False, False, False, False)
        if kind == "barrel":
            self.rect = pygame.Rect(0, 0, 18, 18)
            self.rect.center = (col * T + T // 2, row * T + T // 2)
        elif kind == "tree":
            self.rect = pygame.Rect(col * T + 8, row * T + 8, 16, 16)
        elif kind == "rock":
            self.rect = pygame.Rect(col * T + 3, row * T + 3, 26, 26)
        elif kind in ("crate", "metal"):
            self.rect = pygame.Rect(col * T + 3, row * T + 3, 26, 26)
        elif kind == "barricade":
            self.rect = pygame.Rect(col * T, row * T + 8, T, 18)

    @property
    def depth(self):
        return self.row * T + T


class _Solid:
    """Blocks tanks but isn't a map object (lakes, chasms, the map edge)."""
    alive = True
    blocks_tanks = True
    blocks_bullets = False

    def __init__(self, rect):
        self.rect = rect


class GameMap:
    def __init__(self, map_id, seed=None):
        data = next((m for m in MAPS if m["id"] == map_id), MAPS[0])
        self.data = data
        self.id = data["id"]
        self.name = data["name"]
        self.theme_name = data["theme"]
        self.theme = THEMES[data["theme"]]
        self.seed = seed if seed is not None else random.randrange(1, 10 ** 9)
        self.grid, self.road_curves = generate(self.theme_name, self.seed)
        self.bounds = pygame.Rect(0, 0, WORLD_W, WORLD_H)
        self.objects = []
        self.spawns = {}
        self.loot_spots = []
        self.pit_rects = []
        self.ice = set()
        self.by_cell = {}
        rng = random.Random(self.seed + 1)
        for row, line in enumerate(self.grid):
            for col, ch in enumerate(line):
                center = Vector2(col * T + T / 2, row * T + T / 2)
                if ch in OBJECT_KINDS:
                    obj = MapObject(len(self.objects), ch, col, row, rng.randrange(1000))
                    self.objects.append(obj)
                    self.by_cell[(col, row)] = obj
                elif ch == "S":
                    quarter = (1 if col < QW else 2) + (0 if row < QH else 2)
                    self.spawns[quarter] = center
                elif ch == "L":
                    self.loot_spots.append(center)
                elif ch in "~V":
                    self.pit_rects.append(pygame.Rect(col * T, row * T, T, T))
                elif ch == "i":
                    self.ice.add((col, row))
        self.update_joins()
        self._blockers_dirty = True
        self._blockers = []
        self.ground = None

    # ---------------- rules ----------------
    def cell(self, col, row):
        if 0 <= row < ROWS and 0 <= col < COLS:
            return self.grid[row][col]
        return "V"

    def update_joins(self):
        for obj in self.objects:
            if obj.kind not in ("wall", "barricade"):
                continue

            def same(dc, dr):
                other = self.by_cell.get((obj.col + dc, obj.row + dr))
                return other is not None and other.alive and other.kind == obj.kind
            obj.joins = (same(0, -1), same(1, 0), same(0, 1), same(-1, 0))

    def tank_blockers(self):
        if self._blockers_dirty:
            self._blockers = [o for o in self.objects if o.alive and o.blocks_tanks] + [_Solid(r) for r in self.pit_rects]
            self._blockers_dirty = False
        return self._blockers

    def bullet_blockers(self):
        return [o for o in self.objects if o.alive and o.blocks_bullets]

    def object_destroyed(self):
        self._blockers_dirty = True
        self.update_joins()

    def is_ice(self, x, y):
        return (int(x // T), int(y // T)) in self.ice

    def is_free(self, rect):
        if not self.bounds.contains(rect):
            return False
        return not any(rect.colliderect(b.rect) for b in self.tank_blockers())

    def random_free_point(self, rng=random, near=None, radius=None):
        for _ in range(300):
            if near is not None and radius:
                p = Vector2(near) + Vector2(rng.uniform(0, radius), 0).rotate(rng.uniform(0, 360))
                col, row = int(p.x // T), int(p.y // T)
            else:
                col, row = rng.randrange(COLS), rng.randrange(ROWS)
            p = Vector2(col * T + T / 2, row * T + T / 2)
            r = pygame.Rect(0, 0, 26, 26)
            r.center = p
            if self.is_free(r):
                return p
        return Vector2(WORLD_W / 2, WORLD_H / 2)

    def spawn_point(self, player_id):
        return Vector2(self.spawns.get(player_id, self.spawns.get(1, Vector2(160, 160))))

    # ---------------- drawing ----------------
    def bake(self):
        """Draw the floor once: flat textures in world space, then tilt (squash) it,
        then draw the vertical things (cliffs, banks, decorations) in the tilted view."""
        th = self.theme
        rng = random.Random(self.seed + 7)
        flat = pygame.Surface((WORLD_W, WORLD_H)).convert()
        flat.fill(th["ground"])
        for _ in range(WORLD_W * WORLD_H // 50):
            flat.fill(rng.choice(th["speck"]), (rng.randrange(WORLD_W), rng.randrange(WORLD_H), rng.choice((1, 1, 2)), 1))
        for _ in range(70):
            x, y = rng.randrange(WORLD_W), rng.randrange(WORLD_H)
            pygame.draw.ellipse(flat, shade(th["ground"], rng.choice((0.94, 1.05))), (x, y, rng.randint(30, 110), rng.randint(20, 60)))
        self._grass(flat, rng)
        self._ice(flat, rng)
        self._roads(flat)
        for c in range(COLS):                    # water / pit surfaces
            for r in range(ROWS):
                ch = self.grid[r][c]
                if ch in "~":
                    flat.fill(th["pit"], (c * T, r * T, T, T))
                elif ch == "V":
                    flat.fill(th["bg"], (c * T, r * T, T, T))
        self._round_edges(flat, rng)
        # tilt
        g = pygame.transform.scale(flat, (WORLD_W, VIEW_H))
        self._shadows(g)
        self._decor(g, rng)
        self._bridges(g)
        self._cliffs(g, rng)
        self.ground = g
        return g

    def _round_edges(self, flat, rng):
        """Soften the tile steps: bite round chunks out of land next to the void / lakes."""
        th = self.theme
        for r in range(ROWS):
            for c in range(COLS):
                ch = self.grid[r][c]
                if ch not in "~V":
                    continue
                color = th["bg"] if ch == "V" else th["pit"]
                for dc, dr in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    if self.cell(c + dc, r + dr) not in "~VH" and r + dr >= 0:
                        for _ in range(2):
                            x = c * T + T // 2 + dc * rng.randint(10, 16) + (rng.randint(-12, 12) if dc == 0 else 0)
                            y = r * T + T // 2 + dr * rng.randint(10, 16) + (rng.randint(-12, 12) if dr == 0 else 0)
                            pygame.draw.circle(flat, color, (x, y), rng.randint(6, 10))

    def _grass(self, g, rng):
        th = self.theme
        layer = pygame.Surface((WORLD_W, WORLD_H), pygame.SRCALPHA)
        cells = [(c, r) for r in range(ROWS) for c in range(COLS) if self.grid[r][c] == ","]
        for c, r in cells:
            for _ in range(4):
                pygame.draw.circle(layer, th["grass"] + (255,), (c * T + rng.randint(-4, T + 4), r * T + rng.randint(-4, T + 4)),
                                   rng.randint(9, 15))
        mask = pygame.mask.from_surface(layer)
        rim = mask.to_surface(setcolor=th["grass_dark"] + (255,), unsetcolor=(0, 0, 0, 0))
        g.blit(rim, (0, 3))
        g.blit(layer, (0, 0))
        for _ in range(len(cells) * 16):
            if not cells:
                break
            c, r = rng.choice(cells)
            x, y = c * T + rng.randrange(T), r * T + rng.randrange(T)
            if mask.get_at((min(WORLD_W - 1, x), min(WORLD_H - 1, y))):
                g.fill(rng.choice((th["grass_dark"], shade(th["grass"], 1.2))), (x, y, 1, 3))

    def _ice(self, g, rng):
        for c, r in self.ice:
            x, y = c * T, r * T
            g.fill((186, 224, 242), (x, y, T, T))
            for _ in range(2):
                sx, sy = x + rng.randrange(T), y + rng.randrange(T)
                pygame.draw.line(g, (236, 248, 255), (sx, sy), (sx + rng.randint(4, 12), sy - rng.randint(2, 5)))
        for c, r in self.ice:
            for dc, dr, col in ((0, -1, (214, 238, 250)), (0, 1, (150, 196, 222)), (-1, 0, (214, 238, 250)), (1, 0, (150, 196, 222))):
                if (c + dc, r + dr) not in self.ice:
                    x, y = c * T, r * T
                    rect = {(0, -1): (x, y, T, 3), (0, 1): (x, y + T - 3, T, 3), (-1, 0): (x, y, 3, T), (1, 0): (x + T - 3, y, 3, T)}[(dc, dr)]
                    g.fill(col, rect)

    def _roads(self, g):
        th = self.theme
        for curve in self.road_curves:          # dark edge, then asphalt
            for x, y in curve:
                pygame.draw.circle(g, th["road_edge"], (x, y), 16)
        for curve in self.road_curves:
            for x, y in curve:
                pygame.draw.circle(g, th["road"], (x, y), 13)
        rng = random.Random(self.seed + 3)
        for curve in self.road_curves:
            for x, y in curve[::3]:
                g.fill(shade(th["road"], rng.choice((0.9, 1.1))), (x + rng.randint(-10, 10), y + rng.randint(-10, 10), 2, 1))
        if th["dash"]:
            for curve in self.road_curves:
                dist = 0.0
                for (x0, y0), (x1, y1) in zip(curve, curve[1:]):
                    seg = math.dist((x0, y0), (x1, y1))
                    if (dist // 10) % 2 == 0:
                        pygame.draw.line(g, th["dash"], (x0, y0), (x1, y1), 2)
                    dist += seg

    def _shadows(self, g):
        """Soft shadows at the base of walls, rocks and trees (they never move)."""
        sh = pygame.Surface((44, 16), pygame.SRCALPHA)
        pygame.draw.ellipse(sh, (20, 10, 20, 70), sh.get_rect())
        for obj in self.objects:
            if obj.kind in ("rock", "tree"):
                g.blit(sh, (obj.col * T - 2 + 4, obj.row * T * YS + 14))

    def _decor(self, g, rng):
        """Little details in the tilted view: stones, cracks, flowers, bones, oil, bolts."""
        th = self.theme
        name = th["name"]
        for _ in range(900):
            c, r = rng.randrange(COLS), rng.randrange(ROWS)
            if self.grid[r][c] not in ".,L":
                continue
            x, y = c * T + rng.randrange(T), int((r * T + rng.randrange(T)) * YS)
            roll = rng.random()
            if roll < 0.45:                           # small stone with highlight + shadow
                w = rng.choice((2, 3, 4))
                g.fill(shade(th["pebble"], 0.6), (x, y + 1, w, 2))
                g.fill(th["pebble"], (x, y, w, 2))
                g.fill(shade(th["pebble"], 1.2), (x, y, 1, 1))
            elif roll < 0.6:                          # crack
                for _ in range(rng.randint(3, 6)):
                    g.fill(shade(th["ground"], 0.78), (x, y, 1, 1))
                    x += rng.choice((-1, 1))
                    y += rng.choice((0, 1))
            elif roll < 0.8:
                if name == "valley":                  # flowers
                    g.fill(rng.choice(((250, 230, 90), (240, 120, 160), (255, 255, 255), (150, 180, 255))), (x, y, 2, 2))
                elif name == "frost":                 # snow lump
                    g.fill((250, 252, 255), (x, y, 4, 2))
                    g.fill((196, 210, 230), (x, y + 2, 4, 1))
                elif name == "canyon":                # dry twig
                    pygame.draw.line(g, (120, 82, 50), (x, y), (x + rng.randint(3, 6), y + rng.randint(-2, 2)))
                else:                                  # bolts / scrap bits
                    g.fill((150, 150, 158), (x, y, 2, 2))
                    g.fill((90, 90, 96), (x + 1, y + 1, 1, 1))
            elif name == "scrap" and roll < 0.86:      # oil stain
                pygame.draw.ellipse(g, (52, 46, 46), (x, y, rng.randint(8, 18), rng.randint(4, 8)))
            elif name == "canyon" and roll < 0.83:     # bones
                g.fill((236, 226, 200), (x, y, 5, 1))
                g.fill((236, 226, 200), (x, y - 1, 1, 3))
                g.fill((236, 226, 200), (x + 4, y - 1, 1, 3))

    def _bridges(self, g):
        for r in range(ROWS):
            for c in range(COLS):
                if self.grid[r][c] != "H":
                    continue
                x, y = c * T, int(r * T * YS)
                h = int(T * YS)
                vertical = self.cell(c, r - 1) in "H.,L" and self.cell(c, r + 1) in "H.,L" and \
                    not (self.cell(c - 1, r) in "H.,L" and self.cell(c + 1, r) in "H.,L")
                wood = (150, 102, 62)
                g.fill(shade(wood, 0.7), (x, y, T, h + 4))
                if vertical:
                    for k in range(0, h, 4):
                        g.fill(wood, (x + 2, y + k, T - 4, 3))
                        g.fill(shade(wood, 1.2), (x + 2, y + k, T - 4, 1))
                    g.fill((96, 66, 40), (x, y, 2, h))
                    g.fill((96, 66, 40), (x + T - 2, y, 2, h))
                else:
                    for k in range(0, T, 5):
                        g.fill(wood, (x + k, y + 2, 4, h - 4))
                        g.fill(shade(wood, 1.2), (x + k, y + 2, 1, h - 4))
                    g.fill((96, 66, 40), (x, y, T, 2))
                    g.fill((96, 66, 40), (x, y + h - 2, T, 2))

    def _cliffs(self, g, rng):
        """Vertical faces where the ground ends: map edge cliffs, chasm walls, lake banks."""
        th = self.theme
        h = int(T * YS)
        for r in range(ROWS + 1):
            for c in range(COLS):
                ch = self.cell(c, r)
                above = self.cell(c, r - 1)
                if ch in "~V" and above not in "~V":
                    x, y = c * T, int(r * T * YS)
                    water = ch == "~" and th["water"]
                    face = 8 if water else (CLIFF_H if ch == "V" else 18)
                    cliff = th["cliff"]
                    g.fill(cliff, (x, y, T, face))
                    for k in range(0, face, 4):
                        g.fill(shade(cliff, 0.8 if (k // 4) % 2 else 1.08), (x, y + k, T, 2))
                    for _ in range(4):
                        g.fill(shade(cliff, 0.66), (x + rng.randrange(T), y + rng.randrange(face), 2, rng.randint(2, 5)))
                    for k in range(0, T, 3):          # ragged lip
                        g.fill(shade(th["ground"], 0.86), (x + k, y - 1, 3, rng.randint(1, 3)))
                    jag = [(x + k, y + face + rng.randint(-2, 1)) for k in range(0, T + 1, 4)]
                    pygame.draw.lines(g, OUTLINE, False, jag, 1)
                    if water:
                        g.fill((206, 234, 250), (x, y + face + 1, T, 2))
        for r in range(ROWS):
            for c in range(COLS):
                ch = self.cell(c, r)
                if ch not in "~V":
                    continue
                x, y = c * T, int(r * T * YS)
                if self.cell(c - 1, r) not in "~V":
                    g.fill(OUTLINE, (x, y, 1, h))
                    g.fill(shade(th["ground"], 0.7), (x - 1, y, 1, h))
                if self.cell(c + 1, r) not in "~V":
                    g.fill(OUTLINE, (x + T - 1, y, 1, h))
                if self.cell(c, r + 1) not in "~V":
                    g.fill(shade(th["ground"], 1.08), (x, y + h - 1, T, 1))
                    g.fill(OUTLINE, (x, y + h - 2, T, 1))
        # bottom of the whole map: a tall cliff face so the map looks like a raised plateau
        y = VIEW_H
        bottom = pygame.Surface((WORLD_W, CLIFF_H), pygame.SRCALPHA)
        for c in range(COLS):
            if self.cell(c, ROWS - 1) in "~V":
                continue
            bottom.fill(th["cliff"], (c * T, 0, T, CLIFF_H))
            for k in range(0, CLIFF_H, 4):
                bottom.fill(shade(th["cliff"], 0.8 if (k // 4) % 2 else 1.08), (c * T, k, T, 2))
        self.bottom_cliff = bottom

    def draw_water_shimmer(self, surf, cam, t):
        if not self.theme.get("water"):
            return
        view = cam.view_rect()
        for r in self.pit_rects:
            if not view.colliderect(r) or self.cell(r.x // T, r.y // T) == "V":
                continue
            phase = (r.x * 0.05 + r.y * 0.07 + t * 2.4) % 6.28
            if phase < 1.4:
                x, y = cam.to_view(r.x + 8 + (phase * 6) % 14, r.y + 18)
                surf.fill((170, 214, 246), (x, y, 7, 1))

    def object_sprite(self, obj):
        th = self.theme
        damaged = obj.destructible and obj.health is not None and obj.health < obj.max_health * 0.5
        if obj.kind == "wall":
            n, e, s, w = obj.joins
            return art.wall_sprite(th, n, e, s, w, obj.seed)
        if obj.kind == "barricade":
            n, e, s, w = obj.joins
            vertical = (n or s) and not (e or w)
            return art.barricade_sprite(th, vertical, n if vertical else w, s if vertical else e, damaged)
        if obj.kind in ("crate", "metal"):
            return art.crate_sprite(obj.kind, damaged, obj.seed)
        if obj.kind == "barrel":
            return art.barrel_sprite(damaged)
        if obj.kind == "rock":
            return art.rock_sprite(th, obj.seed % 12)
        if obj.kind == "tree":
            return art.tree_sprite(th, obj.seed % 9)
        return art.bush_sprite(th, obj.seed % 8)

    def draw_object(self, surf, obj, cam, faded=False):
        if obj.kind == "bush" and faded:
            img, (dx, dy) = art.bush_sprite(self.theme, obj.seed % 8, faded=True)
        else:
            img, (dx, dy) = self.object_sprite(obj)
        x, y = cam.to_view(obj.col * T, obj.row * T)
        if faded and obj.kind != "bush":
            img = img.copy()
            img.set_alpha(120)
        surf.blit(img, (x + dx, y + dy))

    def preview(self, size):
        """The whole map, small, for the map-select screen."""
        if self.ground is None:
            self.bake()
        full = pygame.Surface((WORLD_W, VIEW_H + CLIFF_H + 30))
        full.fill(self.theme["bg"])
        full.blit(self.ground, (0, 30))
        full.blit(self.bottom_cliff, (0, 30 + VIEW_H))

        class _Flat:
            def to_view(self, x, y, z=0):
                return (int(x), int(y * YS - z) + 30)
        flat = _Flat()
        for obj in sorted(self.objects, key=lambda o: o.depth):
            self.draw_object(full, obj, flat)
        return pygame.transform.smoothscale(full, size)
