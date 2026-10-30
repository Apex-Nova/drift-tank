# =====================================================================
#  part4_ui/menu.py  —  START SCREEN, GAME-OVER SCREEN, (PAUSE)
#  OWNER: Person 4 (UI)              WHEN: Phase 3 → Phase 4
# =====================================================================
#
# WHAT THIS FILE IS
#   The screens that are NOT the battle itself. Person 1's game loop has a
#   "state" (menu / playing / game_over). When the state is "menu" or
#   "game_over", the loop calls YOUR functions to draw the screen and to
#   find out what the player chose.
#
# TOPICS TO STUDY (in this order)
#   1. pygame.font: pygame.font.Font / SysFont, font.render(text, antialias, color)
#   2. render() gives you a Surface → blit it onto the screen
#   3. Centering text: surface.get_rect(center=(x, y))
#   4. Game states — what a "state machine" is, in plain words
#   5. Handling KEYDOWN events to move a selection up/down and confirm
#   6. Returning a value ("start", "quit", "restart", number of players)
#      instead of changing the game directly — why that keeps parts separate
#
# WHAT TO BUILD — step by step
#   [ ] Start screen: game title + "Press ENTER to start"
#   [ ] Choose number of players (2 / 3 / 4)
#   [ ] Game-over screen: "Player X wins!" (+ final scores) + restart / quit
#   [ ] (Optional) pause screen on ESC, simple animations (blinking text)
#
# CONTRACT (see docs/CLASS_CONTRACTS.md)
#   Something like draw_start_menu(screen), handle_menu_event(event) → action
#   and draw_game_over(screen, winner, scores). Agree names with Person 1.
#
# HOW TO TEST ALONE
#   A tiny loop in practice/<your-name>/ that only shows your menu and
#   prints the action it returns.
# =====================================================================

import pygame


_FONT_CACHE = {}
_PLAYER_COUNTS = (2, 3, 4)
_selected_player_index = 0


def _get_font(size):
    if size not in _FONT_CACHE:
        _FONT_CACHE[size] = pygame.font.Font(None, size)
    return _FONT_CACHE[size]


def _draw_centered_text(screen, text, y, size, color):
    font = _get_font(size)
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect(
        center=(screen.get_width() // 2, y)
    )
    screen.blit(text_surface, text_rect)


def draw_start_menu(screen):
    screen.fill((25, 30, 45))
    center_y = screen.get_height() // 2

    _draw_centered_text(
        screen, "DRIFT TANK", center_y - 130, 64, (255, 255, 255)
    )
    _draw_centered_text(
        screen, "Choose number of players", center_y - 60, 36,
        (220, 220, 220)
    )

    for index, player_count in enumerate(_PLAYER_COUNTS):
        marker = ">" if index == _selected_player_index else " "
        color = (
            (255, 220, 80)
            if index == _selected_player_index
            else (200, 200, 200)
        )
        _draw_centered_text(
            screen,
            f"{marker}  {player_count} Players",
            center_y + index * 45,
            32,
            color,
        )

    _draw_centered_text(
        screen,
        "UP/DOWN: choose    ENTER: start",
        center_y + 160,
        26,
        (220, 220, 220),
    )


def handle_menu_event(event):
    global _selected_player_index

    if event.type == pygame.QUIT:
        return "quit"

    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_UP:
            _selected_player_index = (
                _selected_player_index - 1
            ) % len(_PLAYER_COUNTS)
        elif event.key == pygame.K_DOWN:
            _selected_player_index = (
                _selected_player_index + 1
            ) % len(_PLAYER_COUNTS)
        elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            return _PLAYER_COUNTS[_selected_player_index]

    return None


def draw_game_over(screen, winner, scores):
    screen.fill((25, 30, 45))
    center_y = screen.get_height() // 2

    _draw_centered_text(
        screen, f"Player {winner} wins!", center_y - 100, 54,
        (255, 220, 80)
    )
    _draw_centered_text(
        screen, "Final Scores", center_y - 35, 36, (255, 255, 255)
    )

    for index, (player_id, kills) in enumerate(sorted(scores.items())):
        _draw_centered_text(
            screen,
            f"Player {player_id}: {kills} kills",
            center_y + index * 35,
            28,
            (220, 220, 220),
        )

    _draw_centered_text(
        screen,
        "ENTER: restart    ESC: quit",
        center_y + 170,
        26,
        (220, 220, 220),
    )


def handle_game_over_event(event):
    if event.type == pygame.QUIT:
        return "quit"

    if event.type == pygame.KEYDOWN:
        if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            return "restart"
        if event.key == pygame.K_ESCAPE:
            return "quit"

    return None