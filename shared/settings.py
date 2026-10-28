# =====================================================================
#  shared/settings.py  —  ONE PLACE FOR ALL SHARED NUMBERS & KEYS
#  OWNER: Person 4 (UI) — the ONLY person who edits this file
#  WHEN: Day 1 (push it together with Person 1's skeleton!)
# =====================================================================
#
# WHAT THIS FILE IS
#   Constants that EVERY part imports, e.g.
#       from shared.settings import SCREEN_WIDTH, TANK_SPEED
#   Keeping them in one file means no one has "magic numbers" scattered
#   around, and changing the game's balance happens in one place.
#
# RULE FOR THE OTHER 3 PEOPLE
#   Need a new constant? Ask Person 4 (message or PR comment). Until it's
#   added, use your own temporary value inside YOUR file, and swap it later.
#
# TOPICS TO STUDY
#   1. Module-level variables and how importing them works
#   2. The UPPER_CASE naming convention for constants
#   3. Colors as (R, G, B) tuples
#   4. Pygame key constants (pygame.K_w, pygame.K_UP, pygame.K_SPACE, ...)
#   5. Dictionaries — e.g. one dict per player describing their keys,
#      and a list of those dicts for players 1–4
#
# WHAT TO PUT IN HERE (suggested list — the team can add more)
#   [ ] Screen: width, height, FPS, window title
#   [ ] Map: TILE_SIZE (screen width/height must divide evenly by it)
#   [ ] Colors: background, wall, destructible wall, each player's color
#   [ ] Tank: speed, size, max health, shoot cooldown (ms)
#   [ ] Bullet: speed, size, damage
#   [ ] Walls: destructible wall health
#   [ ] Power-ups: spawn interval, duration, max on map
#   [ ] Match: time limit (seconds)
#   [ ] Controls for P1–P4: up / down / left / right / shoot keys
#       P1 = WASD + SPACE, P2 = arrows + ENTER, P3/P4 = your choice
#       (careful: some keyboards can't register many keys pressed at once)
#
# DON'T
#   - No functions or classes here, only values.
#   - Don't import other project files here (everyone imports THIS one).
# =====================================================================


MATCH_TIME = 120
TANK_MAX_HEALTH = 100