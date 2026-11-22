# =====================================================================
#  part1_engine/renderer.py  —  DRAWS THE BATTLE (3/4 top-down pixel art)
# =====================================================================
# Every frame:
#   1. the camera picks which part of the big map is visible (and zoom)
#   2. draw onto a SMALL surface, 1 world pixel = 1 pixel:
#        floor -> zone tint -> shadows -> objects/tanks/crates/bullets
#        sorted by depth (y) -> particles -> health bars, names, crown
#   3. scale that small surface up to the window with NO smoothing
#      (crisp pixel art, like the reference)
# =====================================================================
import math
import sys

import pygame
from pygame.math import Vector2

from shared.settings import Settings
from part1_engine.view import OUTLINE, shade, W, H, YS
from part3_world.maps import VIEW_H
from part2_combat.weapons import WEAPONS
from part3_world.loot import FALL_MS
from part4_ui import art
from part4_ui.assets import get_font

_views = {}
LITE = sys.platform == "emscripten"     # web / phone version: skip the most expensive effects
WRECK = (64, 62, 70)

# COLOR GRADING per map (like a film colourist): MULTIPLY tints the whole picture,
# ADD lifts the shadows. Warm golden hour for the canyon, fresh green valley,
# cold blue frost, gritty desaturated scrapyard with teal shadows (teal/orange).
GRADES = {
    "canyon": ((255, 238, 216), (10, 4, 0)),
    "valley": ((242, 255, 236), (2, 8, 6)),
    "frost": ((224, 236, 255), (0, 6, 14)),
    "scrap": ((236, 230, 222), (2, 8, 12)),
}
_vignette = None


