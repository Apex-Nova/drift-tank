# Part 3 — WORLD (Arena + Walls + Power-ups)

**You own:** `part3_world/wall.py`, `part3_world/arena.py`, `part3_world/powerup.py`, `part3_world/maps/`
**You never edit:** `main.py`, `part1_*`, `part2_*`, `part4_*`, `shared/`

You build the battlefield: the map, the walls (some breakable), and the
power-ups that make matches interesting.

## Study path (do them in order)
1. Python classes refresher
2. Pygame basics: window, loop, drawing (do the "move a square" exercise)
3. `pygame.draw.rect`, colors, `pygame.Rect`
4. 2D lists, nested loops, `enumerate`
5. Grid ↔ pixel coordinates
6. Reading text files + file paths with `pathlib`
7. Images: `image.load`, `convert_alpha`, `blit`
8. Timers with `get_ticks()` + the `random` module

## Milestones
- [ ] A hardcoded grid draws as walls on screen
- [ ] Destructible walls look different and break with `hit()`
- [ ] Map loads from `maps/level1.txt`; spawn points returned
- [ ] Power-ups spawn, get picked up, and wear off
- [ ] 2–3 maps
