# =====================================================================
#  part3_world/powerup.py  —  POWER-UPS (speed, rapid fire, shield...)
#  OWNER: Person 3 (World)           WHEN: Phase 4
# =====================================================================
#
# WHAT THIS FILE IS
#   Items that appear on empty tiles every few seconds. When a tank drives
#   over one, the tank gets a temporary bonus, and the item disappears.
#   Two pieces:
#     - PowerUp: one item on the map (position, kind)
#     - PowerUpManager: decides WHEN/WHERE to spawn, checks pickups,
#       and removes effects when their time runs out
#
# TOPICS TO STUDY (in this order)
#   1. Timers with pygame.time.get_ticks(): "has 5000 ms passed since X?"
#   2. The random module: random.choice(), random.randint()
#   3. Picking a free spot: not inside a wall, not on top of a tank
#      (rect.collidelist is useful here)
#   4. Temporary effects: store "until when" on the tank, and undo the
#      effect when the time is up
#   5. Using a string or Enum for the power-up kind ("speed", "shield"...)
#   6. Drawing a shape + a letter on it (pygame.font) so players can tell
#      kinds apart
#
# WHAT TO BUILD — step by step
#   [ ] PowerUp class: rect, kind, draw(screen)
#   [ ] Manager spawns one every N seconds, max K on the map at once
#   [ ] Tank touches power-up → apply the effect → remove the item
#   [ ] Effects wear off after their duration
#   [ ] Kinds: speed boost, rapid fire, shield (+ your own ideas)
#
# CONTRACT (see docs/CLASS_CONTRACTS.md)
#   PowerUpManager with update(tanks, walls) and draw(screen)
#   IMPORTANT: power-ups change tank fields (speed, cooldown, shield).
#   Agree with Person 1 on the exact field names BEFORE coding this.
# =====================================================================
