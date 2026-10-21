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
