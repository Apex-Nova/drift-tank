# =====================================================================
#  part1_engine/touch.py  —  ON-SCREEN TOUCH CONTROLS (phones / tablets)
# =====================================================================
# Used when the game runs on a touch screen (web version on a phone, or
# the Android app). It turns finger touches into the SAME inputs dict the
# keyboard makes, so the rest of the game doesn't care where input came from.
#
#   left half of the screen  -> MOVE stick (appears where your thumb lands)
#   right half of the screen -> AIM stick; push it past the ring to FIRE
#   small  II  button at the top -> pause
#
# pygame gives finger events with x, y from 0.0 to 1.0 (fraction of the
# window), so we multiply by the screen size to get pixels.
# =====================================================================
import sys

import pygame
from pygame.math import Vector2

from shared.settings import Settings

RADIUS = 90             # how far the stick knob can travel (pixels)
FIRE_AT = 0.55          # push the aim stick past 55% of the ring to shoot
PAUSE_RECT = pygame.Rect(Settings.SCREEN_WIDTH // 2 - 30, 92, 60, 44)


class Stick:
    def __init__(self):
        self.finger = None          # id of the finger holding this stick
        self.center = Vector2()
        self.knob = Vector2()

    def push(self):
        """Vector from -1..1: how far and which way the knob is pushed."""
        if self.finger is None:
            return Vector2()
        offset = self.knob - self.center
        if offset.length() > RADIUS:
            offset.scale_to_length(RADIUS)
        return offset / RADIUS


class TouchControls:
    def __init__(self):
        self.active = self.has_touch_screen()   # else becomes True after the first touch
        self.move = Stick()
        self.aim = Stick()
        self.pause_tapped = False

    @staticmethod
    def has_touch_screen():
        """In a browser (web version / Android app) ask the page if this is a touch device."""
        if sys.platform != "emscripten":
            return False
        try:
            import platform as web           # in pygbag, platform.window is the browser's window
            return int(web.window.navigator.maxTouchPoints) > 0
        except Exception:
            return False

    @staticmethod
    def _pos(event):
        return Vector2(event.x * Settings.SCREEN_WIDTH, event.y * Settings.SCREEN_HEIGHT)

    def handle_event(self, event):
        """Returns True if the event was a touch (so the game can ignore the fake mouse event)."""
        if event.type == pygame.FINGERDOWN:
            self.active = True
            pos = self._pos(event)
            if PAUSE_RECT.collidepoint(pos):
                self.pause_tapped = True
                return True
            stick = self.move if pos.x < Settings.SCREEN_WIDTH / 2 else self.aim
            if stick.finger is None:
                stick.finger = event.finger_id
                stick.center = Vector2(pos)
                stick.knob = Vector2(pos)
            return True
        if event.type == pygame.FINGERMOTION:
            for stick in (self.move, self.aim):
                if stick.finger == event.finger_id:
                    stick.knob = self._pos(event)
            return True
        if event.type == pygame.FINGERUP:
            for stick in (self.move, self.aim):
                if stick.finger == event.finger_id:
                    stick.finger = None
            return True
        return False

    def release_all(self):
        self.move.finger = self.aim.finger = None

    def inputs(self):
        """The touch sticks as an inputs dict (same keys the keyboard uses)."""
        move = self.move.push()
        aim = self.aim.push()
        inputs = {"move_x": move.x, "move_y": move.y, "aim_angle": None, "shoot": False}
        if aim.length() > 0.2:
            inputs["aim_angle"] = Vector2(1, 0).angle_to(aim)
            inputs["shoot"] = aim.length() > FIRE_AT
        return inputs

    # ---------- drawing ----------
    def draw(self, surf):
        if not self.active:
            return
        overlay = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
        w, h = surf.get_size()
        self._draw_stick(overlay, self.move, (190, h - 170), (246, 240, 230))
        self._draw_stick(overlay, self.aim, (w - 190, h - 170), (255, 120, 100))
        # pause button
        pygame.draw.rect(overlay, (20, 24, 44, 170), PAUSE_RECT, border_radius=10)
        for dx in (-8, 4):
            pygame.draw.rect(overlay, (246, 240, 230, 230), (PAUSE_RECT.centerx + dx, PAUSE_RECT.y + 12, 5, 20))
        surf.blit(overlay, (0, 0))

    def _draw_stick(self, overlay, stick, home, color):
        center = stick.center if stick.finger is not None else Vector2(home)
        knob = center + stick.push() * RADIUS
        alpha = 150 if stick.finger is not None else 70
        pygame.draw.circle(overlay, (20, 24, 44, alpha), center, RADIUS + 8)
        pygame.draw.circle(overlay, color + (alpha,), center, RADIUS + 8, 3)
        if stick is self.aim:   # inner ring = the fire line
            pygame.draw.circle(overlay, color + (alpha // 2,), center, int(RADIUS * FIRE_AT), 2)
        pygame.draw.circle(overlay, color + (min(255, alpha + 80),), knob, 34)
