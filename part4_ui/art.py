# =====================================================================
#  part4_ui/art.py  —  HAND-BUILT PIXEL ART (all drawn in code)
# =====================================================================
# Every sprite is drawn pixel by pixel at small size, with light coming
# from the TOP-LEFT (bright top/left edges, dark bottom/right edges),
# a dark 1-px outline and texture detail (bricks, planks, rivets...).
# The game scales the whole picture up 2x, so it looks like pixel art.
#
# Object sprites return (surface, (dx, dy)): blit the surface at
# (object footprint top-left) + (dx, dy). Height = how tall it stands.
# =====================================================================
import math
import random

import pygame

from part1_engine.view import StackModel, build_slices, outlined, shade, mix, OUTLINE

T = 32          # tile size in world pixels (one tile looks 32 wide x 24 tall on screen)
_cache = {}


def _rng(*key):
    return random.Random(hash(key) & 0xFFFFFFFF)


def _speckle(surf, rect, colors, count, rng, size=1):
    for _ in range(count):
        x = rng.randrange(rect.left, rect.right)
        y = rng.randrange(rect.top, rect.bottom)
        surf.fill(rng.choice(colors), (x, y, size, size))


# =====================================================================
#  TANKS
# =====================================================================
TEAM_COLORS = {1: (212, 64, 58), 2: (80, 92, 206), 3: (88, 160, 72), 4: (226, 172, 46)}
TDM_COLORS = {1: (212, 64, 58), 3: (226, 112, 52), 2: (80, 92, 206), 4: (52, 156, 196)}


def tank_color(player_id, team_mode=False):
    return (TDM_COLORS if team_mode else TEAM_COLORS).get(player_id, (180, 180, 180))


def hull_model(color):
    key = ("hull", color)
    if key not in _cache:
        track = (58, 56, 66)
        dark = shade(color, 0.62)
        parts = [
            {"shape": "box", "x0": -14, "x1": 14, "y0": -12, "y1": -7, "z0": 0, "z1": 6, "color": track, "stripes": 3},
            {"shape": "box", "x0": -14, "x1": 14, "y0": 7, "y1": 12, "z0": 0, "z1": 6, "color": track, "stripes": 3},
            {"shape": "box", "x0": -12, "x1": 13, "y0": -9, "y1": 9, "z0": 2, "z1": 9, "color": color, "taper": 1, "taper_from": 6,
             "details": [(-11, -8, 2, 16, shade(color, 1.2)), (6, -8, 1, 16, dark)]},
            {"shape": "box", "x0": -13, "x1": -10, "y0": -6, "y1": 6, "z0": 3, "z1": 8, "color": (70, 66, 76),
             "details": [(-13, -5, 3, 1, (40, 38, 46)), (-13, -2, 3, 1, (40, 38, 46)), (-13, 1, 3, 1, (40, 38, 46)), (-13, 4, 3, 1, (40, 38, 46))]},
            {"shape": "box", "x0": 10, "x1": 13, "y0": -8, "y1": -5, "z0": 6, "z1": 8, "color": (250, 232, 150)},
            {"shape": "box", "x0": 10, "x1": 13, "y0": 5, "y1": 8, "z0": 6, "z1": 8, "color": (250, 232, 150)},
        ]
        slices, z0 = build_slices(parts)
        _cache[key] = StackModel(slices, z0)
    return _cache[key]


