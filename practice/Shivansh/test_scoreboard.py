#from part4_ui.scoreboard import Scoreboard

#scoreboard = Scoreboard()
#print(scoreboard.kills)
#print(scoreboard.time_left())

import pygame
import sys
from pathlib import Path

# Project root ko Python path mein add karna
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from part4_ui.scoreboard import Scoreboard

pygame.init()

screen = pygame.display.set_mode((900, 600))
pygame.display.set_caption("Drift Tank - Scoreboard Preview")

clock = pygame.time.Clock()
font = pygame.font.Font(None, 42)
small_font = pygame.font.Font(None, 28)

scoreboard = Scoreboard()

# Sirf preview ke liye sample kills
scoreboard.kills = {
    1: 5,
    2: 3,
    3: 7,
    4: 2
}

running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill((30, 35, 50))

    title = font.render("DRIFT TANK SCOREBOARD", True, (255, 220, 80))
    screen.blit(title, (220, 100))

    y = 210

    for player_id, kills in scoreboard.kills.items():
        text = small_font.render(
            f"Player {player_id}       Kills: {kills}",
            True,
            (255, 255, 255)
        )
        screen.blit(text, (300, y))
        y += 50

    seconds = scoreboard.time_left()
    minutes = seconds // 60
    remaining_seconds = seconds % 60

    timer = font.render(
        f"Time Left: {minutes}:{remaining_seconds:02d}",
        True,
        (100, 220, 255)
    )
    screen.blit(timer, (320, 440))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()


