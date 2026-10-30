"""Combat package: bullets, collision handling, and visual effects."""

from .bullet import Bullet
from .collisions import (
    handle_bullet_tank_collisions,
    handle_bullet_wall_collisions,
    rect_touches_wall,
    resolve_collisions,
)
from .effects import Explosion, draw_effects, spawn_explosion, update_effects

__all__ = [
    "Bullet",
    "Explosion",
    "draw_effects",
    "handle_bullet_tank_collisions",
    "handle_bullet_wall_collisions",
    "rect_touches_wall",
    "resolve_collisions",
    "spawn_explosion",
    "update_effects",
]
