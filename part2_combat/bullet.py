# =====================================================================
#  part2_combat/bullet.py  —  THE BULLET CLASS
#  OWNER: Person 2 (Combat)          WHEN: Phase 2
# =====================================================================
#
# WHAT THIS FILE IS
#   One class, Bullet. A tank creates a Bullet when it shoots. The bullet
#   flies in a straight line every frame until it hits something or
#   leaves the screen. There will be MANY bullets at once.
#
# TOPICS TO STUDY (in this order)
#   1. Python classes (__init__, self, methods)
#   2. pygame.Rect — position + size, and moving it
#   3. Direction vectors: a direction (dx, dy) times a speed = how far to
#      move this frame. Why (1, 0) * 7 moves right by 7 pixels.
#      Also look at pygame.math.Vector2 as an alternative to plain tuples.
#   4. Rect positions are WHOLE numbers — what happens to slow/diagonal
#      movement, and why some games store a float position separately
#   5. Off-screen check: compare the bullet's rect with the screen's rect
#   6. Managing a list of many objects: why you must NOT remove items from a
#      list while looping over that same list, and 2 safe ways to do it
#   7. pygame.draw.circle / pygame.draw.rect for drawing small things
#
# WHAT TO BUILD — step by step
#   [ ] Bullet stores: rect, owner (the tank that fired it), direction,
#       speed, damage, alive
#   [ ] update(): moves one step in its direction
#   [ ] When it leaves the screen it marks itself not alive
#   [ ] draw(screen): a small circle or rectangle (owner's color is a nice touch)
#   [ ] Agree with Person 1: tank.shoot() creates Bullet(...) — decide
#       together exactly which arguments the constructor takes, and write it
#       into docs/CLASS_CONTRACTS.md
#   [ ] (Stretch) bullets that bounce off walls once
#
# CONTRACT (others rely on these — see docs/CLASS_CONTRACTS.md)
#   rect, owner, direction, damage, alive, update(), draw()
#
# HOW TO TEST ALONE (without waiting for Person 1)
#   In practice/<your-name>/, make a FAKE tank: any tiny class with a .rect
#   and a .direction. Press space → create a bullet from it → watch it fly.
# =====================================================================
