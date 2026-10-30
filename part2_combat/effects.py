import pygame


class Explosion:
    """An expanding ring that fades out after a short time."""

    def __init__(self, x, y, color=(255, 150, 30), duration_ms=350):
        self.x = int(x)
        self.y = int(y)
        self.color = color
        self.duration_ms = duration_ms
        self.started_at = pygame.time.get_ticks()

    @property
    def alive(self):
        elapsed = pygame.time.get_ticks() - self.started_at
        return elapsed < self.duration_ms

    def draw(self, screen):
        elapsed = pygame.time.get_ticks() - self.started_at
        if elapsed >= self.duration_ms:
            return

        progress = elapsed / self.duration_ms
        radius = max(2, int(5 + progress * 22))
        alpha = max(0, int(255 * (1 - progress)))

        size = radius * 2 + 4
        surface = pygame.Surface((size, size), pygame.SRCALPHA)

        pygame.draw.circle(
            surface,
            (*self.color, alpha),
            (size // 2, size // 2),
            radius,
            width=3,
        )

        screen.blit(
            surface,
            (self.x - size // 2, self.y - size // 2),
        )


class EffectManager:
    """Stores and draws temporary visual effects."""

    def __init__(self):
        self.effects = []

    def spawn_explosion(self, x, y, color=(255, 150, 30)):
        self.effects.append(Explosion(x, y, color))

    def update(self):
        self.effects = [
            effect for effect in self.effects
            if effect.alive
        ]

    def draw(self, screen):
        for effect in self.effects:
            effect.draw(screen)