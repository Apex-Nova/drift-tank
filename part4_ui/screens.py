# =====================================================================
#  part4_ui/screens.py  —  MAIN MENU, MAP SELECT, JOIN, SETTINGS, HELP
# =====================================================================
# Every screen has the same 3 methods the App calls each frame:
#   handle_event(event)   update_screen()   draw(surface)
# =====================================================================
import random


import pygame

from shared import web

from shared.settings import Settings
from shared.resources import save_prefs
from part2_combat.weapons import WEAPONS, WEAPON_ORDER
from part3_world.maps import MAPS, GameMap
from part4_ui import ui
from part4_ui.assets import get_image, has_image, play_sound, set_volume, get_volume, set_music_volume

W, H = Settings.SCREEN_WIDTH, Settings.SCREEN_HEIGHT
VERSION = "v2.0"


class Backdrop:
    """The live bot battle that plays behind the menus (the 'game recording' hero)."""

    def __init__(self):
        from part1_engine.game import Game
        self.game = Game(mode="demo", map_id=random.choice([m["id"] for m in MAPS]))
        self.shade = pygame.Surface((W, H), pygame.SRCALPHA)
        for x in range(W):                       # dark on the left where the buttons are
            a = int(230 * max(0.0, 1 - x / (W * 0.62)) ** 1.2)
            pygame.draw.line(self.shade, (8, 10, 18, a), (x, 0), (x, H))
        self.vignette = ui.vignette((W, H), 170)
        self.hero = None           # menus show the live pixel-art battle only (same art style as the game)
        self.hero_frames = {}

    def update(self):
        self.game.step()

    def hero_mix(self, now, cycle=14000, fade=1500):
        """0..1: how much of the hero picture to show. Hero art for ~6s, then the
        live battle for ~6s, with smooth crossfades in between."""
        if self.hero is None:
            return 0.0
        t = now % cycle
        half = cycle / 2
        if t < half - fade:
            return 1.0
        if t < half:
            return 1 - (t - (half - fade)) / fade
        if t < cycle - fade:
            return 0.0
        return (t - (cycle - fade)) / fade

    def draw_hero(self, surf, now, alpha):
        """Slow 'Ken Burns' zoom over the hero art."""
        zoom = 1.0 + 0.08 * ((now % 14000) / 14000)
        key = round(zoom, 3)
        if key not in self.hero_frames:
            if len(self.hero_frames) > 40:
                self.hero_frames.clear()
            self.hero_frames[key] = pygame.transform.smoothscale(self.hero, (int(W * zoom), int(H * zoom)))
        img = self.hero_frames[key]
        img.set_alpha(int(alpha))
        surf.blit(img, ((W - img.get_width()) / 2, (H - img.get_height()) / 2))

    def draw(self, surf, darker=False, show_hero=False):
        from part1_engine import renderer
        now = pygame.time.get_ticks()
        mix = self.hero_mix(now) if show_hero else 0.0
        if mix < 1.0:
            renderer.draw_world(self.game, surf)
        if mix > 0.0:
            self.draw_hero(surf, now, 255 * mix)
        surf.blit(self.shade, (0, 0))
        surf.blit(self.vignette, (0, 0))
        if darker:
            dim = pygame.Surface((W, H), pygame.SRCALPHA)
            dim.fill((6, 8, 14, 150))
            surf.blit(dim, (0, 0))


def draw_logo(surf, center, now, scale=1.0):
    if has_image("logo"):
        logo = get_image("logo")
        k = 430 * scale / logo.get_width()
        img = pygame.transform.smoothscale(logo, (int(logo.get_width() * k), int(logo.get_height() * k)))
        surf.blit(img, img.get_rect(center=(center[0], center[1] + 4 * ui.pulse(now, 600))))
        return
    ui.title_text(surf, "DRIFT", (center[0], center[1] - 34 * scale), int(78 * scale), ui.ACCENT)
    ui.title_text(surf, "TANK", (center[0], center[1] + 40 * scale), int(78 * scale), ui.CORAL, (50, 10, 8))
    ui.text(surf, "2.5D LOOT BATTLE", (center[0], center[1] + 92 * scale), int(16 * scale), ui.TEXT, anchor="center")


