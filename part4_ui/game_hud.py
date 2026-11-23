# =====================================================================
#  part4_ui/game_hud.py  —  IN-GAME HUD, PAUSE MENU, GAME-OVER SCREEN
# =====================================================================
#   top-left   : every player: colour, name, kills, health, weapon + ammo
#   top-middle : Battleground -> players alive + zone timer
#                Team Deathmatch -> RED score : BLUE score + time
#   top-right  : minimap (walls, zone, tanks, crates, what you can see)
# =====================================================================
import math

import pygame

from shared.settings import Settings
from part2_combat.weapons import WEAPONS
from part3_world.maps import WORLD_W, WORLD_H
from part4_ui import ui, art
from part4_ui.assets import get_font, play_sound
from shared import web

_buttons = []
_minimaps = {}
RED, BLUE = (226, 74, 64), (86, 120, 236)


def handle_click(game, pos):
    for rect, action in _buttons:
        if rect.collidepoint(pos):
            play_sound("click")
            if action == "resume":
                game.paused = False
            elif action == "menu":
                game.leave()
            elif action == "again":
                game.start_match()
            elif action == "pause":
                game.paused = True
            elif action == "start":
                game.begin_match()
            elif action == "ready":
                game.toggle_ready()
            return True
    return False


def _player_row(surf, game, tank, y):
    x, w, h = 12, 262, 44
    ui.panel(surf, (x, y, w, h), alpha=190, radius=10)
    pygame.draw.rect(surf, tank.color, (x + 6, y + 8, 4, h - 16), border_radius=2)
    name = game.label(tank.player_id)
    ui.text(surf, name, (x + 18, y + 5), 13, tank.color)
    kills = game.scoreboard.kills.get(tank.player_id, 0)
    ui.text(surf, "%d" % kills, (x + w - 30, y + 4), 15, ui.TEXT, anchor="topright")
    _skull(surf, x + w - 24, y + 7)
    bar = pygame.Rect(x + 18, y + 23, 110, 7)
    pygame.draw.rect(surf, (8, 10, 16), bar, border_radius=3)
    k = max(0.0, tank.health / tank.max_health)
    if k > 0:
        color = (90, 220, 110) if k > 0.5 else (240, 190, 60) if k > 0.25 else (240, 70, 60)
        pygame.draw.rect(surf, color, (bar.x, bar.y, bar.w * k, bar.h), border_radius=3)
    if not tank.alive:
        if game.rules == "br":
            ui.text(surf, "OUT", (x + 140, y + 21), 12, (255, 110, 100))
        else:
            ui.text(surf, "BACK IN %.1fs" % max(0, (tank.respawn_at - game.now) / 1000), (x + 136, y + 22), 11,
                    (255, 140, 110), kind="narrow")
    elif tank.weapon:
        stats = WEAPONS[tank.weapon]
        surf.blit(art.weapon_icon(tank.weapon, 18), (x + 136, y + 17))
        ammo = pygame.Rect(x + 158, y + 25, 64, 4)
        pygame.draw.rect(surf, (8, 10, 16), ammo)
        pygame.draw.rect(surf, stats["color"], (ammo.x, ammo.y, ammo.w * tank.ammo / stats["ammo"], 4))
        ui.text(surf, str(tank.ammo), (x + w - 10, y + 20), 12, ui.TEXT, anchor="topright", shadow=False)
    else:
        blink = (game.now // 400) % 2 == 0
        ui.text(surf, "GRAB A CRATE!", (x + 136, y + 22), 11, ui.ACCENT if blink else ui.MUTED, kind="narrow")


def _skull(surf, x, y):
    c = (230, 230, 236)
    pygame.draw.circle(surf, c, (x + 5, y + 5), 5)
    surf.fill(c, (x + 2, y + 8, 7, 4))
    surf.fill((20, 20, 26), (x + 2, y + 4, 2, 2))
    surf.fill((20, 20, 26), (x + 7, y + 4, 2, 2))


def _minimap(surf, game):
    key = (game.map.id, game.map.seed)
    if key not in _minimaps:
        _minimaps.clear()
        _minimaps[key] = game.map.preview((200, 150))
    mm = _minimaps[key]
    sw = surf.get_width()
    x, y = sw - mm.get_width() - 12, 12
    frame = pygame.Rect(x - 4, y - 4, mm.get_width() + 8, mm.get_height() + 8)
    ui.panel(surf, frame, alpha=210, radius=8)
    surf.blit(mm, (x, y))
    kx, ky = mm.get_width() / WORLD_W, mm.get_height() / WORLD_H

    def pt(px, py):
        return (int(x + px * kx), int(y + py * ky))
    if game.zone:
        z = game.zone
        clip = surf.get_clip()
        surf.set_clip(pygame.Rect(x, y, mm.get_width(), mm.get_height()))
        cx, cy = pt(z["x"], z["y"])
        pygame.draw.ellipse(surf, (255, 110, 190), (cx - z["r"] * kx, cy - z["r"] * ky, z["r"] * 2 * kx, z["r"] * 2 * ky), 2)
        if 0 < z["nr"] < z["r"]:
            nx, ny = pt(z["nx"], z["ny"])
            pygame.draw.ellipse(surf, (255, 255, 255), (nx - z["nr"] * kx, ny - z["nr"] * ky, z["nr"] * 2 * kx, z["nr"] * 2 * ky), 1)
        surf.set_clip(clip)
    for crate in game.loot.crates:
        surf.fill((255, 220, 90) if crate.kind == "weapon" else (130, 255, 150), (*pt(*crate.pos), 2, 2))
    view = game.camera.view_rect()
    pygame.draw.rect(surf, (255, 255, 255), (*pt(view.x, view.y), view.w * kx, view.h * ky), 1)
    mine = set(game.local_ids())
    for tank in game.tanks:
        if not tank.alive:
            continue
        px, py = pt(*tank.pos)
        pygame.draw.circle(surf, (20, 16, 24), (px, py), 4)
        pygame.draw.circle(surf, tank.color, (px, py), 3)
        if tank.player_id in mine:
            pygame.draw.circle(surf, (255, 255, 255), (px, py), 5, 1)
    return frame


def draw(game, surf):
    global _buttons
    _buttons = []
    sw, sh = surf.get_size()
    now = game.now

    y = 12
    for tank in sorted(game.tanks, key=lambda t: t.player_id):
        _player_row(surf, game, tank, y)
        y += 50
    _minimap(surf, game)

    # ---- top middle ----
    if game.rules == "tdm":
        red, blue = game.team_scores()
        left = game.time_left_value()
        box = ui.panel(surf, (sw / 2 - 130, 10, 260, 56), alpha=205, radius=12)
        ui.text(surf, str(red), (box.x + 44, box.y + 4), 40, RED, kind="narrow", anchor="midtop")
        ui.text(surf, str(blue), (box.right - 44, box.y + 4), 40, BLUE, kind="narrow", anchor="midtop")
        ui.text(surf, "RED", (box.x + 44, box.y + 42), 9, RED, kind="narrow", anchor="midtop")
        ui.text(surf, "BLUE", (box.right - 44, box.y + 42), 9, BLUE, kind="narrow", anchor="midtop")
        ui.text(surf, "%d:%02d" % (left // 60, left % 60), (box.centerx, box.y + 9), 18, ui.TEXT, anchor="midtop")
        ui.text(surf, "FIRST TO %d" % Settings.KILL_LIMIT, (box.centerx, box.y + 34), 10, ui.MUTED, kind="narrow", anchor="midtop")
    else:
        alive = sum(1 for t in game.tanks if t.alive)
        box = ui.panel(surf, (sw / 2 - 190, 10, 380, 56), alpha=205, radius=12)
        ui.text(surf, "%d ALIVE" % alive, (box.x + 18, box.y + 9), 20, ui.TEXT)
        ui.text(surf, "BATTLEGROUND", (box.x + 18, box.y + 34), 10, ui.MUTED, kind="narrow")
        z = game.zone
        if z and game.phase == "playing":
            secs = int(z["timer"] // 1000)
            if z["shrinking"]:
                msg, color = "ZONE CLOSING  %ds" % secs, (255, 120, 190)
            elif z["nr"] < z["r"]:
                msg, color = "ZONE SHRINKS IN %d:%02d" % (secs // 60, secs % 60), ui.TEXT
            else:
                msg, color = "FINAL ZONE", (255, 120, 190)
            ui.text(surf, msg, (box.right - 16, box.y + 12), 12, color, kind="narrow", anchor="topright")
            ui.text(surf, "STAGE %d / %d" % (z["stage"], len(Settings.ZONE_STAGES)), (box.right - 16, box.y + 32), 10,
                    ui.MUTED, kind="narrow", anchor="topright")
        else:
            ui.text(surf, "LAST TANK STANDING", (box.right - 16, box.y + 20), 11, ui.MUTED, kind="narrow", anchor="topright")

    # ---- outside the zone warning ----
    mine = [game.find_tank(i) for i in game.local_ids()]
    if game.zone and any(t is not None and t.alive and game.outside_zone(t.pos) for t in mine):
        if (now // 300) % 2 == 0:
            ui.title_text(surf, "OUTSIDE THE ZONE!", (sw / 2, 110), 26, (255, 110, 190), (60, 10, 40))

    # ---- spectating ----
    if game.mode != "demo" and game.phase == "playing" and mine and not any(t is not None and t.alive for t in mine):
        target = game.find_tank(game.spectate_id) if game.spectate_id else None
        if game.rules == "br":
            msg = "YOU'RE OUT  -  SPECTATING %s  (TAB = next)" % (game.label(target.player_id) if target else "")
            ui.panel(surf, (sw / 2 - 260, sh - 90, 520, 34), alpha=200, radius=8)
            ui.text(surf, msg, (sw / 2, sh - 81), 13, ui.TEXT, kind="narrow", anchor="midtop")

    # ---- kill feed ----
    y = 78
    for killer, victim, weapon, when in game.killfeed[-4:]:
        age = now - when
        if age > 5000:
            continue
        kt, vt = game.find_tank(killer), game.find_tank(victim)
        kc = kt.color if kt else (255, 120, 190)
        vc = vt.color if vt else (200, 200, 200)
        kn = game.label(killer) if kt and killer != victim else ("ZONE" if weapon == "zone" else "BOOM")
        font = get_font(13, "narrow")
        a, b = font.render(kn, True, kc), font.render(game.label(victim), True, vc)
        icon = art.weapon_icon(weapon if weapon in WEAPONS else None, 16)
        total = a.get_width() + b.get_width() + 32
        box = ui.panel(surf, (sw / 2 - total / 2 - 8, y, total + 16, 22), alpha=170, radius=7, border=None)
        surf.blit(a, (box.x + 8, y + 4))
        surf.blit(icon, (box.x + 12 + a.get_width(), y + 3))
        surf.blit(b, (box.x + 34 + a.get_width(), y + 4))
        y += 26

    # ---- announcements ----
    if game.announcement and now < game.announcement[2]:
        msg, color, until = game.announcement
        k = 1 - (until - now) / 900
        size = 96 if len(msg) <= 3 else 38
        ui.title_text(surf, msg, (sw / 2, sh / 2 - 70 - 10 * math.sin(min(1, k) * math.pi)), size, color)
    if game.phase == "countdown":
        rule = "BATTLEGROUND  -  one life, stay inside the zone" if game.rules == "br" else \
            "TEAM DEATHMATCH  -  RED vs BLUE, first to %d" % Settings.KILL_LIMIT
        ui.text(surf, rule, (sw / 2, sh / 2 + 10), 16, ui.TEXT, anchor="midtop")
        # first-time players: the goal + controls, big, while the countdown runs
        box = ui.panel(surf, (sw / 2 - 330, sh / 2 + 52, 660, 112), alpha=200, radius=14)
        ui.text(surf, "DRIVE OVER A CRATE FOR A WEAPON  -  THEN SHOOT!", (sw / 2, box.y + 16), 20, ui.ACCENT,
                anchor="midtop")
        controls = "LEFT STICK drive     RIGHT STICK aim + fire" if game.touch.active else \
            "WASD drive     MOUSE aim     CLICK fire"
        ui.text(surf, controls, (sw / 2, box.y + 62), 20, ui.TEXT, anchor="midtop")

    # ---- bottom: how to join / controls ----
    info = game.join_info()
    line = None
    if info and game.phase not in ("over", "lobby"):
        ip, phone = info
        line = "LAPTOPS JOIN:  %s" % ip + ("      PHONES OPEN:  %s" % phone if phone else "")
        if getattr(game.network, "online", False) and ip[:1].isdigit():
            line = "ROOM CODE:  %s      friends: JOIN GAME and type this code" % ip
        if not ip[:1].isdigit():                # "starting..." or an error message
            line = "ONLINE: %s" % ip
    elif game.mode == "local" and now - game.match_start < 6000 and game.phase != "over":
        line = "WASD / ARROWS drive      MOUSE or Q/E, J/K aim      SPACE / CLICK fire"
        if game.touch.active:
            line = "LEFT STICK drive      RIGHT STICK aim - push to the edge to fire"
    if line:
        img = get_font(13, "narrow").render(line, True, ui.TEXT)
        box = ui.panel(surf, (sw / 2 - img.get_width() / 2 - 14, sh - 36, img.get_width() + 28, 26), alpha=190, radius=8)
        surf.blit(img, (box.x + 14, box.y + 6))

    # web, mouse players: a clickable pause button (Esc can't be used in browsers - it leaves fullscreen)
    if web.IS_WEB and not game.touch.active and game.phase in ("countdown", "playing") and not game.paused:
        from part1_engine.touch import PAUSE_RECT
        ui.panel(surf, PAUSE_RECT, alpha=170, radius=10)
        for dx in (-8, 4):
            pygame.draw.rect(surf, ui.TEXT, (PAUSE_RECT.centerx + dx, PAUSE_RECT.y + 12, 5, 20))
        _buttons.append((pygame.Rect(PAUSE_RECT), "pause"))
    if game.phase == "lobby":
        _lobby(game, surf)
    elif game.phase == "over":
        _game_over(game, surf)
    elif game.paused:
        _pause(game, surf)


def _overlay(surf, alpha=150):
    dim = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
    dim.fill((6, 8, 14, alpha))
    surf.blit(dim, (0, 0))


def _button(surf, label, rect, action, primary=False):
    b = ui.Button(label, rect, action, "primary" if primary else "ghost")
    mouse = pygame.mouse.get_pos()
    b.hover = 1.0 if rect.collidepoint(mouse) else 0.0
    b.draw(surf, rect.collidepoint(mouse))
    _buttons.append((pygame.Rect(rect), action))


def _pause(game, surf):
    _overlay(surf)
    sw, sh = surf.get_size()
    ui.panel(surf, (sw / 2 - 200, sh / 2 - 150, 400, 300))
    ui.text(surf, "PAUSED", (sw / 2, sh / 2 - 120), 40, ui.ACCENT, anchor="midtop")
    if game.mode != "local":
        ui.text(surf, "(online games keep running)", (sw / 2, sh / 2 - 70), 13, ui.MUTED, kind="narrow", anchor="midtop")
    _button(surf, "RESUME", pygame.Rect(sw / 2 - 150, sh / 2 - 30, 300, 56), "resume", True)
    _button(surf, "MAIN MENU", pygame.Rect(sw / 2 - 150, sh / 2 + 45, 300, 56), "menu")


def _lobby(game, surf):
    """Waiting room: who is here, who is READY, and the START (host) / READY (joiner) button."""
    _overlay(surf, 120)
    sw, sh = surf.get_size()
    rows = game.lobby_list() if game.mode == "host" else game.lobby
    ui.title_text(surf, "WAITING ROOM", (sw / 2, 96), 50)
    info = game.join_info()
    if info:
        ip, phone = info
        if getattr(game.network, "online", False) and ip[:1].isdigit():
            sub = "ROOM CODE  %s   -  friends tap JOIN GAME and type it" % ip
        elif ip[:1].isdigit():
            sub = "SAME WI-FI: JOIN GAME with  %s" % ip + ("     PHONE CONTROLLER: %s" % phone if phone else "")
        else:
            sub = ip
        ui.text(surf, sub, (sw / 2, 140), 18, ui.ACCENT, kind="narrow", anchor="midtop")
    else:
        ui.text(surf, "Connected! Press READY, then wait for the host to start.", (sw / 2, 140), 18, ui.ACCENT,
                kind="narrow", anchor="midtop")
    panel = ui.panel(surf, (sw / 2 - 300, 186, 600, 64 + 52 * max(1, len(rows))))
    ui.text(surf, "PLAYERS  %d / 4" % len(rows), (panel.x + 28, panel.y + 18), 15, ui.MUTED)
    for i, (pid, name, ready, kind) in enumerate(rows):
        y = panel.y + 52 + i * 52
        color = art.tank_color(pid, game.rules == "tdm")
        pygame.draw.rect(surf, color, (panel.x + 28, y + 6, 18, 18), border_radius=5)
        label = name + ("  (you)" if pid == game.my_id else "") + ("  - HOST" if kind == "host" and name != "HOST" else "")
        ui.text(surf, label, (panel.x + 60, y + 2), 21, ui.TEXT)
        tag, tag_color = ("READY", ui.TEAL) if ready else ("NOT READY", ui.CORAL)
        if kind == "bot":
            tag, tag_color = "BOT", ui.MUTED
        ui.text(surf, tag, (panel.right - 28, y + 4), 16, tag_color, anchor="topright")
    y = panel.bottom + 26
    if game.mode == "host":
        waiting = [r[1] for r in rows if not r[2]]
        if waiting:
            ui.text(surf, "Waiting for %s to press READY..." % ", ".join(waiting), (sw / 2, y), 15, ui.MUTED,
                    kind="narrow", anchor="midtop")
        else:
            _button(surf, "START MATCH", pygame.Rect(sw / 2 - 160, y, 320, 62), "start", True)
        ui.text(surf, "Players can join until you press START. Bots fill empty slots.", (sw / 2, y + 76), 13,
                ui.MUTED, kind="narrow", anchor="midtop")
    else:
        _button(surf, "READY!" if game.ready else "PRESS WHEN READY", pygame.Rect(sw / 2 - 170, y, 340, 62), "ready",
                not game.ready)
        if game.ready:
            ui.text(surf, "You're ready - waiting for the host to start...", (sw / 2, y + 76), 14, ui.TEAL,
                    kind="narrow", anchor="midtop")
    _button(surf, "LEAVE", pygame.Rect(40, sh - 82, 150, 50), "menu")


def _game_over(game, surf):
    _overlay(surf, 130)
    sw, sh = surf.get_size()
    if game.rules == "tdm" and game.win_team is not None:
        title, color = ("RED TEAM WINS!", RED) if game.win_team == 0 else ("BLUE TEAM WINS!", BLUE)
    elif game.rules == "tdm":
        title, color = "IT'S A DRAW!", ui.ACCENT
    else:
        winner = game.find_tank(game.winner) if game.winner else None
        title = "%s WINS!" % game.label(game.winner).upper() if winner else "NOBODY SURVIVED"
        color = winner.color if winner else ui.ACCENT
    ui.title_text(surf, title, (sw / 2, 110), 60, color)
    rows = sorted(game.tanks, key=lambda t: (-game.scoreboard.kills.get(t.player_id, 0), game.deaths.get(t.player_id, 0)))
    panel = ui.panel(surf, (sw / 2 - 270, 170, 540, 70 + 46 * len(rows)))
    ui.text(surf, "PLAYER", (panel.x + 30, panel.y + 20), 14, ui.MUTED)
    ui.text(surf, "KILLS", (panel.x + 340, panel.y + 20), 14, ui.MUTED, anchor="midtop")
    ui.text(surf, "DEATHS", (panel.x + 450, panel.y + 20), 14, ui.MUTED, anchor="midtop")
    for i, t in enumerate(rows):
        y = panel.y + 54 + i * 46
        pygame.draw.rect(surf, t.color, (panel.x + 30, y + 4, 16, 16), border_radius=4)
        ui.text(surf, game.label(t.player_id), (panel.x + 58, y), 20, ui.TEXT)
        if t.player_id == game.winner:
            ui.text(surf, "MVP", (panel.x + 250, y + 3), 14, ui.ACCENT)
        ui.text(surf, game.scoreboard.kills.get(t.player_id, 0), (panel.x + 340, y), 22, ui.TEXT, anchor="midtop")
        ui.text(surf, game.deaths.get(t.player_id, 0), (panel.x + 450, y), 22, ui.MUTED, anchor="midtop")
    y = panel.bottom + 30
    if game.mode in ("local", "host"):
        _button(surf, "PLAY AGAIN", pygame.Rect(sw / 2 - 310, y, 300, 58), "again", True)
        _button(surf, "MAIN MENU", pygame.Rect(sw / 2 + 10, y, 300, 58), "menu")
        ui.text(surf, "a new random map is generated every match", (sw / 2, y + 70), 12, ui.MUTED, kind="narrow", anchor="midtop")
    else:
        ui.text(surf, "Waiting for the host to start the next match...", (sw / 2, y), 16, ui.MUTED, kind="narrow", anchor="midtop")
        _button(surf, "LEAVE", pygame.Rect(sw / 2 - 150, y + 40, 300, 58), "menu")