def turret_model(color, weapon):
    key = ("turret", color, weapon)
    if key not in _cache:
        metal = (82, 84, 96)
        dark = shade(color, 0.75)
        emblem = (250, 226, 120)
        parts = [
            {"shape": "cyl", "r": 7, "z0": 9, "z1": 14, "color": dark},
            {"shape": "cyl", "r": 6, "z0": 14, "z1": 15, "color": color,
             "details": [(-1, -3, 2, 6, emblem), (-3, -1, 6, 2, emblem)]},
        ]
        if weapon is None:
            parts.append({"shape": "box", "x0": 5, "x1": 12, "y0": -1, "y1": 2, "z0": 11, "z1": 13, "color": (120, 120, 128)})
        elif weapon == "machinegun":
            parts += [{"shape": "box", "x0": 5, "x1": 20, "y0": -3, "y1": -1, "z0": 11, "z1": 13, "color": metal},
                      {"shape": "box", "x0": 5, "x1": 20, "y0": 1, "y1": 3, "z0": 11, "z1": 13, "color": metal},
                      {"shape": "box", "x0": 6, "x1": 10, "y0": -4, "y1": 4, "z0": 10, "z1": 14, "color": (214, 170, 60)}]
        elif weapon == "cannon":
            parts += [{"shape": "box", "x0": 5, "x1": 21, "y0": -2, "y1": 3, "z0": 10, "z1": 14, "color": metal},
                      {"shape": "box", "x0": 18, "x1": 23, "y0": -3, "y1": 4, "z0": 9, "z1": 15, "color": (52, 52, 60)}]
        elif weapon == "shotgun":
            parts += [{"shape": "box", "x0": 5, "x1": 16, "y0": -4, "y1": 5, "z0": 10, "z1": 14, "color": metal},
                      {"shape": "box", "x0": 15, "x1": 18, "y0": -5, "y1": 6, "z0": 9, "z1": 15, "color": (204, 120, 50)}]
        elif weapon == "rocket":
            parts += [{"shape": "box", "x0": -3, "x1": 15, "y0": -6, "y1": 7, "z0": 14, "z1": 19, "color": (74, 112, 70)},
                      {"shape": "cyl", "r": 2, "cx": 14, "cy": -3, "z0": 15, "z1": 18, "color": (236, 80, 60)},
                      {"shape": "cyl", "r": 2, "cx": 14, "cy": 3, "z0": 15, "z1": 18, "color": (236, 80, 60)}]
        elif weapon == "railgun":
            parts += [{"shape": "box", "x0": 5, "x1": 25, "y0": -1, "y1": 2, "z0": 11, "z1": 13, "color": (60, 70, 92)},
                      {"shape": "box", "x0": 8, "x1": 10, "y0": -3, "y1": 4, "z0": 10, "z1": 14, "color": (90, 206, 255)},
                      {"shape": "box", "x0": 14, "x1": 16, "y0": -3, "y1": 4, "z0": 10, "z1": 14, "color": (90, 206, 255)},
                      {"shape": "box", "x0": 20, "x1": 22, "y0": -3, "y1": 4, "z0": 10, "z1": 14, "color": (90, 206, 255)}]
        elif weapon == "bouncer":
            parts += [{"shape": "box", "x0": 5, "x1": 16, "y0": -2, "y1": 3, "z0": 11, "z1": 13, "color": metal},
                      {"shape": "cyl", "r": 4, "cx": 17, "cy": 0, "z0": 9, "z1": 15, "color": (172, 112, 250)}]
        slices, z0 = build_slices(parts)
        _cache[key] = StackModel(slices, z0)
    return _cache[key]


# =====================================================================
#  MAP OBJECTS   (footprint on screen = 32 wide x 24 tall: the floor is tilted)
# =====================================================================
TH = 24          # a tile's floor seen at an angle: 32 px wide, 24 px tall
WALL_H = 20      # how tall walls stand