class MainMenu:
    def __init__(self, app, message=None):
        self.app = app
        self.backdrop = app.backdrop()
        self.message = message
        self.message_until = pygame.time.get_ticks() + 5000
        x, y = 70, 300
        if web.IS_WEB and web.can_host():
            # Android app: internet rooms (relay server) AND Wi-Fi hosting (native DriftNet plugin).
            self.menu = ui.ButtonList([
                ui.Button("PLAY", (x, y, 252, 62), "quick", "primary", sub="quick match vs bots"),
                ui.Button("MAPS", (x + 262, y, 68, 62), "local", "ghost", size=14),
                ui.Button("HOST ONLINE", (x, y + 76, 330, 54), "host_online", "ghost", sub="room code - play with anyone"),
                ui.Button("HOST ON WI-FI", (x, y + 140, 330, 54), "host", "ghost", sub="laptops + phones nearby"),
                ui.Button("JOIN GAME", (x, y + 204, 330, 54), "join", "ghost", sub="Wi-Fi games or room code"),
                ui.Button("HOW TO PLAY", (x, y + 268, 158, 46), "help", "ghost", size=15),
                ui.Button("SETTINGS", (x + 172, y + 268, 158, 46), "settings", "ghost", size=15),
            ])
        elif web.IS_WEB:
            # Website: a browser tab can't open ports, so online play goes through the
            # relay server with room codes (works anywhere with internet).
            self.menu = ui.ButtonList([
                ui.Button("PLAY", (x, y, 252, 62), "quick", "primary", sub="quick match vs bots"),
                ui.Button("MAPS", (x + 262, y, 68, 62), "local", "ghost", size=14),
                ui.Button("HOST ONLINE", (x, y + 76, 330, 54), "host_online", "ghost", sub="get a room code for friends"),
                ui.Button("JOIN GAME", (x, y + 140, 330, 54), "join", "ghost", sub="type a friend's room code"),
                ui.Button("HOW TO PLAY", (x, y + 204, 158, 46), "help", "ghost", size=15),
                ui.Button("SETTINGS", (x + 172, y + 204, 158, 46), "settings", "ghost", size=15),
            ])
        else:
            self.menu = ui.ButtonList([
                ui.Button("PLAY", (x, y - 20, 252, 62), "quick", "primary", sub="quick match vs bots"),
                ui.Button("MAPS", (x + 262, y - 20, 68, 62), "local", "ghost", size=14),
                ui.Button("HOST ONLINE", (x, y + 56, 330, 54), "host_online", "ghost", sub="room code - play with anyone"),
                ui.Button("HOST ON WI-FI", (x, y + 120, 330, 54), "host", "ghost", sub="laptops + phones nearby"),
                ui.Button("JOIN GAME", (x, y + 184, 330, 54), "join", "ghost", sub="Wi-Fi games or room code"),
                ui.Button("HOW TO PLAY", (x, y + 248, 158, 46), "help", "ghost", size=15),
                ui.Button("SETTINGS", (x + 172, y + 248, 158, 46), "settings", "ghost", size=15),
                ui.Button("QUIT", (x, y + 304, 330, 46), "quit", "ghost"),
            ])

    def handle_event(self, event):
        action = self.menu.handle_event(event)
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE and not web.IS_WEB:
            action = "quit"
        if action == "quick":                  # one click from the menu into a match
            play_sound("confirm")
            self.app.start_game("local", random.choice(MAPS)["id"], bots=3, rules=self.app.prefs.get("rules", "br"))
        elif action == "local":
            self.app.go(MapSelect(self.app, "local"))
        elif action == "host":
            self.app.go(MapSelect(self.app, "host"))
        elif action == "host_online":
            self.app.go(MapSelect(self.app, "host", online=True))
        elif action == "join":
            self.app.go(JoinScreen(self.app))
        elif action == "help":
            self.app.go(HelpScreen(self.app))
        elif action == "settings":
            self.app.go(SettingsScreen(self.app))
        elif action == "quit":
            self.app.running = False

    def update_screen(self):
        self.backdrop.update()

    def draw(self, surf):
        now = pygame.time.get_ticks()
        self.backdrop.draw(surf, show_hero=True)
        draw_logo(surf, (235, 160), now)
        self.menu.draw(surf)
        ui.text(surf, "%s   -   Original game - some art from Kenney.nl (CC0)" % VERSION, (70, H - 30), 11, ui.MUTED, kind="narrow")
        if self.backdrop.hero_mix(now) < 0.5:
            ui.text(surf, "LIVE: bots battling on %s" % self.backdrop.game.map.name.upper(), (W - 30, H - 30), 11,
                    ui.MUTED, kind="narrow", anchor="topright")
        if self.message and now < self.message_until:
            r = ui.panel(surf, (W / 2 - 280, 24, 560, 44), color=(80, 20, 20), alpha=220)
            ui.text(surf, self.message, r.center, 15, ui.TEXT, kind="narrow", anchor="center")


