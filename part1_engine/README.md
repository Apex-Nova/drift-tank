# Part 1 — ENGINE (Game loop + Tanks)

**You own:** `main.py`, `part1_engine/game.py`, `part1_engine/tank.py`
**You never edit:** anything in `part2_*`, `part3_*`, `part4_*`, `shared/`

You build the hub: the loop that runs the game and the tanks the players drive.
Everyone else's code gets *called* from your loop.

## Study path (do them in order)
1. Python classes refresher (`__init__`, `self`, methods)
2. Pygame window + game loop + events + Clock/FPS
3. `pygame.Rect` and moving it
4. Keyboard input: `get_pressed()` vs `KEYDOWN`
5. Direction vectors (dx, dy) and Pygame's upside-down y axis
6. Rect collisions (to block movement through walls)
7. Timers/cooldowns with `pygame.time.get_ticks()`
8. Game states (menu / playing / game over)
9. Python imports across folders (packages)
10. (Polish) images, `transform.rotate`, delta time

## Milestones
- [ ] **Day 1:** window opens + empty loop → push to GitHub (everyone waits for this!)
- [ ] Phase 1: one tank drives around a walled map
- [ ] Phase 2: tank shoots bullets (with Person 2)
- [ ] Phase 3: two tanks on one keyboard, game ends with a winner (with Person 4)
- [ ] Phase 4: restart, menus wired in, 3–4 players
