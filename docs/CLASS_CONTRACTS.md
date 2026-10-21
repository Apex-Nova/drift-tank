# Class Contracts — the shapes everyone agrees on

These are **promises**, not code. Each owner builds their class so it has exactly
these names. Then anyone can use `tank.rect` or `wall.hit()` without waiting for
the other person's code — test with a fake object that has the same names.

**Changing a contract?** Talk to the people it affects first, then update this file
in your PR. Never silently rename something on this list.

> Names marked `?` are not decided yet — the owners decide and fill them in.

---

## shared/settings.py — Person 4
Plain constants: `SCREEN_WIDTH`, `SCREEN_HEIGHT`, `FPS`, `TILE_SIZE`, colors,
`TANK_SPEED`, `TANK_MAX_HEALTH`, `SHOOT_COOLDOWN_MS`, `BULLET_SPEED`, `BULLET_DAMAGE`,
`WALL_HEALTH`, power-up timings, `MATCH_TIME`, and `PLAYER_CONTROLS` (keys for P1–P4).

## Tank — Person 1 (`part1_engine/tank.py`)
| Name | What it is |
|---|---|
| `rect` | `pygame.Rect` — position + size |
| `player_id` | 1, 2, 3 or 4 |
| `color` | (R, G, B) |
| `health` | int, starts at `TANK_MAX_HEALTH` |
| `direction` | facing, as (dx, dy) e.g. (0, -1) = up |
| `alive` | bool |
| `update(keys, walls)` ? | read keys, move, stay out of walls |
| `shoot()` | returns a `Bullet` or `None` (cooldown) |
| `take_damage(amount)` | lowers health, sets `alive = False` at 0 |
| `draw(screen)` | draws itself |
| power-up fields ? | e.g. speed multiplier, shield, cooldown — agree with Person 3 |

## Bullet — Person 2 (`part2_combat/bullet.py`)
| Name | What it is |
|---|---|
| `rect` | `pygame.Rect` |
| `owner` | the Tank that fired it |
| `direction` | (dx, dy) |
| `damage` | int |
| `alive` | bool |
| `Bullet(...)` constructor args ? | agree with Person 1 |
| `update()` | move one step; dies off-screen |
| `draw(screen)` | draws itself |

## collisions — Person 2 (`part2_combat/collisions.py`)
| Name ? | What it does |
|---|---|
| bullets vs walls | kill bullet, call `wall.hit()` on destructible walls |
| bullets vs tanks | skip owner, `take_damage`, report kills to scoreboard |
| rect touches any wall | `True`/`False` — used by Tank movement |

## Wall — Person 3 (`part3_world/wall.py`)
| Name | What it is |
|---|---|
| `rect` | `pygame.Rect` |
| `destructible` | bool |
| `alive` | bool |
| `hit(damage)` | only breakable walls lose health |
| `draw(screen)` | draws itself |

## Arena — Person 3 (`part3_world/arena.py`)
`build_arena(map_name)` → `(walls, spawn_points)`

## PowerUpManager — Person 3 (`part3_world/powerup.py`)
`update(tanks, walls)`, `draw(screen)`, `reset()` ?

## Scoreboard — Person 4 (`part4_ui/scoreboard.py`)
`register_kill(killer, victim)`, `is_game_over(tanks)`, `winner()`, `time_left()`, `reset()`

## HUD / Menu / Assets — Person 4 (`part4_ui/`)
`draw_hud(screen, tanks, scoreboard)` · menu draw + event functions returning an action ? ·
`play_sound(name)`, `get_image(name)`