class IntroScreen:
    """2.5 second splash when the game opens (desktop): the live battle, logo drops in. Any key skips."""

    LENGTH = 2600

    def __init__(self, app):
        self.app = app
        self.start = pygame.time.get_ticks()
        self.backdrop = app.backdrop()      # the live pixel-art battle (same style as the game)
        self.played = False

    def done(self):
        self.app.go(MainMenu(self.app))

    def handle_event(self, event):
        if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
            self.done()

    def update_screen(self):
        if not self.played:
            self.played = True
            play_sound("big_explosion", 0.5)
        self.backdrop.update()
        if pygame.time.get_ticks() - self.start > self.LENGTH:
            self.done()

    def draw(self, surf):
        t = (pygame.time.get_ticks() - self.start) / self.LENGTH
        self.backdrop.draw(surf, darker=True)
        dim = pygame.Surface((W, H), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 90))
        surf.blit(dim, (0, 0))
        if t > 0.25:
            k = min(1.0, (t - 0.25) / 0.2)
            bounce = (1 - k) ** 2 * -160
            draw_logo(surf, (W / 2, H / 2 - 20 + bounce), pygame.time.get_ticks(), 1.3)
        ui.text(surf, "press any key", (W / 2, H - 50), 13, ui.MUTED, kind="narrow", anchor="midtop")


