# =====================================================================
#  part1_engine/app.py  —  THE WINDOW + WHICH SCREEN IS SHOWING
# =====================================================================
# The App owns the window and the main loop. It shows ONE screen at a time
# (main menu, map select, join, settings, help, or a Game) and calls its
#     handle_event(event) -> update_screen() -> draw(surface)
# every frame. The window can be resized or made fullscreen (F11); the game
# always draws at 1280 x 720 and pygame scales it to fit.
# =====================================================================
import pygame

from shared.settings import Settings
from shared.resources import load_prefs, save_prefs
from part4_ui import assets


class App:
    def __init__(self, mode=None, host_ip=None):
        pygame.init()
        self.prefs = load_prefs()
        pygame.display.set_caption(Settings.TITLE)
        self.window = pygame.display.set_mode((Settings.SCREEN_WIDTH, Settings.SCREEN_HEIGHT),
                                              pygame.SCALED | pygame.RESIZABLE)
        try:
            icon = assets.get_image("icon") if assets.has_image("icon") else assets.get_image("tank_red")
            pygame.display.set_icon(icon)
        except pygame.error:
            pass
        assets.init_sound()
        assets.set_volume(self.prefs.get("volume", 0.7))
        assets.set_music_volume(self.prefs.get("music", 0.5))
        if self.prefs.get("fullscreen"):
            self.set_fullscreen(True)
        self.clock = pygame.time.Clock()
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
            self.screen = IntroScreen(self)

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

    def start_game(self, mode, map_id, bots=0, host_ip=None, name="", rules="br", humans=1, seed=None):
        """Create a Game and show it. Returns an error message (str) or None."""
        from part1_engine.game import Game
        try:
            game = Game(mode=mode, host_ip=host_ip, map_id=map_id, bots=bots, rules=rules, humans=humans, seed=seed,
                        name=name or self.prefs.get("name", ""), prefs=self.prefs)
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

    def run(self):
        from part4_ui.screens import MainMenu
        from part1_engine.game import Game
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                    self.prefs["fullscreen"] = not self.prefs.get("fullscreen", False)
                    self.set_fullscreen(self.prefs["fullscreen"])
                    save_prefs(self.prefs)
                else:
                    self.screen.handle_event(event)
            self.screen.update_screen()
            self.update_music()
            if isinstance(self.screen, Game) and not self.screen.running:
                message = self.screen.result[1] if self.screen.result else None
                self.screen.close()
                self.go(MainMenu(self, message))
                continue
            self.screen.draw(self.window)
            if self.prefs.get("show_fps"):
                font = assets.get_font(12, "narrow")
                self.window.blit(font.render("%d FPS" % self.clock.get_fps(), True, (255, 255, 255)), (6, 700))
            pygame.display.flip()
            self.clock.tick(Settings.FPS)
        if isinstance(self.screen, Game):
            self.screen.close()
        pygame.quit()
