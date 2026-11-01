import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))




import pygame
from part4_ui.menu import draw_start_menu, handle_menu_event

pygame.init()

screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("Drift Tank - Menu Preview")

clock = pygame.time.Clock()
running = True

while running:
    for event in pygame.event.get():
        action = handle_menu_event(event)

        if action == "quit":
            running = False
        elif action is not None:
            print("Selected players:", action)

    draw_start_menu(screen)
    pygame.display.flip()

    clock.tick(60)

pygame.quit()