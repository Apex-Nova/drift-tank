# Part 2 — COMBAT (Bullets + Collisions + Effects)

**You own:** `part2_combat/bullet.py`, `part2_combat/collisions.py`, `part2_combat/effects.py`
**You never edit:** `main.py`, `part1_*`, `part3_*`, `part4_*`, `shared/`

You make the game *dangerous*: shooting, hitting, damage, and telling the
scoreboard when someone dies.

## Study path (do them in order)
1. Python classes refresher
2. Pygame basics: window, loop, drawing a shape (do the "move a square" exercise)
3. `pygame.Rect` and moving it every frame
4. Direction vectors (dx, dy) × speed — and `pygame.math.Vector2`
5. Lists of many objects + removing dead ones safely
6. `colliderect`, `collidelist`, `collidepoint`
7. Passing objects into functions (references) — changing them inside
8. (Optional) `pygame.sprite.Sprite` / `Group` / `spritecollide`
9. (Polish) lifetimes/timers, particles, alpha transparency

## Milestones
- [ ] A bullet flies across the screen from a fake tank (practice folder)
- [ ] Bullets disappear off-screen; many bullets at once work
- [ ] Bullet hits wall → bullet gone (+ wall damaged if destructible)
- [ ] Bullet hits tank → damage → scoreboard told on a kill
- [ ] Explosion effect
