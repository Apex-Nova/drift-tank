import pygame
from pygame.math import Vector2

from shared.settings import Settings


class Bullet:
    """A projectile fired by a tank."""

    def __init__(self, owner, direction):
        self.owner = owner
        self.direction = Vector2(direction)

        if self.direction.length_squared() == 0:
            self.direction = Vector2(0, -1)
        else:
            self.direction = self.direction.normalize()

        self.speed = Settings.BULLET_SPEED
        self.damage = Settings.BULLET_DAMAGE
        self.alive = True

        width, height = Settings.BULLET_SIZE
        self.rect = pygame.Rect(0, 0, width, height)

        # Place the bullet just outside the front of its tank.
        offset = max(owner.rect.width, owner.rect.height) / 2
        offset += max(width, height) / 2
        self.position = Vector2(owner.rect.center) + self.direction * offset
        self.rect.center = (round(self.position.x), round(self.position.y))

    def update(self):
        """Move the bullet and mark it dead after it leaves the screen."""
        if not self.alive:
            return

        self.position += self.direction * self.speed
        self.rect.center = (round(self.position.x), round(self.position.y))

        screen_rect = pygame.Rect(
            0,
            0,
            Settings.SCREEN_WIDTH,
            Settings.SCREEN_HEIGHT,
        )
        if not screen_rect.contains(self.rect):
            self.alive = False

    def draw(self, screen):
        """Draw the bullet using its owner's color."""
        if self.alive:
            color = getattr(self.owner, "color", (255, 255, 255))
            pygame.draw.rect(screen, color, self.rect)