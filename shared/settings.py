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


MATCH_TIME = 240            # seconds per Team Deathmatch (scoreboard.time_left uses this)
TANK_MAX_HEALTH = 100
class Settings:
    TITLE = "Drift Tank"
    SCREEN_WIDTH = 1280         # logical size; the window scales to any size
    SCREEN_HEIGHT = 720
    FPS = 60
    TILE_SIZE = 32              # map grid: 48 x 36 tiles (world pixels per tile)
    PIXEL_SCALE = 2             # pixel art: the world is drawn small, then scaled up 2x
    BACKGROUND_COLOR = (50, 50, 50)
    WALL_COLOR = (100, 100, 100)
    DESTRUCTIBLE_WALL_COLOR = (150, 75, 0)
    PLAYER_COLORS = [(255, 0, 0), (0, 0, 255), (0, 255, 0), (255, 255, 0)]
    TANK_SPEED = 1.8
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

    # --- loot & weapons ---
    KILL_LIMIT = 15             # Team Deathmatch: first TEAM to this many kills wins
    RESPAWN_MS = 3000           # a destroyed tank comes back after this long (unarmed!)
    SPAWN_SHIELD_MS = 2000      # can't be hurt right after spawning
    CRATE_SPAWN_MS = 3500       # a new loot crate drops this often...
    MAX_CRATES = 9              # ...up to this many on the map
    HEALTH_CRATE_HEAL = 40
    TANK_GRIP = 0.14            # 0-1: lower = more drift
    ICE_GRIP = 0.035

    # --- Battleground: the safe zone shrinks every ~minute ---
    # (seconds to wait, seconds to shrink, new radius in world px, damage per second outside)
    ZONE_STAGES = [(35, 15, 620, 4), (30, 15, 420, 6), (25, 15, 260, 9), (20, 12, 140, 13), (15, 12, 50, 18), (10, 10, 0, 25)]

    # --- online ---
    GAME_PORT = 5555            # laptops join here
    PHONE_PORT = 8080           # phones open http://<host ip>:8080
