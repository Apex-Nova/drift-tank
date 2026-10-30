import pygame
from part3_world.wall import Wall

pygame.init()
screen = pygame.display.set_mode((400, 300))
wall = Wall(pygame.Rect(100, 100, 50, 50), destructible=True)
running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill((30, 30, 30))
    wall.draw(screen)
    pygame.display.flip()

pygame.quit()