def wall_sprite(theme, n, e, s, w, seed=0):
    """Stone wall block. n/e/s/w = wall next to it? (walls join up seamlessly).
    Chipped top edges, plus moss / snow / rust depending on the map."""
    key = ("wall", theme["name"], n, e, s, w, seed % 3)
    if key in _cache:
        return _cache[key]
    top_c, front_c = theme["wall"]
    h = WALL_H
    surf = pygame.Surface((T, TH + h), pygame.SRCALPHA)
    rng = _rng("wall", theme["name"], n, e, s, w, seed % 3)
    top = pygame.Rect(0, 0, T, TH)
    surf.fill(top_c, top)
    mortar = shade(top_c, 0.8)
    for row, y in enumerate(range(0, TH, 6)):
        pygame.draw.line(surf, mortar, (0, y), (T, y))
        for x in range((row % 2) * 8, T, 16):
            pygame.draw.line(surf, mortar, (x, y), (x, y + 5))
            if rng.random() < 0.4:
                surf.fill(shade(top_c, rng.choice((1.08, 0.94))), (x + 1, y + 1, 14, 2))
    _speckle(surf, top, [shade(top_c, 0.88), shade(top_c, 1.12)], 26, rng)
    if rng.random() < 0.6:
        x, y = rng.randrange(4, 28), rng.randrange(2, 12)
        for _ in range(7):
            surf.set_at((x, y), shade(top_c, 0.6))
            x += rng.choice((-1, 0, 1))
            y += 1
    if not s:
        front = pygame.Rect(0, TH, T, h)
        surf.fill(front_c, front)
        for row, y in enumerate(range(TH, TH + h, 5)):
            pygame.draw.line(surf, shade(front_c, 0.74), (0, y), (T, y))
            for x in range((row % 2) * 10, T, 20):
                pygame.draw.line(surf, shade(front_c, 0.74), (x, y), (x, y + 4))
            if rng.random() < 0.5:
                surf.fill(shade(front_c, 1.08), (rng.randrange(0, 24), y + 1, 8, 2))
        surf.fill(shade(front_c, 1.15), (0, TH, T, 1))
        surf.fill(shade(front_c, 0.62), (0, TH + h - 4, T, 3))
        pygame.draw.line(surf, OUTLINE, (0, TH + h - 1), (T - 1, TH + h - 1))
    # theme decoration
    if theme["name"] == "valley":
        for _ in range(rng.randint(2, 5)):
            x = rng.randrange(0, T - 4)
            surf.fill((92, 150, 64), (x, rng.randrange(0, TH - 3), rng.randint(3, 7), 2))
            if not s:
                surf.fill((80, 132, 56), (x, TH, 2, rng.randint(2, 6)))
    elif theme["name"] == "frost" and not n:
        for x in range(0, T, 2):
            surf.fill((248, 252, 255), (x, 0, 2, rng.randint(2, 5)))
    elif theme["name"] == "scrap":
        for _ in range(2):
            surf.fill((150, 96, 60), (rng.randrange(0, T - 3), rng.randrange(TH, TH + h - 6) if not s else rng.randrange(0, TH - 4), 2, 4))
    # chipped edges where the wall ends
    if not n:
        pygame.draw.line(surf, shade(top_c, 1.25), (0, 1), (T - 1, 1))
        for x in range(0, T, 3):
            if rng.random() < 0.3:
                surf.fill((0, 0, 0, 0), (x, 0, rng.randint(2, 4), rng.randint(1, 2)))
    if not w:
        pygame.draw.line(surf, shade(top_c, 1.15), (1, 0), (1, TH - 1))
    if not e:
        pygame.draw.line(surf, shade(top_c, 0.75), (T - 2, 0), (T - 2, TH - 1))
    # outline only on the outside edges
    mask_img = surf.copy()
    out = outlined(mask_img)
    final = pygame.Surface((T, TH + h), pygame.SRCALPHA)
    final.blit(out, (-1, -1))
    if n:   # remove outline seams between joined walls
        final.blit(surf, (0, 0), (0, 0, T, 1))
    if w:
        final.blit(surf, (0, 0), (0, 0, 1, TH + h))
    if e:
        final.blit(surf, (T - 1, 0), (T - 1, 0, 1, TH + h))
    if s:
        final.blit(surf, (0, TH - 1), (0, TH - 1, T, 1))
    _cache[key] = (final, (0, -h))
    return _cache[key]


def barricade_sprite(theme, vertical, joined_a, joined_b, damaged):
    """Concrete jersey barrier with a yellow/black hazard stripe."""
    key = ("barricade", vertical, joined_a, joined_b, damaged)
    if key in _cache:
        return _cache[key]
    concrete = (200, 200, 190) if not damaged else (158, 156, 148)
    if not vertical:
        surf = pygame.Surface((T, 32), pygame.SRCALPHA)
        surf.fill(concrete, (0, 4, T, 8))
        surf.fill(shade(concrete, 1.12), (0, 4, T, 1))
        surf.fill(shade(concrete, 0.8), (0, 12, T, 14))
        for i in range(-12, T + 12, 8):
            pygame.draw.polygon(surf, (236, 186, 40), [(i, 15), (i + 4, 15), (i + 1, 21), (i - 3, 21)])
            pygame.draw.polygon(surf, (40, 36, 40), [(i + 4, 15), (i + 8, 15), (i + 5, 21), (i + 1, 21)])
        surf.fill(shade(concrete, 0.6), (0, 23, T, 3))
        x0 = 0 if joined_a else 1
        x1 = T if joined_b else T - 1
        surf.fill((0, 0, 0, 0), (0, 0, x0, 32))
        surf.fill((0, 0, 0, 0), (x1, 0, T - x1, 32))
        pygame.draw.line(surf, OUTLINE, (x0, 3), (x1 - 1, 3))
        pygame.draw.line(surf, OUTLINE, (x0, 26), (x1 - 1, 26))
        if not joined_a:
            pygame.draw.line(surf, OUTLINE, (x0, 3), (x0, 26))
        if not joined_b:
            pygame.draw.line(surf, OUTLINE, (x1 - 1, 3), (x1 - 1, 26))
        offset = (0, -6)
    else:
        surf = pygame.Surface((T, TH + 14), pygame.SRCALPHA)
        y0 = 0 if joined_a else 2
        y1 = TH if joined_b else TH - 1
        surf.fill(concrete, (10, y0, 12, y1 - y0))
        pygame.draw.line(surf, shade(concrete, 1.15), (10, y0), (10, y1 - 1))
        pygame.draw.line(surf, shade(concrete, 0.8), (21, y0), (21, y1 - 1))
        if not joined_b:
            surf.fill(shade(concrete, 0.78), (10, y1, 12, 12))
            for i in range(10, 22, 6):
                surf.fill((236, 186, 40), (i, y1 + 3, 3, 5))
                surf.fill((40, 36, 40), (i + 3, y1 + 3, 3, 5))
            pygame.draw.line(surf, OUTLINE, (10, y1 + 11), (21, y1 + 11))
        pygame.draw.line(surf, OUTLINE, (9, y0), (9, y1 + (0 if joined_b else 11)))
        pygame.draw.line(surf, OUTLINE, (22, y0), (22, y1 + (0 if joined_b else 11)))
        if not joined_a:
            pygame.draw.line(surf, OUTLINE, (10, y0 - 1), (21, y0 - 1))
        offset = (0, -12)
    if damaged:
        rng = _rng("bdmg", vertical)
        for _ in range(6):
            surf.fill((90, 88, 84), (rng.randrange(10, 22), rng.randrange(6, 22), 2, 1))
    _cache[key] = (surf, offset)
    return _cache[key]


