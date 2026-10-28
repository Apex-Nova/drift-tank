# =====================================================================
#  part4_ui/hud.py  —  ON-SCREEN INFO DURING THE BATTLE
#  OWNER: Person 4 (UI)              WHEN: Phase 3
# =====================================================================
#
# WHAT THIS FILE IS
#   The HUD (heads-up display): health bars, kill counts and the match
#   timer, drawn ON TOP of the game every frame (so it's drawn last).
#
# TOPICS TO STUDY (in this order)
#   1. pygame.draw.rect for bars: a background bar + a filled bar whose
#      width = full_width * (health / max_health)
#   2. pygame.font for small text (create the font ONCE, not every frame —
#      find out why creating it every frame is slow)
#   3. Layout: putting each player's info in its own corner/area
#   4. Formatting time as M:SS (integer division // and modulo %, or f-strings)
#
# WHAT TO BUILD — step by step
#   [ ] Health bar per player, in that player's color
#   [ ] Kills per player
#   [ ] Match timer counting down (if the team uses a time limit)
#   [ ] Dead players shown as "OUT" or greyed
#   [ ] (Optional) bars above each tank's head instead of corners
#
# CONTRACT (see docs/CLASS_CONTRACTS.md)
#   draw_hud(screen, tanks, scoreboard) — called by Person 1's loop each frame.
#   You only READ tank.health / tank.color / tank.player_id / tank.alive.
# =====================================================================


import pygame
_HUD_FONT = None

from shared.settings import TANK_MAX_HEALTH

def draw_hud(screen, tanks,scoreboard):
    global _HUD_FONT
    if _HUD_FONT is None:
        _HUD_FONT = pygame.font.Font(None, 24)
    bar_width = 160
    bar_height = 16

    for index, tank in enumerate(tanks):
        x = 20
        y = 20 + index * 42

        health_ratio = tank.health / TANK_MAX_HEALTH
        health_ratio = max(0,min(health_ratio, 1))

        pygame.draw.rect(screen, (70, 70, 70), (x, y, bar_width, bar_height))
        pygame.draw.rect(
            screen, tank.color,
            (x, y, int(bar_width * health_ratio), bar_height),
        )
        kills = scoreboard.kills.get(tank.player_id, 0)

        if tank.alive:
            text = f"Player {tank.player_id} Kills: {kills}"
            text_color = (255, 255, 255)
        else:
            text = f"Player {tank.player_id} OUT Kills: {kills}"
            text_color = (160, 160, 160)

        label = _HUD_FONT.render(text, True, text_color)
        screen.blit(label, (x, y + 18))

    seconds_left = scoreboard.time_left()
    minutes = seconds_left // 60
    seconds = seconds_left % 60

    timer_text = f"{minutes}:{seconds:02d}"
    timer_label = _HUD_FONT.render(timer_text, True, (255, 255, 255))

    timer_rect = timer_label.get_rect(midtop=(screen.get_width() // 2, 20))
    screen.blit(timer_label, timer_rect)