class MapSelect:
    """Pick the mode, the map (a fresh random layout - press SHUFFLE for another), players and bots."""

    def __init__(self, app, mode, online=False):
        self.online = online              # host an internet room (relay) instead of Wi-Fi
        self.app = app
        self.mode = mode
        self.backdrop = app.backdrop()
        self.index = 0
        self.rules = app.prefs.get("rules", "br")
        self.humans = 1
        self.bots = 3 if mode == "local" else 0
        self.seeds = [random.randrange(1, 10 ** 9) for _ in MAPS]
        self.previews = {}
        self.error = None
        self.cards = []
        cw, ch, gap = 270, 170, 22
        total = 4 * cw + 3 * gap
        for i in range(4):
            self.cards.append(pygame.Rect((W - total) / 2 + i * (cw + gap), 220, cw, ch))
        self.mode_btns = [(pygame.Rect(W / 2 - 330, 140, 320, 50), "br"), (pygame.Rect(W / 2 + 10, 140, 320, 50), "tdm")]
        self.shuffle_btn = pygame.Rect(W / 2 - 80, 470, 160, 34)
        self.rows = []                     # (label, attr, min, max)
        self.rows.append(("BOTS", "bots", 0, 3))
        self.start_btn = ui.Button("START BATTLE" if mode == "local" else "START HOSTING", (W / 2 - 170, 612, 340, 62), "start")
        self.back_btn = ui.Button("BACK", (40, H - 80, 150, 48), "back", "ghost")

    def row_rects(self, i):
        y = 500 + i * 52
        return pygame.Rect(W / 2 + 60, y, 40, 40), pygame.Rect(W / 2 + 170, y, 40, 40), y

    def total_players(self):
        return (self.humans if self.mode == "local" else 1) + self.bots

    def clamp(self):
        self.bots = max(0, min(self.bots, 4 - (self.humans if self.mode == "local" else 1)))
        if self.mode == "local" and self.total_players() < 2:
            self.bots = 2 - self.humans

    def preview(self, i):
        key = (i, self.seeds[i])
        if key not in self.previews:
            self.previews[key] = GameMap(MAPS[i]["id"], self.seeds[i]).preview((self.cards[i].w, self.cards[i].h))
        return self.previews[key]

    def start(self):
        play_sound("confirm")
        self.app.prefs["rules"] = self.rules
        save_prefs(self.app.prefs)
        error = self.app.start_game(self.mode, MAPS[self.index]["id"], bots=self.bots, rules=self.rules,
                                    humans=self.humans, seed=self.seeds[self.index], online=self.online)
        if error:
            self.error = error

    def change(self, attr, delta):
        setattr(self, attr, getattr(self, attr) + delta)
        lo, hi = next((r[2], r[3]) for r in self.rows if r[1] == attr)
        setattr(self, attr, max(lo, min(hi, getattr(self, attr))))
        self.clamp()
        play_sound("click")

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.app.go(MainMenu(self.app))
            elif event.key in (pygame.K_LEFT, pygame.K_a):
                self.index = (self.index - 1) % 4
                play_sound("select", 0.5)
            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                self.index = (self.index + 1) % 4
                play_sound("select", 0.5)
            elif event.key == pygame.K_TAB:
                self.rules = "tdm" if self.rules == "br" else "br"
                play_sound("switch")
            elif event.key == pygame.K_r:
                self.seeds[self.index] = random.randrange(1, 10 ** 9)
                play_sound("switch")
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                self.start()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for rect, rules in self.mode_btns:
                if rect.collidepoint(event.pos):
                    self.rules = rules
                    play_sound("switch")
            for i, r in enumerate(self.cards):
                if r.collidepoint(event.pos):
                    self.index = i
                    play_sound("select")
            if self.shuffle_btn.collidepoint(event.pos):
                self.seeds[self.index] = random.randrange(1, 10 ** 9)
                play_sound("switch")
            for i, (label, attr, lo, hi) in enumerate(self.rows):
                minus, plus, _ = self.row_rects(i)
                if minus.collidepoint(event.pos):
                    self.change(attr, -1)
                elif plus.collidepoint(event.pos):
                    self.change(attr, 1)
            if self.start_btn.rect.collidepoint(event.pos):
                self.start()
            elif self.back_btn.rect.collidepoint(event.pos):
                play_sound("click")
                self.app.go(MainMenu(self.app))

    def update_screen(self):
        self.backdrop.update()

    def draw(self, surf):
        self.backdrop.draw(surf, darker=True)
        mouse = pygame.mouse.get_pos()
        ui.title_text(surf, "CHOOSE YOUR BATTLE", (W / 2, 70), 44)
        sub = ("You against the exact number of bots you pick (friends? use HOST ONLINE)") if self.mode == "local" else \
            "You host an online room. Friends anywhere join with the room code. Bots fill empty slots." if self.online else \
            "You host. Friends join from laptops or phones on the same Wi-Fi. Bots fill empty slots."
        ui.text(surf, sub, (W / 2, 106), 14, ui.MUTED, kind="narrow", anchor="midtop")
        names = {"br": ("BATTLEGROUND", "1 life - shrinking zone - last one wins"),
                 "tdm": ("TEAM DEATHMATCH", "red vs blue - respawns - first to %d" % Settings.KILL_LIMIT)}
        for rect, rules in self.mode_btns:
            on = rules == self.rules
            pygame.draw.rect(surf, ui.ACCENT if on else (28, 32, 48), rect, border_radius=12)
            pygame.draw.rect(surf, (255, 222, 150) if on else (80, 86, 104), rect, 2, border_radius=12)
            ui.text(surf, names[rules][0], (rect.centerx, rect.y + 7), 18, (40, 22, 6) if on else ui.TEXT, anchor="midtop", shadow=False)
            ui.text(surf, names[rules][1], (rect.centerx, rect.y + 30), 11, (60, 36, 10) if on else ui.MUTED,
                    kind="narrow", anchor="midtop", shadow=False)
        for i, r in enumerate(self.cards):
            selected = i == self.index
            rr = r.move(0, -8 if selected else 0)
            pygame.draw.rect(surf, (0, 0, 0), rr.move(0, 8), border_radius=14)
            surf.blit(self.preview(i), rr)
            pygame.draw.rect(surf, ui.ACCENT if selected else (255, 255, 255), rr, 4 if selected else 1, border_radius=12)
            ui.text(surf, MAPS[i]["name"].upper(), (rr.centerx, rr.bottom + 10), 18, ui.ACCENT if selected else ui.TEXT, anchor="midtop")
        ui.text(surf, MAPS[self.index]["blurb"], (W / 2, 446), 14, ui.TEXT, kind="narrow", anchor="center")
        pygame.draw.rect(surf, (40, 46, 66) if self.shuffle_btn.collidepoint(mouse) else (26, 30, 44), self.shuffle_btn, border_radius=10)
        pygame.draw.rect(surf, (90, 96, 116), self.shuffle_btn, 2, border_radius=10)
        ui.text(surf, "SHUFFLE MAP (R)", self.shuffle_btn.center, 12, ui.TEXT, anchor="center", shadow=False)
        for i, (label, attr, lo, hi) in enumerate(self.rows):
            minus, plus, y = self.row_rects(i)
            ui.text(surf, label, (W / 2 + 30, y + 20), 16, ui.TEXT, anchor="midright")
            for rect, sign in ((minus, "-"), (plus, "+")):
                pygame.draw.rect(surf, (30, 34, 50), rect, border_radius=10)
                pygame.draw.rect(surf, ui.ACCENT if rect.collidepoint(mouse) else (90, 96, 116), rect, 2, border_radius=10)
                ui.text(surf, sign, rect.center, 22, ui.TEXT, anchor="center", shadow=False)
            ui.text(surf, str(getattr(self, attr)), ((minus.right + plus.left) / 2, y + 20), 24, ui.TEXT, anchor="center")
        ui.text(surf, "%d TANKS IN THIS BATTLE" % self.total_players(), (W / 2, 600), 11, ui.MUTED, kind="narrow", anchor="midbottom")
        self.start_btn.draw(surf, True)
        self.back_btn.draw(surf, self.back_btn.rect.collidepoint(mouse))
        ui.text(surf, "ARROWS map   TAB mode   R shuffle   ENTER start", (W - 40, H - 62), 11, ui.MUTED,
                kind="narrow", anchor="topright")
        if self.error:
            r = ui.panel(surf, (W / 2 - 330, 680, 660, 32), color=(80, 20, 20), alpha=220)
            ui.text(surf, self.error, r.center, 13, ui.TEXT, kind="narrow", anchor="center")


