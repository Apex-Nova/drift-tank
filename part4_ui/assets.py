# =====================================================================
#  part4_ui/assets.py  —  LOADING IMAGES + PLAYING SOUNDS
#  OWNER: Person 4 (UI)              WHEN: Phase 4
# =====================================================================
#
# WHAT THIS FILE IS
#   One place that loads every picture and sound from part4_ui/assets/,
#   so nobody else has to deal with file paths. Others just ask:
#   "give me the tank image" or "play the shoot sound".
#
# TOPICS TO STUDY (in this order)
#   1. pygame.mixer: mixer.init(), mixer.Sound(path), sound.play(),
#      set_volume()
#   2. pygame.mixer.music for one looping background track (different
#      from Sound — find out how)
#   3. pygame.image.load + convert() / convert_alpha() (and why convert
#      only works AFTER the window exists)
#   4. pygame.transform.scale — resizing images to TILE_SIZE
#   5. Paths that work from any folder: __file__ + pathlib.Path
#   6. Loading once into a dictionary (name → Sound/Image), not every frame
#   7. try/except — the game should still run if a sound file is missing
#
# WHAT TO BUILD — step by step
#   [ ] load everything once at startup into dictionaries
#   [ ] play_sound(name) — e.g. "shoot", "explosion", "pickup"
#   [ ] get_image(name) — e.g. "tank_p1", "wall", "wall_cracked"
#   [ ] background music on/off
#   [ ] missing file → print a warning, don't crash
#
# CONTRACT (see docs/CLASS_CONTRACTS.md)
#   play_sound(name), get_image(name) — tell the team the exact names
#   you support by listing them in the assets/ README files.
# =====================================================================
