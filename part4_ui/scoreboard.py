# =====================================================================
#  part4_ui/scoreboard.py  —  KILLS, MATCH END, WINNER
#  OWNER: Person 4 (UI)              WHEN: Phase 3
# =====================================================================
#
# WHAT THIS FILE IS
#   One class, Scoreboard. It remembers who killed whom, keeps the match
#   clock, and answers two questions for the game loop:
#     "Is the match over?"  and  "Who won?"
#
# TOPICS TO STUDY (in this order)
#   1. Classes again (this one has no drawing at all — pure logic!)
#   2. Dictionaries: player_id → kills
#   3. Win conditions: only one tank alive, OR time is up → most kills
#   4. Ties: what if two players have the same kills? Decide a rule.
#   5. Time with pygame.time.get_ticks()
#   6. reset() — so a new match can start without restarting the program
#
# WHAT TO BUILD — step by step
#   [ ] register_kill(killer, victim) — Person 2 calls this
#   [ ] is_game_over(tanks) → True/False — Person 1 calls this each frame
#   [ ] winner() → the winning player (or a "draw" result)
#   [ ] time_left() for the HUD
#   [ ] reset()
#
# CONTRACT (see docs/CLASS_CONTRACTS.md)
#   register_kill(), is_game_over(), winner(), time_left(), reset()
#
# HOW TO TEST ALONE
#   This file needs NO window at all. In practice/<your-name>/, make fake
#   players, call register_kill a few times, and print the results.
# =====================================================================




import pygame
from shared.settings import MATCH_TIME


class Scoreboard:
    def __init__(self):
        self.kills = {1: 0, 2: 0, 3: 0, 4: 0}
        self.start_time = pygame.time.get_ticks()

    def register_kill(self, killer, victim):
        player_id = killer.player_id
        self.kills[player_id] += 1

    def is_game_over(self, tanks):
        alive_count = 0
        for tank in tanks:
            if tank.alive:
                alive_count += 1
        return alive_count <= 1 or self.time_left() == 0
    def winner(self):
        highest_kills = max(self.kills.values())
        for player_id, kills in self.kills.items():
            if kills == highest_kills:
                return player_id
    def time_left(self):
        elapsed_ms = pygame.time.get_ticks() - self.start_time
        elapsed_seconds = elapsed_ms // 1000
        return max(0, MATCH_TIME - elapsed_seconds)
    def reset(self):
        self.kills = {1: 0, 2: 0, 3: 0, 4: 0}
        self.start_time = pygame.time.get_ticks()