# =====================================================================
#  main.py  —  THE START BUTTON OF THE GAME
#  OWNER: Person 1 (Engine)          WHEN: Phase 0 (Day 1)
# =====================================================================
#
# WHAT WE ARE MAKING
#   Drift Tank: a 2–4 player, same-keyboard tank battle in Python + Pygame.
#
# WHAT THIS FILE IS FOR
#   This is the ONE file everybody runs:      python main.py
#   It must stay TINY. Its only job is to start the game that lives in
#   part1_engine/game.py. All real logic lives inside the part folders.
#
# TOPICS TO STUDY FIRST
#   - How Python imports work: importing a class/function from a module
#     that sits inside a folder (a "package" = folder with __init__.py)
#   - What   if __name__ == "__main__":   means and why programs use it
#
# WHAT TO DO
#   [ ] Import your Game class (or a run function) from part1_engine.game
#   [ ] Under the __name__ guard: create the game and start it
#   [ ] Stop there. If this file grows past ~10 lines, that code belongs
#       somewhere else.
#
# HOW TO KNOW IT WORKS
#   From the project root folder, `python main.py` opens the game window.
#   (If you get "ModuleNotFoundError", you are probably running it from
#    the wrong folder — study how Python decides where to look for imports.)
# =====================================================================


class Main:
    def __init__(self):
        from part1_engine.game import Game
        game = Game()
        game.run()

Main()  # Start the game when this file is run directly