class JoinScreen:
    """Join a friend: tap a game found on your Wi-Fi, or type the 5-digit room code (any network).
    No IP addresses: hosts announce themselves on the Wi-Fi (part1_engine/lan.py)."""

    BLOCKED_HINT = "This Wi-Fi may block it - ask the host to use HOST ONLINE and share the room code."

    def __init__(self, app):
        self.app = app
        self.backdrop = app.backdrop()
        right = W / 2 + 40
        last = app.prefs.get("last_ip", "")
        self.code = ui.TextInput((right, 236, 360, 60), last if web.is_room_code(last) else "", "e.g. 48213",
                                 allowed="0123456789" if web.IS_WEB else "0123456789.", max_len=15)
        self.code.active = True
        self.name = ui.TextInput((right, 352, 360, 56), app.prefs.get("name", ""), "your name (optional)", max_len=12)
        self.name.active = False
        self.status = None
        self.connect_btn = ui.Button("JOIN ROOM", (right, 440, 360, 62), "connect")
        self.back_btn = ui.Button("BACK", (40, H - 80, 150, 48), "back", "ghost")
        self.pending = 0
        self.target = None                 # room code or host address being joined
        self.target_label = ""
        self.client = None                 # web version: connection being opened
        self.client_started = 0
        self.keypad = []                   # phones: on-screen number pad
        self.rows = []                     # [(rect, ip, info)] games found on the Wi-Fi
        self.opened = pygame.time.get_ticks()
        if web.IS_WEB:
            keys = "123456789<0"
            for i, key in enumerate(keys):
                col, row = i % 3, i // 3
                self.keypad.append((key, pygame.Rect(right + col * 122, 312 + row * 64, 114, 56)))
            self.connect_btn.rect.topleft = (right, 574)
        # who can look for games on the Wi-Fi: the Mac/Windows app and the Android app
        self.finder = None
        if not web.IS_WEB:
            from part1_engine.lan import LanFinder
            self.finder = LanFinder()
        elif web.can_host():
            from part1_engine.webnet import WebFinder
            self.finder = WebFinder()
        pygame.key.start_text_input()

    def leave_screen(self, screen):
        if self.finder is not None:
            self.finder.close()
            self.finder = None
        self.app.go(screen)

    def press_key(self, key):
        play_sound("click")
        if key == "<":
            self.code.value = self.code.value[:-1]
        elif len(self.code.value) < 5:
            self.code.value += key

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for key, rect in self.keypad:
                if rect.collidepoint(event.pos):
                    self.press_key(key)
                    return
            for rect, ip, info in self.rows:
                if rect.collidepoint(event.pos):
                    self.join(ip, info.get("name", "HOST"))
                    return
        self.code.handle_event(event)
        if not web.IS_WEB:
            self.name.handle_event(event)
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE and not web.IS_WEB:
                self.leave_screen(MainMenu(self.app))
            elif event.key == pygame.K_TAB and not web.IS_WEB:
                self.code.active, self.name.active = self.name.active, self.code.active
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self.connect()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.connect_btn.rect.collidepoint(event.pos):
                self.connect()
            elif self.back_btn.rect.collidepoint(event.pos):
                self.leave_screen(MainMenu(self.app))

    def connect(self):
        value = self.code.value.strip()
        if not (web.is_room_code(value) or value.count(".") == 3):
            self.status = ("Type the 5-digit room code from the host's screen.", (255, 140, 120))
            play_sound("empty")
            return
        self.join(value, "room %s" % value if web.is_room_code(value) else value)

    def join(self, target, label):
        if self.pending or self.client is not None:
            return
        play_sound("confirm")
        self.target, self.target_label = target, label
        self.status = ("Joining %s ..." % label, ui.TEXT)
        self.pending = 2           # connect after the "Joining" text has been drawn

    def update_screen(self):
        self.backdrop.update()
        if self.finder is not None:
            self.finder.poll() if hasattr(self.finder, "poll") else None
        if self.pending:
            self.pending -= 1
            if self.pending == 0:
                if web.is_room_code(self.target):
                    self.app.prefs["last_ip"] = self.target
                self.app.prefs["name"] = self.name.value
                save_prefs(self.app.prefs)
                if web.IS_WEB:
                    from part1_engine.webnet import WebClient
                    self.client = WebClient(self.target, self.name.value or web.cg_name())
                    self.client_started = pygame.time.get_ticks()
                    return
                error = self.app.start_game("join", None, host_ip=self.target, name=self.name.value)
                if error:
                    if not web.is_room_code(self.target):
                        error = "Couldn't reach %s. %s" % (self.target_label, self.BLOCKED_HINT)
                    self.status = (error, (255, 140, 120))
                elif self.finder is not None:
                    self.finder.close()
        if self.client is not None:            # web version: wait for the host's "welcome"
            self.client.poll()
            if self.client.ready:
                client, self.client = self.client, None
                if self.finder is not None:
                    self.finder.close()
                self.app.start_game("join", None, name=self.name.value, network=client)
            elif self.client.error or pygame.time.get_ticks() - self.client_started > 8000:
                if web.is_room_code(self.target):
                    message = self.client.error or "No answer from room %s. Check the code." % self.target
                else:
                    message = "Couldn't reach %s. %s" % (self.target_label, self.BLOCKED_HINT)
                self.status = (message, (255, 140, 120))
                self.client.close()
                self.client = None

    def draw(self, surf):
        now = pygame.time.get_ticks()
        mouse = pygame.mouse.get_pos()
        self.backdrop.draw(surf, darker=True)
        ui.title_text(surf, "JOIN A GAME", (W / 2, 90), 48)
        # ---- left: games on this Wi-Fi ----
        left = pygame.Rect(60, 196, W / 2 - 100, 330)
        ui.panel(surf, left, alpha=200)
        ui.text(surf, "GAMES ON YOUR WI-FI", (left.x + 24, left.y + 18), 18, ui.ACCENT)
        self.rows = []
        if self.finder is None:
            ui.text(surf, "Wi-Fi games need the Drift Tank app", (left.x + 24, left.y + 70), 16, ui.TEXT, kind="narrow")
            ui.text(surf, "(Mac, Windows or Android). Here, use a room code.", (left.x + 24, left.y + 100), 16, ui.MUTED,
                    kind="narrow")
        else:
            games = self.finder.games()[:4]
            for i, (ip, info) in enumerate(games):
                rect = pygame.Rect(left.x + 20, left.y + 60 + i * 66, left.w - 40, 58)
                self.rows.append((rect, ip, info))
                hover = rect.collidepoint(mouse)
                ui.panel(surf, rect, color=(44, 52, 86) if hover else (30, 36, 62), alpha=240, radius=12)
                mode = "BATTLEGROUND" if info.get("rules") == "br" else "TEAM DEATHMATCH"
                ui.text(surf, "%s's game" % info.get("name", "HOST"), (rect.x + 18, rect.y + 8), 20, ui.TEXT)
                ui.text(surf, "%s   -   %d / 4 players" % (mode, info.get("players", 1)), (rect.x + 18, rect.y + 34), 14,
                        ui.MUTED, kind="narrow")
                ui.text(surf, "JOIN", (rect.right - 18, rect.centery), 20, ui.ACCENT, anchor="midright")
            if not games:
                dots = "." * (1 + (now // 400) % 3)
                ui.text(surf, "Looking for games" + dots, (left.x + 24, left.y + 70), 18, ui.TEXT, kind="narrow")
                if now - self.opened > 6000:
                    ui.text(surf, "Nothing yet? Make sure the host pressed", (left.x + 24, left.y + 112), 15, ui.MUTED,
                            kind="narrow")
                    ui.text(surf, "HOST ON WI-FI - or use a room code ->", (left.x + 24, left.y + 138), 15, ui.MUTED,
                            kind="narrow")
        # ---- right: room code ----
        right = self.code.rect
        ui.text(surf, "ROOM CODE  (any network)", (right.x, right.y - 32), 18, ui.ACCENT)
        self.code.draw(surf, now)
        if self.keypad:
            for key, rect in self.keypad:
                ui.panel(surf, rect, alpha=230, radius=12)
                ui.text(surf, "DEL" if key == "<" else key, rect.center, 24, ui.TEXT, anchor="center")
        else:
            ui.text(surf, "NAME", (self.name.rect.x, self.name.rect.y - 28), 16, ui.ACCENT)
            self.name.draw(surf, now)
        self.connect_btn.draw(surf, True)
        self.back_btn.draw(surf, self.back_btn.rect.collidepoint(mouse))
        if self.status:
            ui.text(surf, self.status[0], (W / 2, H - 46), 15, self.status[1], kind="narrow", anchor="midtop")


class SettingsScreen:
    def __init__(self, app):
        self.app = app
        self.backdrop = app.backdrop()
        self.focus = 0
        # in a browser the site gives fullscreen (CrazyGames does not allow a game's own button)
        self.rows = ["volume", "music", "fps", "back"] if web.IS_WEB else ["volume", "music", "fullscreen", "fps", "back"]

    def toggle(self, row, direction=1):
        prefs = self.app.prefs
        if row == "volume":
            prefs["volume"] = round(max(0.0, min(1.0, prefs.get("volume", 0.7) + 0.1 * direction)), 1)
            set_volume(prefs["volume"])
            play_sound("click")
        elif row == "music":
            prefs["music"] = round(max(0.0, min(1.0, prefs.get("music", 0.5) + 0.1 * direction)), 1)
            set_music_volume(prefs["music"])
            play_sound("click")
        elif row == "fullscreen":
            prefs["fullscreen"] = not prefs.get("fullscreen", False)
            self.app.set_fullscreen(prefs["fullscreen"])
        elif row == "fps":
            prefs["show_fps"] = not prefs.get("show_fps", False)
        elif row == "back":
            self.app.go(MainMenu(self.app))
        save_prefs(prefs)

    def row_rect(self, i):
        return pygame.Rect(W / 2 - 300, 200 + i * 76, 600, 60)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.app.go(MainMenu(self.app))
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.focus = (self.focus + 1) % len(self.rows)
            elif event.key in (pygame.K_UP, pygame.K_w):
                self.focus = (self.focus - 1) % len(self.rows)
            elif event.key in (pygame.K_LEFT, pygame.K_a):
                self.toggle(self.rows[self.focus], -1)
            elif event.key in (pygame.K_RIGHT, pygame.K_d, pygame.K_RETURN, pygame.K_SPACE):
                self.toggle(self.rows[self.focus], 1)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, row in enumerate(self.rows):
                r = self.row_rect(i)
                if r.collidepoint(event.pos):
                    self.focus = i
                    if row in ("volume", "music"):
                        self.toggle(row, -1 if event.pos[0] < r.centerx + 120 else 1)
                    else:
                        self.toggle(row)

    def update_screen(self):
        self.backdrop.update()

    def draw(self, surf):
        self.backdrop.draw(surf, darker=True)
        ui.title_text(surf, "SETTINGS", (W / 2, 120), 52)
        prefs = self.app.prefs
        labels = {
            "volume": ("SOUND EFFECTS", "<  %d%%  >" % round(prefs.get("volume", 0.7) * 100)),
            "music": ("MUSIC", "<  %d%%  >" % round(prefs.get("music", 0.5) * 100)),
            "fullscreen": ("FULLSCREEN  (F11)", "ON" if prefs.get("fullscreen") else "OFF"),
            "fps": ("SHOW FPS", "ON" if prefs.get("show_fps") else "OFF"),
            "back": ("BACK", ""),
        }
        for i, row in enumerate(self.rows):
            r = self.row_rect(i)
            focused = i == self.focus
            pygame.draw.rect(surf, (40, 46, 66) if focused else (24, 28, 42), r, border_radius=12)
            pygame.draw.rect(surf, ui.ACCENT if focused else (70, 76, 96), r, 2, border_radius=12)
            name, value = labels[row]
            ui.text(surf, name, (r.x + 24, r.centery), 20, ui.TEXT, anchor="midleft", shadow=False)
            ui.text(surf, value, (r.right - 24, r.centery), 20, ui.ACCENT, anchor="midright", shadow=False)


class HelpScreen:
    def __init__(self, app):
        self.app = app
        self.backdrop = app.backdrop()

    def handle_event(self, event):
        if (event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE)) or \
                (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1):
            play_sound("click")
            self.app.go(MainMenu(self.app))

    def update_screen(self):
        self.backdrop.update()

    def draw(self, surf):
        from part1_engine.renderer import weapon_icon
        self.backdrop.draw(surf, darker=True)
        ui.title_text(surf, "HOW TO PLAY", (W / 2, 70), 46)
        left = ui.panel(surf, (60, 120, 560, 520))
        lines = [
            ("THE RULES", ui.ACCENT),
            ("You start with NO weapon.", ui.TEXT),
            ("Drive over a loot crate to get one.", ui.TEXT),
            ("Star box = random weapon.  Cross = +60 health.", ui.TEXT),
            ("Ammo runs out - grab the next crate!", ui.TEXT),
            ("Red barrels explode. Bushes hide you.", ui.TEXT),
            ("BATTLEGROUND: 1 life, zone shrinks.", ui.TEXT),
            ("TEAM DEATHMATCH: first team to %d kills." % Settings.KILL_LIMIT, ui.TEXT),
            ("CONTROLS", ui.ACCENT),
            ("DRIVE: WASD or ARROWS", ui.TEXT),
            ("AIM: MOUSE  (or Q/E, J/K)", ui.TEXT),
            ("FIRE: LEFT CLICK or SPACE", ui.TEXT),
            ("PHONE: left stick drive, right stick aim + fire", ui.TEXT),
            ("P pause" if web.IS_WEB else "ESC or P pause  -  F11 fullscreen", ui.TEXT),
        ]
        for i, (line, color) in enumerate(lines):
            ui.text(surf, line, (left.x + 28, left.y + 24 + i * 36), 14 if color == ui.TEXT else 20, color,
                    kind="narrow" if color == ui.TEXT else "future")
        right = ui.panel(surf, (650, 120, 570, 520))
        ui.text(surf, "WEAPONS", (right.x + 28, right.y + 26), 20, ui.ACCENT)
        desc = {
            "machinegun": "Fast and steady. Lots of ammo.",
            "cannon": "Heavy shell with a small blast.",
            "shotgun": "7 pellets. Brutal up close.",
            "rocket": "Speeds up, big explosion. Rare!",
            "railgun": "Instant beam, pierces tanks. Rare!",
            "bouncer": "Bounces off walls 3 times.",
        }
        for i, key in enumerate(WEAPON_ORDER):
            y = right.y + 74 + i * 72
            surf.blit(weapon_icon(key, 40), (right.x + 28, y))
            stats = WEAPONS[key]
            ui.text(surf, stats["name"].upper(), (right.x + 84, y), 18, stats["color"])
            ui.text(surf, "%s   (%d shots)" % (desc[key], stats["ammo"]), (right.x + 84, y + 26), 14, ui.MUTED, kind="narrow")
        ui.text(surf, "click or press ENTER to go back", (W / 2, H - 50), 13, ui.MUTED, kind="narrow", anchor="midtop")
