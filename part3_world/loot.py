# =====================================================================
#  part3_world/loot.py  —  LOOT CRATES THAT DROP FROM THE SKY
# =====================================================================
#
# Every few seconds a crate falls onto the map (up to MAX_CRATES).
#   "weapon"  mystery crate (?)   -> random weapon, full ammo
#   "weapon"  marked crate        -> you can SEE which weapon is inside
#   "health"  green cross         -> +60 health
# A crate can only be picked up after it has landed.
# =====================================================================
import random

import pygame
from pygame.math import Vector2

from shared.settings import Settings
from part2_combat.weapons import WEAPONS, random_weapon

FALL_MS = 750


class LootCrate:
    def __init__(self, crate_id, pos, kind, weapon, spawned_at):
        self.id = crate_id
        self.pos = Vector2(pos)
        self.kind = kind            # "weapon" or "health"
        self.weapon = weapon        # set = everyone can see what's inside; None = mystery
        self.spawned_at = spawned_at
        self.rect = pygame.Rect(0, 0, 22, 22)
        self.rect.center = self.pos

    def landed(self, now):
        return now - self.spawned_at >= FALL_MS

    def to_state(self):
        return {"id": self.id, "x": round(self.pos.x), "y": round(self.pos.y), "k": self.kind,
                "w": self.weapon, "t": self.spawned_at}


class LootManager:
    def __init__(self, game_map, now):
        self.map = game_map
        self.crates = []
        self.next_id = 1
        self.next_spawn = now + 600
        self.first_wave = 6          # drop a few right away so nobody waits long
        self.zone_center = None      # Battleground: only drop crates inside the safe zone
        self.zone_radius = 0

    def reset(self, now):
        self.crates = []
        self.next_spawn = now + 600
        self.first_wave = 6

    def _spot(self, tanks):
        spots = list(self.map.loot_spots)
        random.shuffle(spots)
        extra = [self.map.random_free_point(near=self.zone_center, radius=self.zone_radius) if self.zone_radius
                 else self.map.random_free_point() for _ in range(10)]
        if self.zone_radius:
            spots = [s for s in spots if s.distance_to(self.zone_center) < self.zone_radius - 20]
        for spot in spots + extra:
            if any(c.pos.distance_to(spot) < 50 for c in self.crates):
                continue
            if any(t.alive and t.pos.distance_to(spot) < 60 for t in tanks):
                continue
            return spot
        return None

    def update(self, now, tanks):
        """Drop new crates, let tanks pick them up. Returns a list of events (dicts)."""
        events = []
        if now >= self.next_spawn and len(self.crates) < Settings.MAX_CRATES:
            spot = self._spot(tanks)
            if spot is not None:
                hurt = any(t.alive and t.health < t.max_health * 0.6 for t in tanks)
                kind = "health" if hurt and random.random() < 0.3 else "weapon"
                weapon = random_weapon() if kind == "weapon" and random.random() < 0.3 else None
                self.crates.append(LootCrate(self.next_id, spot, kind, weapon, now))
                self.next_id += 1
            if self.first_wave > 1:
                self.first_wave -= 1
                self.next_spawn = now + 250
            else:
                self.first_wave = 0
                self.next_spawn = now + Settings.CRATE_SPAWN_MS + random.randint(-800, 800)

        for crate in list(self.crates):
            if not crate.landed(now):
                continue
            for tank in tanks:
                if not tank.alive or not tank.rect.colliderect(crate.rect):
                    continue
                if crate.kind == "health":
                    if tank.health >= tank.max_health:
                        continue
                    tank.heal(Settings.HEALTH_CRATE_HEAL)
                    events.append({"t": "heal", "id": tank.player_id, "x": crate.pos.x, "y": crate.pos.y,
                                   "text": "+" + str(Settings.HEALTH_CRATE_HEAL) + " HP"})
                else:
                    weapon = crate.weapon or random_weapon(exclude=tank.weapon)
                    tank.give_weapon(weapon)
                    events.append({"t": "pick", "id": tank.player_id, "x": crate.pos.x, "y": crate.pos.y,
                                   "w": weapon, "text": WEAPONS[weapon]["name"].upper() + "!"})
                self.crates.remove(crate)
                break
        return events

    def landing_events(self, now, last_now):
        """Crates that touched the ground since the last frame (for dust + sound)."""
        return [{"t": "drop", "x": c.pos.x, "y": c.pos.y} for c in self.crates
                if last_now < c.spawned_at + FALL_MS <= now]

    def to_state(self):
        return [c.to_state() for c in self.crates]
