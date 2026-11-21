# =====================================================================
#  part4_ui/ui.py  —  SMALL UI KIT: panels, text, buttons, text input
# =====================================================================
# Works with mouse, keyboard (arrows + Enter) and touch screens
# (pygame turns finger taps into mouse clicks).
# =====================================================================
import math

import pygame

from part4_ui.assets import get_font, play_sound

# COLOR THEORY: the UI is built on a complementary pair —
#   cool deep NAVY for backgrounds/panels  <->  warm AMBER for what matters (buttons, titles)
# plus a split-complementary pair for meaning: CORAL = danger/enemy, TEAL = good/you.
# Text is a warm off-white (pure white looks harsh on navy).
ACCENT = (255, 178, 52)        # amber
ACCENT_DARK = (196, 112, 24)
CORAL = (255, 98, 78)
TEAL = (70, 214, 190)
TEXT = (246, 240, 230)
MUTED = (150, 160, 190)
PANEL = (20, 24, 44)           # navy


def panel(surf, rect, color=PANEL, alpha=215, border=(255, 255, 255, 34), radius=14):
    rect = pygame.Rect(rect)
    s = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(s, color + (alpha,), s.get_rect(), border_radius=radius)
    if border:
        pygame.draw.rect(s, border, s.get_rect(), 1, border_radius=radius)
    surf.blit(s, rect)
    return rect


def text(surf, string, pos, size=20, color=TEXT, kind="future", anchor="topleft", shadow=True, alpha=255):
    font = get_font(size, kind)
    img = font.render(str(string), True, color)
    rect = img.get_rect(**{anchor: pos})
    if shadow:
        sh = font.render(str(string), True, (0, 0, 0))
        sh.set_alpha(int(150 * alpha / 255))
        surf.blit(sh, rect.move(2, 2))
    if alpha < 255:
        img.set_alpha(alpha)
    surf.blit(img, rect)
    return rect


