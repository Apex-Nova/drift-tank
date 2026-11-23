# =====================================================================
#  part1_engine/app.py  —  THE WINDOW + WHICH SCREEN IS SHOWING
# =====================================================================
# The App owns the window and the main loop. It shows ONE screen at a time
# (main menu, map select, join, settings, help, or a Game) and calls its
#     handle_event(event) -> update_screen() -> draw(surface)
# every frame. The window can be resized or made fullscreen (F11); the game
# always draws at 1280 x 720 and pygame scales it to fit.
# =====================================================================
import sys

import pygame

from shared.settings import Settings
from shared.resources import load_prefs, save_prefs
from part4_ui import assets
from shared import web


class App:
    def __init__(self, mode=None, host_ip=None):
        pygame.init()
        if sys.platform == "emscripten" and pygame.mixer.get_init():
            # The browser plays all sound on the web/phone version (shared/web.py). pygame's own
            # audio engine would keep running on the game's thread and steal time every frame.
            pygame.mixer.quit()
        self.prefs = load_prefs()
        pygame.display.set_caption(Settings.TITLE)
        # On desktop pygame scales the 1280x720 picture to the window (SCALED).
        # In a browser the page already scales the canvas, so SCALED would double it.
        flags = 0 if sys.platform == "emscripten" else pygame.SCALED | pygame.RESIZABLE
        self.window = pygame.display.set_mode((Settings.SCREEN_WIDTH, Settings.SCREEN_HEIGHT), flags)
        try:
            icon = assets.get_image("icon") if assets.has_image("icon") else assets.get_image("tank_red")
            pygame.display.set_icon(icon)
        except pygame.error:
            pass
        assets.init_sound()
        assets.preload_web_sounds()
        web.cg_init()                       # CrazyGames SDK (only in the CrazyGames upload)
        self.frames = 0
        assets.set_volume(self.prefs.get("volume", 0.7))
        assets.set_music_volume(self.prefs.get("music", 0.5))
        if self.prefs.get("fullscreen"):
            self.set_fullscreen(True)
        self.clock = pygame.time.Clock()
        self.frame_ms = 1000 / 60
        self.lag_ms = 0.0
        self.touch_screen = None          # web: is this a phone/tablet? (asked once)
        self.running = True
        self._backdrop = None

        from part4_ui.screens import MainMenu, MapSelect, IntroScreen
        self.screen = None
        if mode == "join" and host_ip:
            error = self.start_game("join", None, host_ip=host_ip)
            if error:
                self.screen = MainMenu(self, error)
        elif mode in ("host", "local"):
            self.screen = MapSelect(self, mode)
        if self.screen is None:
            # web: no "press any key" splash - straight to the menu (one click from PLAY to a match)
            self.screen = MainMenu(self) if web.IS_WEB else IntroScreen(self)

    def backdrop(self):
        """One shared live bot battle for all menu screens."""
        if self._backdrop is None:
            from part4_ui.screens import Backdrop
            self._backdrop = Backdrop()
        return self._backdrop

    def go(self, screen):
        self.screen = screen

    def set_fullscreen(self, on):
        is_full = bool(pygame.display.get_surface().get_flags() & pygame.FULLSCREEN)
        if on != is_full:
            pygame.display.toggle_fullscreen()

    def start_game(self, mode, map_id, bots=0, host_ip=None, name="", rules="br", humans=1, seed=None, network=None, online=False):
        """Create a Game and show it. Returns an error message (str) or None."""
        from part1_engine.game import Game
        try:
            game = Game(mode=mode, host_ip=host_ip, map_id=map_id, bots=bots, rules=rules, humans=humans, seed=seed,
                        name=name or self.prefs.get("name", "") or web.cg_name(), prefs=self.prefs, network=network,
                        online=online)
        except ConnectionError as error:
            return str(error)
        except OSError as error:
            if mode == "host":
                return "Could not start hosting (%s). Is another Drift Tank already hosting?" % error.strerror
            return "Could not connect (%s). Same Wi-Fi? Right IP? Is the host running?" % (error.strerror or error)
        self.go(game)
        return None

    def update_music(self):
        """Menu music in menus, battle music in a match, a jingle when the match ends."""
        from part1_engine.game import Game
        if isinstance(self.screen, Game):
            assets.play_music("victory", loop=False) if self.screen.phase == "over" else assets.play_music("battle")
        else:
            assets.play_music("menu")
        assets.update_music()           # start the next random track when one ends

    def step(self):
        """One frame: events -> update -> draw. Returns False when the app should close."""
        from part4_ui.screens import MainMenu
        from part1_engine.game import Game
        screen_before = self.screen
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_F11 and not web.IS_WEB:
                self.prefs["fullscreen"] = not self.prefs.get("fullscreen", False)
                self.set_fullscreen(self.prefs["fullscreen"])
                save_prefs(self.prefs)
            elif self.is_echo_of_touch(event):
                continue
            else:
                self.screen.handle_event(event)
                for fake in self.touch_as_mouse(event):
                    self.screen.handle_event(fake)
        for _ in range(self.updates_this_frame()):
            self.screen.update_screen()
            if self.screen is not screen_before:
                break
        self.update_music()
        if web.IS_WEB:
            self.crazygames()
        if isinstance(self.screen, Game) and not self.screen.running:
            message = self.screen.result[1] if self.screen.result else None
            self.screen.close()
            self.go(MainMenu(self, message))
            return self.running
        self.screen.draw(self.window)
        if self.prefs.get("show_fps"):
            font = assets.get_font(12, "narrow")
            self.window.blit(font.render("%d FPS" % self.clock.get_fps(), True, (255, 255, 255)), (6, 700))
        pygame.display.flip()
        self.frame_ms = self.clock.tick(Settings.FPS)
        return self.running

    def crazygames(self):
        """CrazyGames: report loading/gameplay, open invite links, 'instant multiplayer'."""
        from part1_engine.game import Game
        from part4_ui.screens import JoinScreen
        self.frames += 1
        if self.frames == 20:
            web.cg_call("dtCG.loaded()")                 # first screen is up: loading done
        if self.frames % 10:
            return
        game = self.screen if isinstance(self.screen, Game) else None
        playing = bool(game and game.mode != "demo" and game.phase in ("countdown", "playing") and not game.paused)
        web.cg_call("dtCG.gameplay(%s)" % ("true" if playing else "false"))
        if self.frames % 30 or not web.cg_ready():
            return
        code = web.cg_take_join()
        if code:                                         # a friend's invite: join their room
            if game is not None:
                game.close()
            screen = JoinScreen(self)
            screen.ip.value = code
            self.go(screen)
            screen.connect()
        elif game is None and web.cg_instant():          # "play with friends": host a room right away
            from part3_world.maps import MAPS
            import random
            self.start_game("host", random.choice(MAPS)["id"], bots=0, online=True)

    def updates_this_frame(self):
        """The game logic is made for exactly 60 updates a second (speeds are 'per update').
        Desktop: the window is capped at 60 frames a second -> 1 update per frame.
        Browser: the screen decides the frame rate. A 144 Hz monitor draws 144 frames a second,
        so most frames get 0 updates; a slow phone at 30 frames gets 2. The game then runs at the
        same speed everywhere (CrazyGames tests 60 / 144 / 165 Hz screens)."""
        if sys.platform != "emscripten":
            return 1
        step = 1000 / 60
        self.lag_ms = min(self.lag_ms + self.frame_ms, step * 4)
        updates = min(2, int(self.lag_ms // step))      # at most 2 per frame: more would slow it further
        self.lag_ms = self.lag_ms - updates * step if updates < 2 else 0.0
        return updates

    def is_echo_of_touch(self, event):
        """Phones also send a pretend mouse click after every tap. We already turned the tap
        into a click ourselves (touch_as_mouse), so drop the phone's copy - otherwise every
        button would be pressed twice."""
        if sys.platform != "emscripten" or event.type not in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION):
            return False
        if self.touch_screen is None:
            from part1_engine.touch import TouchControls
            self.touch_screen = TouchControls.has_touch_screen()
        return self.touch_screen       # on a touch screen we only listen to fingers

    def touch_as_mouse(self, event):
        """In a browser a finger tap doesn't make a mouse click, so menus would ignore it.
        Make the click ourselves (marked touch=True so the Game knows it came from a finger)."""
        if sys.platform != "emscripten" or event.type not in (pygame.FINGERDOWN, pygame.FINGERUP):
            return []
        pos = (int(event.x * Settings.SCREEN_WIDTH), int(event.y * Settings.SCREEN_HEIGHT))
        if event.type == pygame.FINGERDOWN:
            return [pygame.event.Event(pygame.MOUSEMOTION, pos=pos, rel=(0, 0), buttons=(0, 0, 0), touch=True),
                    pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=pos, button=1, touch=True)]
        return [pygame.event.Event(pygame.MOUSEBUTTONUP, pos=pos, button=1, touch=True)]

    def quit(self):
        from part1_engine.game import Game
        if isinstance(self.screen, Game):
            self.screen.close()
        pygame.quit()

    async def run(self):
        """The main loop. It is async so the same code runs in a web browser (pygbag):
        `await asyncio.sleep(0)` hands control back to the browser once per frame."""
        import asyncio
        while self.step():
            await asyncio.sleep(0)
        self.quit()
