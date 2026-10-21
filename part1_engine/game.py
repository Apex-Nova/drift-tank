# =====================================================================
#  part1_engine/game.py  —  THE GAME LOOP (the heart / the "hub")
#  OWNER: Person 1 (Engine)          WHEN: Phase 0 → Phase 4
# =====================================================================
#
# WHAT THIS FILE IS
#   The loop that runs ~60 times per second for the whole game.
#   It OWNS the lists of everything alive (tanks, bullets, walls,
#   power-ups) and, every frame, CALLS everyone else's code in order.
#   It does NOT contain bullet / wall / menu logic itself — it only
#   calls the functions the other 3 people write (see docs/CLASS_CONTRACTS.md).
#
# TOPICS TO STUDY (in this order)
#   1. The game loop idea: handle input → update → draw → repeat
#   2. pygame.init(), pygame.display.set_mode(), the "screen" Surface
#   3. The event queue: pygame.event.get(), event.type, QUIT, KEYDOWN
#   4. Drawing a frame: screen.fill(...) then pygame.display.flip()
#   5. pygame.time.Clock and clock.tick(FPS) — why games cap the frame rate
#   6. Classes: putting the loop inside a Game class (self.screen, self.running)
#   7. Game STATES: a variable like "menu" / "playing" / "game_over" that
#      decides what the loop does this frame
#   8. (later) delta time — moving by speed * time instead of per frame
#
# WHAT TO BUILD — step by step
#   PHASE 0  (push this on Day 1 so everyone can branch off it!)
#   [ ] A window opens with the size from shared/settings.py
#   [ ] It fills with a background color every frame
#   [ ] Clicking the window's X closes the game cleanly
#   [ ] Runs at a steady FPS using a Clock
#
#   PHASE 1
#   [ ] Create one Tank (from part1_engine/tank.py); update + draw it every frame
#   [ ] Ask Person 3's arena for the walls and draw them
#       (until their code is merged: use a small list of fake pygame.Rects)
#
#   PHASE 2
#   [ ] Keep a list of bullets. When a tank's shoot() gives back a bullet,
#       add it to the list
#   [ ] Every frame: update bullets, call Person 2's collision functions,
#       then remove bullets that are no longer alive
#
#   PHASE 3
#   [ ] Two tanks, each with its own key scheme from settings
#   [ ] Ask Person 4's scoreboard if the game is over → switch state
#
#   PHASE 4
#   [ ] Use Person 4's menu for the "menu" and "game_over" states
#   [ ] A reset/restart function that rebuilds everything fresh
#   [ ] 3rd / 4th player support
#   [ ] Call Person 3's power-up manager every frame
#
# THE ORDER INSIDE ONE FRAME (getting this wrong causes weird bugs)
#   events → update tanks → update bullets → collisions → power-ups
#   → check game over → draw arena → draw tanks/bullets/power-ups
#   → draw HUD → flip → tick
#   (Think about WHY drawing happens after all updating.)
#
# WHAT YOU USE FROM OTHERS (only through the contracts)
#   Person 2: Bullet, collision functions
#   Person 3: build_arena(), Wall.draw(), PowerUpManager
#   Person 4: settings, menu, HUD, scoreboard, sounds
#
# DON'T
#   - Don't write bullet/wall/menu logic here. If you need it, ask the owner.
#   - Don't edit other people's files. Use a fake/placeholder until theirs lands.
# =====================================================================
