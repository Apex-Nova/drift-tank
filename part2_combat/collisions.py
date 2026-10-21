# =====================================================================
#  part2_combat/collisions.py  —  "WHAT HIT WHAT" + WHAT HAPPENS NEXT
#  OWNER: Person 2 (Combat)          WHEN: Phase 2 → Phase 3
# =====================================================================
#
# WHAT THIS FILE IS
#   Plain functions (no class needed) that the game loop calls once per
#   frame. They look at every bullet, tank and wall and decide:
#   did something touch something else? If yes, what happens?
#
# TOPICS TO STUDY (in this order)
#   1. rect.colliderect(other_rect) — do two rectangles overlap?
#   2. rect.collidelist() / collidelistall() — check one rect against many
#   3. rect.collidepoint() — is a point inside a rect?
#   4. Nested loops: "every bullet vs every tank". Why this is fine for a
#      small game (and what "n × m checks" means)
#   5. Functions that take lists and change the objects in them
#      (Python passes object references — changing bullet.alive inside a
#       function changes the real bullet)
#   6. (Later, optional) pygame.sprite.Group and spritecollide — the
#      "built-in" way. Compare it with doing it by hand.
#
# WHAT TO BUILD — step by step
#   [ ] A function: bullets vs walls
#         bullet touches a wall → bullet dies;
#         if the wall is destructible → tell the wall it was hit (wall.hit)
#   [ ] A function: bullets vs tanks
#         skip the tank that fired the bullet (bullet.owner);
#         hit → tank.take_damage(bullet.damage), bullet dies;
#         if that killed the tank → tell the scoreboard (Person 4) who
#         killed whom
#   [ ] A helper: "does this rect touch any wall?" → True/False
#         (Person 1 uses it so tanks can't drive through walls)
#   [ ] (Optional) tanks bumping into each other
#
# CONTRACT (see docs/CLASS_CONTRACTS.md)
#   You READ: bullet.rect/owner/damage/alive, tank.rect/alive/take_damage(),
#             wall.rect/destructible/hit(), scoreboard.register_kill()
#   You PROVIDE: the functions above, with names agreed in the contracts doc
#
# HOW TO TEST ALONE
#   Fake tanks and fake walls (tiny classes with a .rect) in your practice
#   folder. Print "HIT!" when they collide before doing anything fancier.
# =====================================================================
