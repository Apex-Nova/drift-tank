# =====================================================================
#  main.py  —  THE START BUTTON OF THE GAME
#  OWNER: Person 1 (Engine)
# =====================================================================
#
# Drift Tank: an isometric 2.5D loot battle in Python + Pygame.
# This file only starts the App (part1_engine/app.py).
#
# HOW TO RUN (from the project root folder)
#   python main.py                 -> main menu
#   python main.py local           -> straight to map select (one keyboard)
#   python main.py host            -> straight to map select (host online)
#   python main.py join <host IP>  -> join a game hosted on the same Wi-Fi
#   Phones: open  http://<host IP>:8080  while someone is hosting.
# =====================================================================
import sys


class Main:
    def __init__(self):
        from part1_engine.app import App
        mode = sys.argv[1] if len(sys.argv) > 1 else None
        host_ip = sys.argv[2] if len(sys.argv) > 2 else None
        if mode not in (None, "local", "host", "join") or (mode == "join" and not host_ip):
            print("Usage: python main.py [local | host | join <host IP>]")
            return
        App(mode, host_ip).run()


if __name__ == "__main__":
    Main()  # Start the game when this file is run directly
