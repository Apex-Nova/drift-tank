import pygame
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from part4_ui.hud import draw_hud
from shared.settings import TANK_MAX_HEALTH
from shared.settings import TANK_MAX_HEALTH


class SampleTank:
    def __init__(self, player_id, health, color, alive=True):
        self.player_id = player_id
        self.health = health
        self.color = color
        self.alive = alive


class SampleScoreboard:
    kills = {1: 3, 2: 1}

    def time_left(self):
        return 125


pygame.init()
screen = pygame.display.set_mode((900, 600))
pygame.display.set_caption("Drift Tank - HUD Preview")

tanks = [
    SampleTank(1, TANK_MAX_HEALTH, (255, 0, 0)),
    SampleTank(2, TANK_MAX_HEALTH // 2, (0, 0, 255))
]

scoreboard = SampleScoreboard()
clock = pygame.time.Clock()
running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill((45, 55, 75))
    draw_hud(screen, tanks, scoreboard)
    pygame.display.flip()
    clock.tick(60)

pygame.quit()