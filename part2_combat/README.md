# Part 2 — Combat

This package implements bullets, bullet collisions, and a small expanding
explosion effect. It uses the interfaces in `docs/CLASS_CONTRACTS.md`.

## Files

- `bullet.py`: `Bullet` stores a rectangle, owner, direction, speed, damage, and
  alive state. `update()` moves it and retires it beyond screen bounds.
- `collisions.py`: wall and tank hit handling plus `rect_touches_wall()` for
  movement code. Call `resolve_collisions()` after updating bullets.
- `effects.py`: short-lived `Explosion` visual and list update/draw helpers.

## Bullet constructor contract

`Bullet(x, y, direction, owner, damage=None, speed=None, size=None)`

`x, y` are the bullet rectangle's top-left coordinates. `direction` is a pair
such as `(1, 0)` for right. Optional combat settings use `shared.settings` if
present; defaults are bullet size 10, speed 7, damage 1, and an 800 x 600 screen.
Agree with the Tank owner to use this constructor in `Tank.shoot()` and record
the agreed signature in `docs/CLASS_CONTRACTS.md`.

## Game-loop integration

The game loop should update every bullet, resolve collisions, remove dead
bullets without mutating the list during iteration, then draw surviving bullets.
For example, the loop's structure is:

```python
for bullet in bullets:
    bullet.update()
resolve_collisions(bullets, walls, tanks, scoreboard)
bullets = [bullet for bullet in bullets if bullet.alive]
for bullet in bullets:
    bullet.draw(screen)
```

If effects are enabled, keep an `effects` list; append the value returned by
`spawn_explosion(x, y)`, then call `update_effects(effects)` and
`draw_effects(screen, effects)` each frame. Add explosions at hit/death sites
only after the game-loop owner agrees on where that event should be triggered.

## Dependencies

The project needs Pygame (`pip install -r requirements.txt`). Walls must expose
`rect`, `alive`, `destructible`, and `hit(damage)`. Tanks must expose `rect`,
`alive`, and `take_damage(amount)`. The scoreboard must expose
`register_kill(killer, victim)`. Call wall collision handling before tank
collision handling so walls shield tanks behind them.