def title_text(surf, string, center, size, color=ACCENT, outline=(40, 20, 6)):
    """Big chunky title (Bungee font) with outline + drop shadow."""
    size = int(size * 0.85)
    font = get_font(size, "title")
    base = font.render(string, True, color)
    out = font.render(string, True, outline)
    rect = base.get_rect(center=center)
    for dx, dy in ((-3, 0), (3, 0), (0, -3), (0, 3), (-2, -2), (2, 2), (-2, 2), (2, -2)):
        surf.blit(out, rect.move(dx, dy))
    shadow = font.render(string, True, (0, 0, 0))
    shadow.set_alpha(120)
    surf.blit(shadow, rect.move(6, 8))
    for dx, dy in ((-3, 0), (3, 0), (0, -3), (0, 3)):
        surf.blit(out, rect.move(dx, dy))
    surf.blit(base, rect)
    hi = font.render(string, True, (255, 240, 200))
    hi.set_alpha(90)
    surf.blit(hi, rect.move(0, -2), pygame.Rect(0, 0, rect.width, rect.height // 2))
    return rect


class Button:
    def __init__(self, label, rect, action, style="primary", sub=None, enabled=True, size=22):
        self.label = label
        self.size = size
        self.rect = pygame.Rect(rect)
        self.action = action
        self.style = style
        self.sub = sub
        self.enabled = enabled
        self.hover = 0.0

    def draw(self, surf, focused=False):
        target = 1.0 if focused else 0.0
        self.hover += (target - self.hover) * 0.25
        r = self.rect.move(int(self.hover * 6), 0)
        if self.style == "primary":
            base = ACCENT if self.enabled else (90, 90, 96)
            pygame.draw.rect(surf, ACCENT_DARK if self.enabled else (60, 60, 66), r.move(0, 5), border_radius=12)
            pygame.draw.rect(surf, base, r, border_radius=12)
            pygame.draw.rect(surf, (255, 222, 150), r.inflate(-6, -6), 2, border_radius=10)
            color = (40, 22, 6)
        else:
            fill = (40, 46, 66) if focused else (26, 30, 44)
            pygame.draw.rect(surf, (8, 10, 16), r.move(0, 5), border_radius=12)
            pygame.draw.rect(surf, fill, r, border_radius=12)
            pygame.draw.rect(surf, ACCENT if focused else (255, 255, 255, 40), r, 2, border_radius=12)
            color = TEXT if self.enabled else MUTED
        if self.sub:
            text(surf, self.label, (r.x + 22, r.centery - 2), self.size, color, anchor="bottomleft", shadow=False)
            text(surf, self.sub, (r.x + 22, r.centery + 3), 13, color if self.style == "primary" else MUTED,
                 kind="narrow", anchor="topleft", shadow=False)
        else:
            text(surf, self.label, r.center, self.size, color, anchor="center", shadow=False)


class ButtonList:
    """A vertical menu: arrows/W/S move, Enter/Space/click activates."""

    def __init__(self, buttons):
        self.buttons = buttons
        self.focus = 0

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            for i, b in enumerate(self.buttons):
                if b.rect.collidepoint(event.pos) and i != self.focus:
                    self.focus = i
                    play_sound("select", 0.5)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, b in enumerate(self.buttons):
                if b.rect.collidepoint(event.pos) and b.enabled:
                    self.focus = i
                    play_sound("click")
                    return b.action
        elif event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_DOWN, pygame.K_s):
                self.focus = (self.focus + 1) % len(self.buttons)
                play_sound("select", 0.5)
            elif event.key in (pygame.K_UP, pygame.K_w):
                self.focus = (self.focus - 1) % len(self.buttons)
                play_sound("select", 0.5)
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                b = self.buttons[self.focus]
                if b.enabled:
                    play_sound("click")
                    return b.action
        return None

    def draw(self, surf):
        for i, b in enumerate(self.buttons):
            b.draw(surf, i == self.focus)


class TextInput:
    def __init__(self, rect, value="", placeholder="", allowed=None, max_len=40):
        self.rect = pygame.Rect(rect)
        self.value = value
        self.placeholder = placeholder
        self.allowed = allowed
        self.max_len = max_len
        self.active = True

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.active = self.rect.collidepoint(event.pos)
            if self.active:
                pygame.key.start_text_input()
        elif event.type == pygame.TEXTINPUT and self.active:
            for ch in event.text:
                if (self.allowed is None or ch in self.allowed) and len(self.value) < self.max_len:
                    self.value += ch
        elif event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_BACKSPACE:
                self.value = self.value[:-1]
            elif event.key == pygame.K_v and (event.mod & (pygame.KMOD_CTRL | pygame.KMOD_META)):
                try:
                    pasted = pygame.scrap.get_text() if hasattr(pygame.scrap, "get_text") else ""
                except pygame.error:
                    pasted = ""
                for ch in pasted or "":
                    if (self.allowed is None or ch in self.allowed) and len(self.value) < self.max_len:
                        self.value += ch

    def draw(self, surf, now):
        pygame.draw.rect(surf, (10, 12, 20), self.rect, border_radius=10)
        pygame.draw.rect(surf, ACCENT if self.active else (80, 86, 104), self.rect, 2, border_radius=10)
        shown = self.value or self.placeholder
        color = TEXT if self.value else MUTED
        r = text(surf, shown, (self.rect.x + 16, self.rect.centery), 26, color, anchor="midleft", shadow=False)
        if self.active and (now // 500) % 2 == 0:
            x = r.right + 3 if self.value else self.rect.x + 16
            pygame.draw.line(surf, ACCENT, (x, self.rect.y + 12), (x, self.rect.bottom - 12), 2)


def vignette(size, strength=200):
    w, h = size
    v = pygame.Surface((w, h), pygame.SRCALPHA)
    steps = 40
    # dark edges: concentric ellipses, more transparent toward the middle
    v.fill((0, 0, 0, strength))
    for i in range(steps, 0, -1):
        k = i / steps
        rect = pygame.Rect(0, 0, w * 1.4 * k, h * 1.4 * k)
        rect.center = (w / 2, h / 2)
        pygame.draw.ellipse(v, (0, 0, 0, int(strength * (k ** 2.5))), rect)
    return v


def pulse(now, speed=300):
    return 0.5 + 0.5 * math.sin(now / speed)
