"""Combat package: bullets, collision handling, and visual effects."""

from .bullet import Bullet
from .collisions import bullets_vs_walls, bullets_vs_tanks, rect_touches_wall
from .effects import Explosion, EffectManager

__all__ = [
    "Bullet",
    "bullets_vs_walls",
    "bullets_vs_tanks",
    "rect_touches_wall",
    "Explosion",
    "EffectManager",
]
