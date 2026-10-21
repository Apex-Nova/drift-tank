# =====================================================================
#  part3_world/wall.py  —  THE WALL CLASS
#  OWNER: Person 3 (World)           WHEN: Phase 1 → Phase 2
# =====================================================================
#
# WHAT THIS FILE IS
#   One class, Wall. Each wall is one square tile of the map. Two kinds:
#     - solid walls: block tanks and bullets forever
#     - destructible walls: have health, break after a few hits
#
# TOPICS TO STUDY (in this order)
#   1. Python classes (__init__, self, methods)
#   2. pygame.Rect — a wall IS basically a rect with extra info
#   3. pygame.draw.rect(screen, color, rect) — and the optional border width
#   4. Colors as (R, G, B) tuples (they live in shared/settings.py)
#   5. (Phase 4) Images: pygame.image.load, .convert()/.convert_alpha(),
#      screen.blit(image, rect) — drawing a picture instead of a box
#
# WHAT TO BUILD — step by step
#   [ ] Wall stores: rect, destructible (True/False), health, alive
#   [ ] draw(screen): solid and destructible walls look different
#   [ ] hit(damage): only destructible walls lose health; at 0 → not alive
#   [ ] Damaged walls look damaged (darker color, or crack images later)
#
# CONTRACT (see docs/CLASS_CONTRACTS.md)
#   rect, destructible, alive, hit(damage), draw(screen)
#   Person 2 calls hit() when a bullet touches the wall.
#   Person 1 checks tank movement against wall.rect.
#
# HOW TO TEST ALONE
#   In practice/<your-name>/: a window with a few walls. Press a key to
#   call hit() on one and watch it break.
# =====================================================================
