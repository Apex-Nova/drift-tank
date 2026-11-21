# =====================================================================
#  part1_engine/tank.py  —  THE TANK CLASS
#  OWNER: Person 1 (Engine)
# =====================================================================
#
# One Tank object per player. The tank lives in a flat top-down WORLD
# (x, y in pixels); part1_engine/view.py + renderer.py draw it in 3/4 pixel art.
#
# CONTROLS COME IN AS DATA (Lesson 6 — B1):
#   inputs = {"move_x": 0.0, "move_y": -1.0,   # which way to drive (world direction)
#             "barrel_left": False, "barrel_right": False,
#             "aim_angle": None or degrees,     # mouse / phone stick aims directly
#             "shoot": True}
#   The same dictionary works for the keyboard, a bot, a laptop over Wi-Fi
#   or a phone controller.
#
# LOOT RULE: a tank starts with NO weapon. Drive over a loot crate to get
# a random weapon with limited ammo. Ammo 0 = weapon gone, find another crate.
#
# DRIFT: the hull turns toward where you steer at hull_turn_speed, and the
# tank's velocity only slowly follows the hull ("grip"), so it slides.
# =====================================================================
import pygame
from pygame.math import Vector2

from shared.settings import Settings
from part2_combat.collisions import rect_touches_wall
from part2_combat.weapons import WEAPONS, fire