def _get_vignette():
    global _vignette
    if _vignette is None:
        _vignette = pygame.Surface((W, H), pygame.SRCALPHA)
        for i in range(40, 0, -1):
            k = i / 40
            rect = pygame.Rect(0, 0, W * (0.7 + 0.7 * k), H * (0.7 + 0.8 * k))
            rect.center = (W // 2, H // 2)
            pygame.draw.ellipse(_vignette, (8, 6, 20, int(110 * k ** 3)), rect)
        inner = pygame.Rect(0, 0, W * 0.72, H * 0.72)
        inner.center = (W // 2, H // 2)
        pygame.draw.ellipse(_vignette, (0, 0, 0, 0), inner)
    return _vignette


def _view_surface(size):
    if size not in _views:
        if len(_views) > 30:
            _views.clear()
        _views[size] = pygame.Surface(size).convert()
    return _views[size]


def weapon_icon(weapon, size):
    return art.weapon_icon(weapon, size)


def _flash(img):
    white = img.copy()
    white.fill((170, 170, 170), special_flags=pygame.BLEND_RGB_ADD)
    return white


def draw_tank(surf, tank, game, cam):
    now = game.now
    alive = tank.alive
    color = tank.color if alive else WRECK
    hull = art.hull_model(color)
    turret = art.turret_model(color, tank.weapon if alive else None)
    vx, vy = cam.to_view(tank.pos.x, tank.pos.y)
    sh, (sx, sy) = hull.shadow(tank.hull_angle)
    surf.blit(sh, (vx - sx + 3, vy - sy + 3))
    img, (ax, ay) = hull.render(tank.hull_angle)
    flash = alive and tank.flash_until > now
    surf.blit(_flash(img) if flash else img, (vx - ax, vy - ay))
    recoil = Vector2(1, 0).rotate(tank.barrel_angle) * -tank.recoil * 0.6
    tx, ty = cam.to_view(tank.pos.x + recoil.x, tank.pos.y + recoil.y)
    img, (ax, ay) = turret.render(tank.barrel_angle)
    surf.blit(_flash(img) if flash else img, (tx - ax, ty - ay))
    if alive and tank.shield_until > now:
        pulse = (now // 120) % 2
        pygame.draw.ellipse(surf, (150, 230, 255) if pulse else (90, 190, 255), (vx - 18, vy - 16, 36, 26), 1)


def draw_crate(surf, crate, now, cam):
    t = now - crate.spawned_at
    gx, gy = cam.to_view(crate.pos.x, crate.pos.y)
    if t < FALL_MS:
        k = t / FALL_MS
        z = 260 * (1 - k) ** 2
        r = int(10 + 8 * (1 - k))
        pygame.draw.ellipse(surf, (255, 236, 140), (gx - r, gy - r * 0.6, r * 2, r * 1.2), 1)
    else:
        z = 1 + (1 if (now // 300 + crate.id) % 2 else 0)
        # thin light beam so crates are easy to spot on the big map
        beam = pygame.Surface((4, 50), pygame.SRCALPHA)
        color = (130, 255, 150) if crate.kind == "health" else (WEAPONS[crate.weapon]["color"] if crate.weapon else (255, 220, 90))
        for y in range(50):
            beam.fill(color + (int(70 * y / 50),), (0, y, 4, 1))
        surf.blit(beam, (gx - 2, gy - 58))
    shrink = max(0.3, 1 - z / 300)
    sw = int(20 * shrink)
    shadow = pygame.Surface((sw, max(2, sw // 2)), pygame.SRCALPHA)
    pygame.draw.ellipse(shadow, (20, 10, 20, 90), shadow.get_rect())
    surf.blit(shadow, (gx - sw // 2, gy - sw // 4 + 2))
    img = art.loot_sprite(crate.kind, crate.weapon)
    surf.blit(img, (gx - img.get_width() // 2, gy - img.get_height() + 6 - int(z)))


def draw_projectile(surf, p, cam):
    stats = WEAPONS[p.weapon]
    gx, gy = cam.to_view(p.pos.x, p.pos.y)
    surf.fill((30, 16, 24), (gx - 1, gy, 3, 1))
    x, y = cam.to_view(p.pos.x, p.pos.y, 10)
    a = math.radians(p.angle)
    dx, dy = math.cos(a), math.sin(a)
    c = stats["color"]
    if p.weapon == "railgun":
        pygame.draw.line(surf, c, (x - dx * 16, y - dy * 16), (x, y), 3)
        pygame.draw.line(surf, (255, 255, 255), (x - dx * 16, y - dy * 16), (x, y), 1)
    elif p.weapon == "rocket":
        tail = (x - dx * 7, y - dy * 7)
        pygame.draw.line(surf, OUTLINE, tail, (x + dx, y + dy), 5)
        pygame.draw.line(surf, (226, 226, 220), tail, (x, y), 3)
        surf.fill((236, 70, 50), (int(x + dx * 1) - 1, int(y + dy * 1) - 1, 3, 3))
        surf.fill((255, 210, 90), (int(tail[0]) - 1, int(tail[1]) - 1, 3, 3))
    elif p.weapon in ("cannon", "bouncer"):
        r = 3 if p.weapon == "cannon" else 3
        pygame.draw.circle(surf, OUTLINE, (x, y), r + 1)
        pygame.draw.circle(surf, c if p.weapon == "bouncer" else (70, 66, 74), (x, y), r)
        surf.fill((255, 255, 255), (x - 1, y - 1, 1, 1))
    else:
        pygame.draw.line(surf, OUTLINE, (x - dx * 4, y - dy * 4), (x + dx, y + dy), 4)
        pygame.draw.line(surf, c, (x - dx * 3, y - dy * 3), (x, y), 2)
        surf.fill((255, 250, 220), (x, y, 1, 1))


def _draw_zone(surf, game, cam):
    zone = game.zone
    if not zone:
        return
    cx, cy = cam.to_view(zone["x"], zone["y"])
    r = int(zone["r"])
    vw, vh = surf.get_size()
    ring = pygame.Rect(cx - r, cy - r * YS, r * 2, r * 2 * YS)
    if not ring.contains(surf.get_rect()):      # some of the screen is outside the safe zone
        surf.blit(_zone_overlay((vw, vh), ring), (0, 0))
    if r > 0:
        pulse = (game.now // 250) % 2
        pygame.draw.ellipse(surf, (255, 110, 190) if pulse else (240, 70, 160), ring, 2)
    nx, ny = cam.to_view(zone["nx"], zone["ny"])
    nr = int(zone["nr"])
    if nr > 0 and nr < r:
        steps = max(12, nr // 6)
        for i in range(0, steps, 2):      # dashed: where the zone will shrink to
            a1, a2 = i / steps * math.tau, (i + 1) / steps * math.tau
            pygame.draw.line(surf, (255, 255, 255), (nx + math.cos(a1) * nr, ny + math.sin(a1) * nr * YS),
                             (nx + math.cos(a2) * nr, ny + math.sin(a2) * nr * YS), 1)


_zone_cache = {"key": None, "img": None}


def _zone_overlay(size, ring):
    """Pink tint outside the safe zone. Only rebuilt when the zone or the camera moves."""
    key = (size, tuple(ring))
    if _zone_cache["key"] != key:
        overlay = pygame.Surface(size, pygame.SRCALPHA)
        overlay.fill((150, 30, 90, 80))
        if ring.w > 0:
            pygame.draw.ellipse(overlay, (0, 0, 0, 0), ring)
        _zone_cache["key"], _zone_cache["img"] = key, overlay
    return _zone_cache["img"]


_tag_cache = {}


def _name_tag(font, label, color):
    """A tank's name with a dark outline, drawn once and reused."""
    key = (label, tuple(color))
    tag = _tag_cache.get(key)
    if tag is None:
        if len(_tag_cache) > 64:
            _tag_cache.clear()
        img = font.render(label, False, color)
        shadow = font.render(label, False, OUTLINE)
        tag = pygame.Surface((img.get_width() + 2, img.get_height() + 2), pygame.SRCALPHA)
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            tag.blit(shadow, (1 + dx, 1 + dy))
        tag.blit(img, (1, 1))
        _tag_cache[key] = tag
    return tag


def _crown(surf, x, y):
    gold, dark = (250, 200, 50), (180, 120, 20)
    pts = [(x - 7, y + 4), (x - 7, y - 2), (x - 3, y + 1), (x, y - 4), (x + 3, y + 1), (x + 7, y - 2), (x + 7, y + 4)]
    pygame.draw.polygon(surf, OUTLINE, [(px, py + 1) for px, py in pts])
    pygame.draw.polygon(surf, gold, pts)
    pygame.draw.line(surf, dark, (x - 7, y + 3), (x + 7, y + 3))
    surf.fill((255, 250, 200), (x - 1, y - 2, 2, 2))


def draw_world(game, screen):
    cam = game.camera
    cam.shake = game.fx.offset()
    now = game.now
    view = _view_surface(cam.view_size)
    view.fill(game.map.theme["bg"])
    view.blit(game.map.ground, (-cam.left, -cam.top))
    view.blit(game.map.bottom_cliff, (-cam.left, VIEW_H - cam.top))
    game.map.draw_water_shimmer(view, cam, now / 1000)
    game.fx.draw_ground(view, cam)
    _draw_zone(view, game, cam)

    visible = cam.view_rect().inflate(120, 160)
    mine = set(game.local_ids())
    items = []
    for obj in game.map.objects:
        if obj.alive and visible.colliderect(obj.rect):
            items.append((obj.depth, 0, obj))
    for tank in game.tanks:
        if (tank.alive or game.rules == "br" or now < tank.respawn_at) and visible.collidepoint(tank.pos):
            items.append((tank.pos.y + 11, 1, tank))
    for crate in game.loot.crates:
        if visible.collidepoint(crate.pos):
            items.append((crate.pos.y + 10, 2, crate))
    for p in game.projectiles:
        if visible.collidepoint(p.pos):
            items.append((p.pos.y + 2, 3, p))
    items.sort(key=lambda it: (it[0], it[1]))

    tanks_alive = [t for t in game.tanks if t.alive]
    for depth, kind, thing in items:
        if kind == 0:
            faded = False
            if thing.kind == "bush":
                faded = any(t.player_id in mine and thing.rect.inflate(6, 6).collidepoint(t.pos) for t in tanks_alive)
            elif thing.kind in ("wall", "rock", "tree"):
                for t in tanks_alive:
                    if t.pos.y + 11 < depth and abs(t.pos.x - thing.rect.centerx) < 26 and depth - 70 < t.pos.y:
                        faded = True
                        break
            game.map.draw_object(view, thing, cam, faded)
        elif kind == 1:
            draw_tank(view, thing, game, cam)
        elif kind == 2:
            draw_crate(view, thing, now, cam)
        else:
            draw_projectile(view, thing, cam)

    game.fx.draw(view, cam)

    # health bars, names, ammo, crown
    font = get_font(8, "pixel")
    leader = game.leader_id()
    my_team = game.my_team()
    for tank in tanks_alive:
        if not visible.collidepoint(tank.pos):
            continue
        x, y = cam.to_view(tank.pos.x, tank.pos.y, 26)
        w = 22
        k = max(0.0, tank.health / tank.max_health)
        if tank.player_id in mine:
            bar = (90, 226, 176)
        elif my_team is not None and game.rules == "tdm" and tank.team == my_team:
            bar = (90, 160, 255)
        else:
            bar = (226, 64, 64)
        pygame.draw.rect(view, OUTLINE, (x - w // 2 - 1, y - 1, w + 2, 5))
        view.fill((60, 40, 50), (x - w // 2, y, w, 3))
        view.fill(bar, (x - w // 2, y, int(w * k), 3))
        view.fill(shade(bar, 1.3), (x - w // 2, y, int(w * k), 1))
        if tank.weapon:
            stats = WEAPONS[tank.weapon]
            pips = min(stats["ammo"], 8)
            filled = math.ceil(tank.ammo / stats["ammo"] * pips)
            for i in range(pips):
                view.fill(stats["color"] if i < filled else (70, 60, 70), (x - pips * 3 // 2 + i * 3, y + 5, 2, 2))
        label = game.label(tank.player_id)
        tag = _name_tag(font, label, tank.color)
        view.blit(tag, (x - tag.get_width() // 2, y - 11))
        if tank.player_id == leader:
            _crown(view, x, y - 16)

    game.fx.draw_texts(view, cam)
    mult, add = GRADES.get(game.map.theme_name, ((255, 255, 255), (0, 0, 0)))
    view.fill(mult, special_flags=pygame.BLEND_RGB_MULT)
    view.fill(add, special_flags=pygame.BLEND_RGB_ADD)
    pygame.transform.scale(view, (W, H), screen)
    if not LITE:                       # the soft dark edge costs a full-screen blend: skip it on phones
        screen.blit(_get_vignette(), (0, 0))

    # mouse reticle (full resolution)
    if game.mouse_active and game.phase != "over":
        me = game.find_tank(game.my_id)
        if me is not None and me.alive:
            mx, my = game.mouse_pos
            color = me.color if me.weapon else (170, 170, 170)
            pygame.draw.circle(screen, OUTLINE, (mx, my), 11, 4)
            pygame.draw.circle(screen, color, (mx, my), 10, 2)
            screen.fill(color, (mx - 1, my - 1, 3, 3))
