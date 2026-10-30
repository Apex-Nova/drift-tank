"""Combat ke liye chhote visual effects, jaise explosion."""

import pygame


class Explosion:
    """Ek circle jo dheere-dheere bada aur fade hota hai."""

    def __init__(self, x, y, color=(255, 150, 40), duration_ms=350, max_radius=24):
        self.x = int(x)
        self.y = int(y)
        self.color = color
        self.duration_ms = max(1, int(duration_ms))
        self.max_radius = max(1, int(max_radius))
        self.started_at = pygame.time.get_ticks()
        self.alive = True

    def update(self, now_ms=None):
        """Effect ka time update karo; active ho to True return karo."""
        if now_ms is None:
            now_ms = pygame.time.get_ticks()
        self.alive = now_ms - self.started_at < self.duration_ms
        return self.alive

    def draw(self, screen, now_ms=None):
        """Effect ko uske current size aur fade level par draw karo."""
        if not self.alive:
            return
        if now_ms is None:
            now_ms = pygame.time.get_ticks()

        elapsed = max(0, now_ms - self.started_at)
        progress = min(1.0, elapsed / self.duration_ms)
        radius = max(1, round(self.max_radius * progress))
        alpha = round(255 * (1.0 - progress))

        # Transparent layer se effect fade hota hai, main screen change nahi hoti.
        diameter = self.max_radius * 2 + 2
        layer = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
        pygame.draw.circle(
            layer,
            (*self.color, alpha),
            (diameter // 2, diameter // 2),
            radius,
        )
        screen.blit(layer, (self.x - diameter // 2, self.y - diameter // 2))


def spawn_explosion(x, y, color=(255, 150, 40), duration_ms=350, max_radius=24):
    """Explosion banao aur return karo; game loop ise effects list mein dale."""
    return Explosion(x, y, color, duration_ms, max_radius)


def update_effects(effects, now_ms=None):
    """Effects update karo aur jo khatam ho gaye unhe list se hatao."""
    if now_ms is None:
        now_ms = pygame.time.get_ticks()
    effects[:] = [effect for effect in effects if effect.update(now_ms)]


def draw_effects(screen, effects, now_ms=None):
    """Saare active effects screen par draw karo."""
    if now_ms is None:
        now_ms = pygame.time.get_ticks()
    for effect in effects:
        effect.draw(screen, now_ms)