class Tank:
    def __init__(self, start_x, start_y, color, name, speed, player_id, score=0, controls=None):
        self.color = color
        self.name = name
        self.player_id = player_id
        self.score = score
        self.controls = controls or {}
        self.speed = speed or Settings.TANK_SPEED
        self.max_health = Settings.TANK_MAX_HEALTH
        self.health = self.max_health
        self.alive = True

        self.rect = pygame.Rect(0, 0, 22, 22)        # collision box (world pixels)
        self.pos = Vector2(start_x, start_y)          # exact center (floats)
        self.rect.center = self.pos
        self.velocity = Vector2(0, 0)

        self.hull_angle = 0
        self.target_angle = 0
        self.hull_turn_speed = 4
        self.barrel_angle = 0
        self.barrel_speed = 4
        self.aim = Vector2(1, 0)

        self.weapon = None              # key in WEAPONS, or None = unarmed
        self.ammo = 0
        self.last_shot_time = -100000
        self.recoil = 0.0               # turret kicks back when firing (drawing only)
        self.flash_until = 0            # white flash when hit (drawing only)
        self.shield_until = 0           # can't be hurt until this time (after spawning)
        self.respawn_at = 0
        self.last_attacker = None
        self.distance_driven = 0.0      # used to drop track marks
        self.team = 0                   # Team Deathmatch: 0 = red team, 1 = blue team
        self.zone_damage = 0.0          # Battleground: damage from the zone builds up here
        self.is_bot = False

    # ---------------- loot ----------------
    def give_weapon(self, weapon):
        self.weapon = weapon
        self.ammo = WEAPONS[weapon]["ammo"]

    def heal(self, amount):
        self.health = min(self.max_health, self.health + amount)

    # ---------------- shooting ----------------
    def can_shoot(self, now):
        if self.weapon is None:
            return False
        return now - self.last_shot_time >= WEAPONS[self.weapon]["cooldown"]

    def shoot(self, now=None):
        """Returns a list of new Projectiles (empty if no weapon / cooling down)."""
        now = pygame.time.get_ticks() if now is None else now
        if not self.alive or not self.can_shoot(now):
            return []
        self.last_shot_time = now
        weapon = self.weapon
        muzzle = self.pos + self.aim * 18
        shots = fire(weapon, self.player_id, muzzle, self.barrel_angle)
        self.ammo -= 1
        self.recoil = WEAPONS[weapon]["recoil"]
        self.velocity -= self.aim * WEAPONS[weapon]["recoil"] * 0.15     # a little knock-back
        if self.ammo <= 0:
            self.weapon = None
            self.ammo = 0
        return shots

    # ---------------- health ----------------
    def take_damage(self, amount, now=None, attacker=None):
        """Returns True if this hit destroyed the tank."""
        now = pygame.time.get_ticks() if now is None else now
        if not self.alive or now < self.shield_until:
            return False
        self.health -= amount
        self.flash_until = now + 90
        if attacker is not None:
            self.last_attacker = attacker
        if self.health <= 0:
            self.health = 0
            self.alive = False
            self.weapon = None
            self.ammo = 0
            self.respawn_at = now + Settings.RESPAWN_MS
            return True
        return False

    def respawn(self, x, y, now):
        self.pos = Vector2(x, y)
        self.rect.center = self.pos
        self.velocity = Vector2(0, 0)
        self.health = self.max_health
        self.alive = True
        self.weapon = None
        self.ammo = 0
        self.shield_until = now + Settings.SPAWN_SHIELD_MS
        self.last_attacker = None

    # ---------------- movement ----------------
    def move(self, inputs, walls, bounds=None, on_ice=False):
        # 1. which way does the player want to go? (already a WORLD direction)
        arrow = Vector2(inputs.get("move_x", 0.0), inputs.get("move_y", 0.0))
        if arrow.length() > 1:
            arrow = arrow.normalize()

        # 2. barrel: aim straight at a point (mouse/phone) or turn with keys
        aim_angle = inputs.get("aim_angle")
        if aim_angle is not None:
            difference = (aim_angle - self.barrel_angle + 180) % 360 - 180
            step = 9
            self.barrel_angle += max(-step, min(step, difference))
        else:
            if inputs.get("barrel_left"):
                self.barrel_angle -= self.barrel_speed
            if inputs.get("barrel_right"):
                self.barrel_angle += self.barrel_speed
        self.barrel_angle %= 360
        self.aim = Vector2(1, 0).rotate(self.barrel_angle)

        # 3. hull turns toward the steering direction (the shortest way round)
        if arrow.length() > 0.2:
            self.target_angle = Vector2(1, 0).angle_to(arrow)
        difference = (self.target_angle - self.hull_angle + 180) % 360 - 180
        if abs(difference) <= self.hull_turn_speed:
            self.hull_angle = self.target_angle
        elif difference > 0:
            self.hull_angle += self.hull_turn_speed
        else:
            self.hull_angle -= self.hull_turn_speed
        self.hull_angle %= 360

        # 4. DRIFT: velocity slowly catches up with where the hull points
        drive = Vector2(0, 0)
        if arrow.length() > 0.2:
            drive = Vector2(1, 0).rotate(self.hull_angle) * self.speed * min(1.0, arrow.length())
        grip = Settings.ICE_GRIP if on_ice else Settings.TANK_GRIP
        self.velocity += (drive - self.velocity) * grip

        # 5. move X and Y separately so the tank slides along walls
        for axis in (0, 1):
            self.pos[axis] += self.velocity[axis]
            self.rect.center = (round(self.pos.x), round(self.pos.y))
            if rect_touches_wall(self.rect, walls):
                self.pos[axis] -= self.velocity[axis]
                self.velocity[axis] *= -0.25          # small bounce off the wall
                self.rect.center = (round(self.pos.x), round(self.pos.y))
        self.distance_driven += self.velocity.length()

        # 6. stay inside the map
        if bounds is not None:
            clamped = self.rect.clamp(bounds)
            if clamped != self.rect:
                self.rect = clamped
                self.pos = Vector2(self.rect.center)
                self.velocity *= 0.3

        if self.recoil > 0:
            self.recoil = max(0.0, self.recoil - 0.8)

    def is_drifting(self):
        """Sliding sideways? (used for track marks / dust)."""
        if self.velocity.length() < 1.2:
            return False
        facing = Vector2(1, 0).rotate(self.hull_angle)
        return abs(facing.cross(self.velocity.normalize())) > 0.35
