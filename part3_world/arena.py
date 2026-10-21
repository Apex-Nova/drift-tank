# =====================================================================
#  part3_world/arena.py  —  BUILDS THE MAP (LEVEL) FROM A GRID
#  OWNER: Person 3 (World)           WHEN: Phase 1 → Phase 4
# =====================================================================
#
# WHAT THIS FILE IS
#   Turns a text "picture" of the map into real Wall objects and player
#   spawn points. Example idea of a grid (one character = one tile):
#       ##########
#       #1.....+.#
#       #..##....#
#       #.+...2..#
#       ##########
#   The exact symbols are YOUR choice — document them in maps/README.md.
#
# TOPICS TO STUDY (in this order)
#   1. 2D lists / a list of strings, and indexing grid[row][col]
#   2. Nested loops with enumerate() — getting row number AND column number
#   3. Grid → pixels: pixel_x = col * TILE_SIZE (and the same for y).
#      Why rows map to y and columns map to x (a classic mix-up!)
#   4. Reading a text file: open(), "with", reading lines, .strip()
#   5. File paths that work no matter which folder the game is run from
#      (look up __file__ and pathlib.Path)
#   6. Returning more than one value from a function (tuples)
#
# WHAT TO BUILD — step by step
#   [ ] Start with the grid written directly in the code as a list of strings
#   [ ] Loop over it → make a Wall for every wall symbol
#   [ ] Remember the spawn points ('1', '2', ...) as pixel positions
#   [ ] Return the walls AND the spawn points
#   [ ] Make sure the grid size × TILE_SIZE matches the screen size
#   [ ] Then move the grid into maps/level1.txt and load it from the file
#   [ ] Draw a floor/background (plain color or grid lines, image later)
#   [ ] (Phase 4) 2–3 different maps to choose from
#
# CONTRACT (see docs/CLASS_CONTRACTS.md)
#   build_arena(map_name) → (list of walls, list of spawn points)
#   Person 1 calls this once at the start of every match.
# =====================================================================
