# =====================================================================
#  part2_combat/effects.py  —  EXPLOSIONS, HIT FLASHES, SCREEN SHAKE
#  OWNER: Person 2 (Combat)          WHEN: Phase 4 (polish — optional)
# =====================================================================
#
# WHAT THIS FILE IS
#   Short-lived visual effects that make hits feel good. An effect is an
#   object that lives for a fixed time (e.g. 300 ms), draws itself, then
#   disappears. Only start this after bullets + collisions work.
#
# TOPICS TO STUDY
#   1. Objects with a "lifetime": store the spawn time, compare with
#      pygame.time.get_ticks() each frame
#   2. Simple particles: many tiny dots with random directions
#      (the random module: random.uniform, random.randint)
#   3. Transparency: a Surface made with pygame.SRCALPHA, and fading by
#      lowering alpha over time
#   4. Screen shake: drawing everything with a small random offset for a
#      few frames (needs a tiny agreement with Person 1)
#
# WHAT TO BUILD
#   [ ] Explosion effect when a tank dies (growing circle or particles)
#   [ ] Small spark when a bullet hits a wall
#   [ ] A list of active effects that updates/draws/removes itself
#   [ ] (Optional) screen shake on big explosions
#
# CONTRACT
#   Something like spawn_explosion(x, y), update_effects(), draw_effects(screen)
#   — add the exact names to docs/CLASS_CONTRACTS.md before Person 1 calls them.
# =====================================================================