def crate_sprite(kind, damaged, seed=0):
    key = ("crate", kind, damaged, seed % 2)
    if key in _cache:
        return _cache[key]
    w, top_h, h = 26, 19, 15
    surf = pygame.Surface((w, top_h + h), pygame.SRCALPHA)
    if kind == "crate":
        c = (180, 116, 60) if not damaged else (140, 90, 48)
        if seed % 2:
            c = shade(c, 0.9)
        surf.fill(c, (0, 0, w, top_h))
        for y in range(0, top_h, 5):
            pygame.draw.line(surf, shade(c, 0.7), (0, y), (w, y))
            pygame.draw.line(surf, shade(c, 1.16), (0, y + 1), (w, y + 1))
        pygame.draw.rect(surf, shade(c, 0.58), (0, 0, w, top_h), 2)
        for x, y in ((2, 2), (w - 3, 2), (2, top_h - 3), (w - 3, top_h - 3)):
            surf.set_at((x, y), (214, 204, 184))
        front = pygame.Rect(0, top_h, w, h)
        surf.fill(shade(c, 0.74), front)
        for y in range(top_h + 4, top_h + h, 5):
            pygame.draw.line(surf, shade(c, 0.6), (1, y), (w - 2, y))
        pygame.draw.line(surf, shade(c, 0.52), (2, top_h + 2), (w - 3, top_h + h - 2), 2)
        pygame.draw.rect(surf, shade(c, 0.5), front, 2)
        surf.fill(shade(c, 1.2), (0, top_h, w, 1))
    else:
        c = (132, 144, 158) if not damaged else (108, 116, 126)
        surf.fill(c, (0, 0, w, top_h))
        pygame.draw.line(surf, shade(c, 0.75), (2, 2), (w - 3, top_h - 3), 2)
        pygame.draw.line(surf, shade(c, 0.75), (w - 3, 2), (2, top_h - 3), 2)
        pygame.draw.rect(surf, shade(c, 0.62), (0, 0, w, top_h), 2)
        surf.fill(shade(c, 1.25), (1, 1, w - 2, 1))
        for x, y in ((3, 3), (w - 4, 3), (3, top_h - 4), (w - 4, top_h - 4)):
            surf.fill(shade(c, 1.4), (x - 1, y - 1, 2, 2))
        surf.fill(shade(c, 0.7), (0, top_h, w, h))
        for x in range(3, w, 4):
            pygame.draw.line(surf, shade(c, 0.55), (x, top_h + 1), (x, top_h + h - 2))
            pygame.draw.line(surf, shade(c, 0.85), (x + 1, top_h + 1), (x + 1, top_h + h - 2))
        surf.fill((214, 170, 50), (w // 2 - 4, top_h + 4, 8, 4))
    if damaged:
        rng = _rng("cdmg", kind)
        for _ in range(4):
            x, y = rng.randrange(4, w - 4), rng.randrange(3, top_h - 3)
            pygame.draw.line(surf, OUTLINE, (x, y), (x + rng.randint(-4, 4), y + rng.randint(2, 6)))
    surf = outlined(surf)
    _cache[key] = (surf, ((T - surf.get_width()) // 2, TH - surf.get_height() - 1))
    return _cache[key]


def barrel_sprite(damaged):
    key = ("barrel", damaged)
    if key in _cache:
        return _cache[key]
    w, h = 18, 20
    eh = 8
    surf = pygame.Surface((w, eh + h), pygame.SRCALPHA)
    red, dark, light = (206, 52, 44), (128, 30, 30), (242, 124, 100)
    surf.fill(red, (0, eh // 2, w, h))
    surf.fill(dark, (w - 5, eh // 2, 5, h))
    surf.fill(light, (3, eh // 2, 3, h))
    pygame.draw.ellipse(surf, red, (0, h - eh // 2, w, eh))
    pygame.draw.ellipse(surf, dark, (0, h - eh // 2, w, eh), 1)
    surf.fill((238, 198, 52), (0, eh // 2 + 6, w, 3))
    surf.fill((238, 198, 52), (0, eh // 2 + 13, w, 2))
    pygame.draw.ellipse(surf, shade(red, 0.78), (0, 0, w, eh))
    pygame.draw.ellipse(surf, light, (0, 0, w, eh), 1)
    pygame.draw.circle(surf, (60, 30, 30), (w // 2 + 3, eh // 2), 2)
    surf.fill((255, 240, 200), (8, eh // 2 + 7, 2, 1))           # hazard mark
    if damaged:
        surf.fill((60, 30, 30), (6, eh + 2, 3, 2))
    surf = outlined(surf)
    _cache[key] = (surf, ((T - surf.get_width()) // 2, TH - surf.get_height() + 2))
    return _cache[key]


def _blob(rng, cx, cy, rx, ry, points=9, jitter=0.25):
    pts = []
    for i in range(points):
        a = i / points * math.tau
        k = 1 + rng.uniform(-jitter, jitter)
        pts.append((cx + math.cos(a) * rx * k, cy + math.sin(a) * ry * k))
    return pts


def rock_sprite(theme, seed):
    """Rocks in 4 shapes: boulder, spires, layered mesa, rock pile."""
    key = ("rock", theme["name"], seed)
    if key in _cache:
        return _cache[key]
    rng = _rng("rock", theme["name"], seed)
    c = theme["rock"]
    lit, mid, dark = shade(c, 1.22), c, shade(c, 0.7)
    surf = pygame.Surface((48, 70), pygame.SRCALPHA)
    ground = 62
    kind = seed % 4
    if kind == 0:                                   # big boulder
        rx, ry = rng.randint(13, 17), rng.randint(14, 19)
        cy = ground - ry
        pts = _blob(rng, 24, cy, rx, ry, 11, 0.18)
        pts = [(x, min(y, ground)) for x, y in pts]
        pygame.draw.polygon(surf, mid, pts)
        pygame.draw.polygon(surf, dark, _blob(rng, 28, cy + 4, rx * 0.75, ry * 0.8, 9, 0.15))
        pygame.draw.polygon(surf, mid, _blob(rng, 23, cy - 2, rx * 0.75, ry * 0.75, 9, 0.15))
        pygame.draw.polygon(surf, lit, _blob(rng, 19, cy - ry * 0.4, rx * 0.45, ry * 0.35, 8, 0.2))
        for _ in range(3):
            x, y = 24 + rng.randint(-8, 8), cy + rng.randint(-6, 8)
            pygame.draw.line(surf, dark, (x, y), (x + rng.randint(-4, 4), y + rng.randint(3, 6)))
    elif kind == 1:                                 # spires
        for _ in range(rng.randint(3, 4)):
            cx, height, half = rng.randint(10, 38), rng.randint(26, 52), rng.randint(6, 10)
            tip = (cx + rng.randint(-2, 2), ground - height)
            pygame.draw.polygon(surf, mid, [(cx - half, ground), tip, (cx + half, ground)])
            pygame.draw.polygon(surf, lit, [(cx - half, ground), tip, (cx - 1, ground)])
            pygame.draw.polygon(surf, dark, [(cx + 2, ground), tip, (cx + half, ground)])
            for k in range(1, 4):
                y = ground - height * k / 4
                ww = half * (1 - k / 4)
                pygame.draw.line(surf, shade(c, 0.82), (cx - ww, y), (cx + ww, y))
    elif kind == 2:                                 # layered mesa / slab stack
        y = ground
        width = rng.randint(34, 42)
        for layer in range(rng.randint(3, 4)):
            lh = rng.randint(7, 10)
            x0 = 24 - width / 2 + rng.randint(-2, 2)
            pygame.draw.rect(surf, dark, (x0, y - lh, width, lh), border_radius=3)
            pygame.draw.rect(surf, mid, (x0, y - lh, width, lh - 3), border_radius=3)
            pygame.draw.line(surf, lit, (x0 + 2, y - lh), (x0 + width - 3, y - lh))
            y -= lh - 1
            width -= rng.randint(4, 8)
        pygame.draw.ellipse(surf, lit, (24 - width / 2, y - 4, width, 6))
    else:                                           # rock pile
        for _ in range(rng.randint(4, 6)):
            rx = rng.randint(5, 9)
            cx, cy = rng.randint(10, 38), ground - rng.randint(4, 18)
            pygame.draw.ellipse(surf, dark, (cx - rx, cy - rx * 0.8 + 2, rx * 2, rx * 1.6))
            pygame.draw.ellipse(surf, mid, (cx - rx, cy - rx * 0.8, rx * 2, rx * 1.5))
            pygame.draw.ellipse(surf, lit, (cx - rx + 2, cy - rx * 0.8 + 1, rx, rx * 0.6))
    if theme["name"] == "frost":                    # snow cap
        mask = pygame.mask.from_surface(surf)
        for x in range(48):
            for y in range(70):
                if mask.get_at((x, y)):
                    surf.fill((246, 250, 255), (x, y, 1, rng.randint(2, 4)))
                    break
    for _ in range(4):
        surf.fill(shade(c, rng.choice((0.75, 1.15))), (rng.randint(4, 44), ground - rng.randint(0, 3), 3, 2))
    surf = outlined(surf.subsurface(surf.get_bounding_rect()).copy())
    bw, bh = surf.get_size()
    _cache[key] = (surf, ((T - bw) // 2, TH - bh + 3))
    return _cache[key]


def tree_sprite(theme, seed):
    """Trees per theme: round + pine (valley), snowy pine (frost), cactus + dead tree (canyon/scrap)."""
    key = ("tree", theme["name"], seed)
    if key in _cache:
        return _cache[key]
    rng = _rng("tree", theme["name"], seed)
    leaf = theme["leaf"]
    surf = pygame.Surface((52, 72), pygame.SRCALPHA)
    ground = 68
    name = theme["name"]
    kind = {"valley": ("round", "pine", "round"), "frost": ("pine", "pine", "round"),
            "canyon": ("cactus", "dead", "cactus"), "scrap": ("dead", "round", "dead")}[name][seed % 3]
    if kind == "round":
        surf.fill((96, 66, 42), (23, ground - 18, 6, 18))
        surf.fill((70, 48, 30), (26, ground - 18, 3, 18))
        blobs = [(26, ground - 34, 15), (16, ground - 28, 10), (36, ground - 28, 10), (26, ground - 46, 11),
                 (18, ground - 40, 9), (34, ground - 40, 9)]
        for x, y, r in blobs:
            pygame.draw.circle(surf, shade(leaf, 0.72), (x, y + 3), r)
        for x, y, r in blobs:
            pygame.draw.circle(surf, leaf, (x, y), r - 1)
        for x, y, r in blobs:
            pygame.draw.circle(surf, shade(leaf, 1.22), (x - r // 3, y - r // 3), max(2, r // 2))
        for _ in range(50):
            a, d = rng.uniform(0, math.tau), rng.uniform(0, 16)
            surf.set_at((int(26 + math.cos(a) * d), int(ground - 36 + math.sin(a) * d)), shade(leaf, rng.choice((0.78, 1.35))))
        if name == "valley" and rng.random() < 0.5:
            for _ in range(5):
                surf.fill((232, 90, 80), (rng.randint(14, 36), rng.randint(ground - 50, ground - 26), 2, 2))
    elif kind == "pine":
        surf.fill((92, 64, 44), (23, ground - 12, 6, 12))
        for i, (w, y) in enumerate(((22, ground - 12), (18, ground - 26), (13, ground - 39), (8, ground - 50))):
            pts = [(26 - w, y), (26, y - 22), (26 + w, y)]
            pygame.draw.polygon(surf, shade(leaf, 0.7), [(px, py + 2) for px, py in pts])
            pygame.draw.polygon(surf, leaf, pts)
            pygame.draw.polygon(surf, shade(leaf, 1.25), [(26 - w, y), (26, y - 22), (24, y)])
            if name == "frost":
                pygame.draw.polygon(surf, (244, 250, 255), [(26 - w * 0.6, y - 8), (26, y - 22), (26 + w * 0.4, y - 9)])
    elif kind == "cactus":
        g = (96, 160, 76)
        surf.fill(g, (21, ground - 46, 10, 46))
        surf.fill(shade(g, 1.25), (22, ground - 46, 3, 44))
        surf.fill(shade(g, 0.7), (28, ground - 46, 3, 46))
        pygame.draw.ellipse(surf, g, (21, ground - 50, 10, 8))
        for side, y in ((-1, ground - 30), (1, ground - 22)):
            x0 = 21 if side < 0 else 31
            arm_x = x0 - 9 if side < 0 else x0 + 3
            surf.fill(g, (min(x0, arm_x), y, 9, 6))
            surf.fill(g, (arm_x, y - 14, 6, 18))
            surf.fill(shade(g, 1.25), (arm_x, y - 14, 2, 16))
        for y in range(ground - 44, ground - 2, 4):
            surf.set_at((26, y), (236, 232, 200))
        if rng.random() < 0.5:
            surf.fill((236, 110, 140), (24, ground - 52, 4, 3))
    else:                                           # dead tree
        bark = (110, 82, 60)
        surf.fill(bark, (23, ground - 30, 6, 30))
        surf.fill(shade(bark, 1.2), (23, ground - 30, 2, 30))
        for _ in range(5):
            x, y = 26, ground - rng.randint(18, 30)
            for _ in range(rng.randint(3, 5)):
                nx, ny = x + rng.randint(-5, 5), y - rng.randint(3, 6)
                pygame.draw.line(surf, bark, (x, y), (nx, ny), 2)
                x, y = nx, ny
    surf = outlined(surf.subsurface(surf.get_bounding_rect()).copy())
    bw, bh = surf.get_size()
    _cache[key] = (surf, ((T - bw) // 2, TH - bh - 2))
    return _cache[key]


def bush_sprite(theme, seed, faded=False):
    key = ("bush", theme["name"], seed, faded)
    if key in _cache:
        return _cache[key]
    rng = _rng("bush", theme["name"], seed)
    leaf = theme["bush"]
    surf = pygame.Surface((42, 30), pygame.SRCALPHA)
    blobs = [(rng.randint(8, 34), rng.randint(11, 19), rng.randint(6, 10)) for _ in range(rng.randint(5, 8))]
    for x, y, r in blobs:
        pygame.draw.circle(surf, shade(leaf, 0.7), (x, y + 3), r)
    for x, y, r in blobs:
        pygame.draw.circle(surf, leaf, (x, y), r - 1)
    for x, y, r in blobs:
        pygame.draw.circle(surf, shade(leaf, 1.2), (x - 2, y - 2), max(1, r // 2))
    for _ in range(40):
        x, y, r = rng.choice(blobs)
        a = rng.uniform(math.pi, math.tau)
        surf.set_at((int(x + math.cos(a) * r), int(y + math.sin(a) * r)), shade(leaf, 1.38))
    if theme["name"] == "valley" and seed % 2:
        for _ in range(6):
            surf.fill(rng.choice(((250, 230, 90), (240, 120, 160), (255, 255, 255))), (rng.randint(6, 34), rng.randint(5, 20), 2, 2))
    if theme["name"] == "frost":
        for x, y, r in blobs:
            surf.fill((244, 250, 255), (x - r // 2, y - r + 1, r, 2))
    surf = outlined(surf.subsurface(surf.get_bounding_rect()).copy())
    if faded:
        surf.set_alpha(110)
    bw, bh = surf.get_size()
    _cache[key] = (surf, ((T - bw) // 2, TH - bh + 2))
    return _cache[key]


# =====================================================================
#  LOOT CRATES + WEAPON ICONS
# =====================================================================
WEAPON_ICON_SHAPES = {}


def weapon_icon(weapon, size=16, color=None):
    """Pixel icon for a weapon (drawn on 16x16, scaled up crisp)."""
    from part2_combat.weapons import WEAPONS
    key = ("icon", weapon, size, color)
    if key in _cache:
        return _cache[key]
    s = pygame.Surface((16, 16), pygame.SRCALPHA)
    c = color or (WEAPONS[weapon]["color"] if weapon in WEAPONS else (150, 150, 160))
    d = shade(c, 0.6)
    if weapon == "machinegun":
        for i, x in enumerate((2, 7, 12)):
            s.fill(d, (x, 5, 3, 9))
            s.fill(c, (x, 3, 3, 9))
            s.fill((255, 240, 200), (x, 3, 1, 3))
    elif weapon == "cannon":
        pygame.draw.ellipse(s, c, (3, 2, 10, 12))
        s.fill(c, (3, 8, 10, 6))
        s.fill(d, (3, 12, 10, 2))
        s.fill((255, 240, 200), (5, 4, 2, 4))
    elif weapon == "shotgun":
        for x, y in ((3, 4), (9, 2), (11, 9), (5, 10), (8, 6)):
            pygame.draw.circle(s, c, (x + 1, y + 1), 2)
            s.set_at((x, y), (255, 240, 200))
    elif weapon == "rocket":
        pygame.draw.polygon(s, c, [(8, 1), (11, 5), (11, 12), (5, 12), (5, 5)])
        s.fill((236, 80, 60), (5, 12, 6, 2))
        s.fill((255, 200, 80), (6, 14, 4, 2))
        s.fill((255, 240, 200), (7, 4, 1, 6))
    elif weapon == "railgun":
        pygame.draw.lines(s, c, False, [(2, 13), (6, 7), (9, 10), (14, 2)], 3)
        pygame.draw.lines(s, (255, 255, 255), False, [(2, 13), (6, 7), (9, 10), (14, 2)], 1)
    elif weapon == "bouncer":
        pygame.draw.circle(s, c, (8, 8), 5)
        pygame.draw.circle(s, (255, 255, 255), (6, 6), 2)
        s.fill(d, (1, 7, 2, 2))
        s.fill(d, (13, 7, 2, 2))
    else:
        pygame.draw.circle(s, c, (8, 8), 6, 2)
        pygame.draw.line(s, c, (4, 12), (12, 4), 2)
    s = outlined(s)
    img = pygame.transform.scale(s, (size, size))
    _cache[key] = img
    return img


def loot_sprite(kind, weapon):
    """Reference-style loot: green ammo box with a star, white medkit with a green cross,
    or a box painted in a weapon's colour (you can see what's inside)."""
    from part2_combat.weapons import WEAPONS
    key = ("loot", kind, weapon)
    if key in _cache:
        return _cache[key]
    w, top_h, h = 22, 15, 9            # squat box: tilted top + front face
    surf = pygame.Surface((w, top_h + h), pygame.SRCALPHA)
    if kind == "health":
        c, front = (230, 236, 244), (170, 182, 198)
    elif weapon is None:
        c, front = (74, 122, 66), (48, 84, 46)
    else:
        c = WEAPONS[weapon]["color"]
        front = shade(c, 0.6)
    surf.fill(c, (0, 0, w, top_h))
    pygame.draw.line(surf, shade(c, 1.22), (0, 0), (w - 1, 0))
    pygame.draw.line(surf, shade(c, 1.12), (0, 0), (0, top_h - 1))
    surf.fill(front, (0, top_h, w, h))
    surf.fill(shade(front, 0.72), (0, top_h + h - 2, w, 2))
    pygame.draw.line(surf, shade(c, 0.78), (0, top_h), (w, top_h))
    for x in (3, w - 4):                           # metal straps
        surf.fill(shade(front, 1.35), (x, top_h + 2, 1, h - 4))
    cx, cy = w // 2, top_h // 2
    if kind == "health":
        surf.fill((52, 178, 84), (cx - 2, cy - 5, 4, 10))
        surf.fill((52, 178, 84), (cx - 6, cy - 2, 12, 4))
        surf.fill((130, 224, 150), (cx - 2, cy - 5, 4, 1))
    elif weapon is None:
        pts = []
        for i in range(10):
            r = 6 if i % 2 == 0 else 2.6
            a = -math.pi / 2 + i * math.pi / 5
            pts.append((cx + math.cos(a) * r, cy + 1 + math.sin(a) * r * 0.8))
        pygame.draw.polygon(surf, (248, 212, 66), pts)
        pygame.draw.polygon(surf, (180, 140, 30), pts, 1)
    else:
        icon = weapon_icon(weapon, 12, (255, 255, 255))
        surf.blit(icon, (cx - 6, cy - 6))
        surf.fill((255, 255, 255), (cx - 3, top_h + 3, 6, 2))
    surf = outlined(surf)
    _cache[key] = surf
    return surf
