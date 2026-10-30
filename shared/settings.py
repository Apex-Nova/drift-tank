# =====================================================================
#  shared/settings.py  —  ONE PLACE FOR ALL SHARED NUMBERS & KEYS
#  OWNER: Person 4 (UI) — the ONLY person who edits this file
#  WHEN: Day 1 (push it together with Person 1's skeleton!)
# =====================================================================
#
# WHAT THIS FILE IS
#   Constants that EVERY part imports, grouped in one class, e.g.
#       from shared.settings import Settings
#       Settings.SCREEN_WIDTH, Settings.TANK_SPEED
#   (Starter version written by Person 1 so the skeleton runs —
#    Person 4: it's yours now, keep the names stable or tell the team.)
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
#   - Only values in here (inside the Settings class) — no functions/logic.
#   - Don't import other project files here (everyone imports THIS one).
# =====================================================================


MATCH_TIME = 120
TANK_MAX_HEALTH = 100
class Settings:
    SCREEN_WIDTH = 800
    SCREEN_HEIGHT = 600
    FPS = 60
    TILE_SIZE = 40
    BACKGROUND_COLOR = (50, 50, 50)
    WALL_COLOR = (100, 100, 100)
    DESTRUCTIBLE_WALL_COLOR = (150, 75, 0)
    PLAYER_COLORS = [(255, 0, 0), (0, 0, 255), (0, 255, 0), (255, 255, 0)]
    TANK_SPEED = 3
    TANK_SIZE = (40, 40)
    TANK_MAX_HEALTH = 100
    TANK_SHOOT_COOLDOWN = 500
    BULLET_SPEED = 10
    BULLET_SIZE = (10, 10)
    BULLET_DAMAGE = 25
    DESTRUCTIBLE_WALL_HEALTH = 50
    POWERUP_SPAWN_INTERVAL = 10000
    POWERUP_DURATION = 5000
    MAX_POWERUPS_ON_MAP = 3
    MATCH_TIME_LIMIT = 300
