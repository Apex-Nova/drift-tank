# =====================================================================
#  part2_combat/weapons.py  —  LOOT WEAPONS + PROJECTILES
# =====================================================================
#
# Tanks start with NO weapon. Driving over a loot crate gives a random
# weapon with limited ammo. When the ammo runs out, find the next crate.
#
#   WEAPONS[key]          -> stats for each weapon
#   fire(key, owner_id, muzzle_pos, angle) -> list of new Projectiles
#   Projectile.update(walls) -> moves it, bounces / stops on walls
#   splash_targets(...)   -> who gets hurt by an explosion
# =====================================================================
import math
import random

import pygame
from pygame.math import Vector2

# name      : shown in the HUD / pickup message
# ammo      : shots per crate
# cooldown  : ms between shots
# pellets   : projectiles per shot (scatter gun fires many)
# spread    : random angle (degrees) added to each projectile
# range     : px before the projectile fizzles (or explodes, if it has splash)
# splash    : explosion radius (0 = no explosion)
# bounces   : how many times it bounces off walls
# pierce    : flies through tanks
# accel     : speed added every frame (rockets)
WEAPONS = {
    "machinegun": {
        "name": "Machine Gun", "ammo": 40, "cooldown": 95, "damage": 7, "speed": 8,
        "pellets": 1, "spread": 5, "range": 432, "radius": 3, "splash": 0.0,
        "sprite": "bulletDark1", "sound": "shot_small", "shake": 1, "recoil": 3,
        "color": (255, 214, 92), "rarity": 30,
    },
    "cannon": {
        "name": "Big Cannon", "ammo": 8, "cooldown": 650, "damage": 30, "speed": 6,
        "pellets": 1, "spread": 0, "range": 660, "radius": 5, "splash": 36,
        "sprite": "bulletRed2", "sound": "shot_cannon", "shake": 6, "recoil": 9,
        "color": (255, 110, 80), "rarity": 22,
    },
    "shotgun": {
        "name": "Scatter Gun", "ammo": 7, "cooldown": 720, "damage": 10, "speed": 7,
        "pellets": 7, "spread": 26, "range": 198, "radius": 3, "splash": 0.0,
        "sprite": "bulletSand1", "sound": "shot_shotgun", "shake": 5, "recoil": 8,
        "color": (255, 180, 60), "rarity": 20,
    },
    "rocket": {
        "name": "Rockets", "ammo": 5, "cooldown": 900, "damage": 45, "speed": 2.0,
        "accel": 0.23, "max_speed": 6, "pellets": 1, "spread": 0, "range": 840,
        "radius": 5, "splash": 68, "sprite": "bulletGreen3", "sound": "shot_rocket",
        "shake": 12, "recoil": 6, "trail": True, "color": (120, 255, 120), "rarity": 12,
    },
    "railgun": {
        "name": "Railgun", "ammo": 4, "cooldown": 1100, "damage": 42, "speed": 17,
        "pellets": 1, "spread": 0, "range": 900, "radius": 4, "splash": 0.0, "pierce": True,
        "sprite": "bulletBlue3", "sound": "shot_rail", "shake": 7, "recoil": 10, "beam": True,
        "color": (110, 200, 255), "rarity": 8,
    },
    "bouncer": {
        "name": "Bouncer", "ammo": 12, "cooldown": 340, "damage": 14, "speed": 5,
        "pellets": 1, "spread": 3, "range": 1440, "radius": 4, "splash": 0.0, "bounces": 3,
        "sprite": "bulletBlue1", "sound": "shot_bouncer", "shake": 2, "recoil": 4,
        "color": (190, 140, 255), "rarity": 18,
    },
}
WEAPON_ORDER = ["machinegun", "cannon", "shotgun", "rocket", "railgun", "bouncer"]


def random_weapon(exclude=None):
    """Pick a weapon; rare ones (rocket, railgun) come up less often."""
    keys = [k for k in WEAPON_ORDER if k != exclude]
    weights = [WEAPONS[k]["rarity"] for k in keys]
    return random.choices(keys, weights=weights)[0]


class Projectile:
    """Anything a tank fires. Plain numbers only, so it can be sent over the network."""

    def __init__(self, weapon, owner_id, pos, angle):
        stats = WEAPONS[weapon]
        self.weapon = weapon
        self.owner_id = owner_id
        self.pos = Vector2(pos)
        self.start = Vector2(pos)
        self.angle = angle
        self.speed = stats["speed"]
        self.vel = Vector2(1, 0).rotate(angle) * self.speed
        self.damage = stats["damage"]
        self.radius = stats["radius"]
        self.splash = stats.get("splash", 0)
        self.bounces = stats.get("bounces", 0)
        self.pierce = stats.get("pierce", False)
        self.range = stats["range"] * random.uniform(0.9, 1.1)
        self.traveled = 0.0
        self.alive = True
        self.hit_ids = set()        # tanks already hit (railgun pierces each tank once)

    @property
    def rect(self):
        r = pygame.Rect(0, 0, self.radius * 2, self.radius * 2)
        r.center = (round(self.pos.x), round(self.pos.y))
        return r

    def update(self, walls, bounds):
        """Move one frame. Returns (event, wall) where event is None, 'bounce', 'wall' or 'expired'."""
        stats = WEAPONS[self.weapon]
        if stats.get("accel"):
            self.speed = min(stats["max_speed"], self.speed + stats["accel"])
            self.vel.scale_to_length(self.speed)

        steps = max(1, math.ceil(self.speed / 5))     # small steps so fast shots don't skip walls
        step = self.vel / steps
        for _ in range(steps):
            for axis in (0, 1):
                self.pos[axis] += step[axis]
                wall = _touching_wall(self.rect, walls)
                if wall is None:
                    continue
                if self.bounces > 0:
                    self.pos[axis] -= step[axis]
                    self.vel[axis] = -self.vel[axis]
                    step[axis] = -step[axis]
                    self.bounces -= 1
                    self.angle = Vector2(1, 0).angle_to(self.vel)
                    return "bounce", wall
                self.alive = False
                return "wall", wall
            self.traveled += step.length()

        if self.traveled > self.range or not bounds.collidepoint(self.pos):
            self.alive = False
            return "expired", None
        return None, None


def _touching_wall(rect, walls):
    for wall in walls:
        if wall.alive and wall.blocks_bullets and rect.colliderect(wall.rect):
            return wall
    return None


def fire(weapon, owner_id, muzzle_pos, angle):
    stats = WEAPONS[weapon]
    shots = []
    for _ in range(stats["pellets"]):
        spread = random.uniform(-stats["spread"], stats["spread"]) / (2 if stats["pellets"] == 1 else 1)
        shots.append(Projectile(weapon, owner_id, muzzle_pos, angle + spread))
    return shots


def splash_targets(center, radius, damage, tanks, owner_id, same_team=None):
    """Tanks inside the blast and how much damage each takes (less at the edge)."""
    hits = []
    for tank in tanks:
        if not tank.alive or tank.player_id == owner_id:
            continue
        if same_team is not None and same_team(tank.player_id, owner_id):
            continue
        distance = Vector2(tank.rect.center).distance_to(center)
        if distance < radius + 14:
            falloff = max(0.35, 1 - distance / (radius + 14))
            hits.append((tank, round(damage * falloff)))
    return hits
