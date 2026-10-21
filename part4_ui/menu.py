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
