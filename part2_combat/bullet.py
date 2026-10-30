import pygame

from shared import settings


class Bullet:
    def __init__(self, x, y, direction, owner, damage=None, speed=None, size=None):
        # Use shared defaults, but allow a tank to customize its own bullet.
        bullet_size = size if size is not None else getattr(settings, "BULLET_SIZE", 10)
        self.rect = pygame.Rect(x, y, bullet_size, bullet_size)

        self.direction = direction
        self.owner = owner
        self.speed = speed if speed is not None else getattr(settings, "BULLET_SPEED", 7)
        self.damage = damage if damage is not None else getattr(settings, "BULLET_DAMAGE", 1)
        self.alive = True

    def update(self):
        # Move the bullet in the direction it was fired.
        dx, dy = self.direction
        self.rect.x += dx * self.speed
        self.rect.y += dy * self.speed

        # Remove it after it leaves the screen.
        width = getattr(settings, "SCREEN_WIDTH", 800)
        height = getattr(settings, "SCREEN_HEIGHT", 600)

        if not pygame.Rect(0, 0, width, height).colliderect(self.rect):
            self.alive = False

    def draw(self, screen):
        # Draw live bullets in the shooter's color.
        if self.alive:
            color = getattr(self.owner, "color", (255, 230, 80))
            pygame.draw.rect(screen, color, self.rect)
