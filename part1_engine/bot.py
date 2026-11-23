# =====================================================================
#  part1_engine/bot.py  —  COMPUTER-CONTROLLED TANKS
# =====================================================================
# A bot does exactly what a player does: every frame it returns an
# inputs dictionary ({"move_x", "move_y", "aim_angle", "shoot"}).
# Used for "play vs bots" and for the live battle behind the main menu.
#
# Brain (very simple):
#   no weapon   -> drive to the nearest crate
#   has weapon  -> pick the nearest enemy, keep a nice distance, aim, shoot
#                  when the shot isn't blocked by a wall
#   stuck       -> back off in a random direction for a moment
# =====================================================================
import random

from pygame.math import Vector2


def line_is_clear(a, b, blockers):
    for wall in blockers:
        if wall.alive and wall.blocks_bullets and wall.rect.clipline(a, b):
            return False
    return True


class Bot:
    def __init__(self, player_id, skill=0.7):
        self.player_id = player_id
        self.skill = skill
        self.stuck_frames = 0
        self.escape = None
        self.escape_frames = 0
        self.last_pos = None
        self.wander = Vector2(1, 0).rotate(random.uniform(0, 360))
        self.reaction = 0

    def think(self, game, tank):
        if not tank.alive:
            return {}
        inputs = {"move_x": 0.0, "move_y": 0.0, "aim_angle": None, "shoot": False}
        blockers = game.map.bullet_blockers()

        # unstick
        if self.last_pos is not None and tank.pos.distance_to(self.last_pos) < 0.4:
            self.stuck_frames += 1
        else:
            self.stuck_frames = 0
        self.last_pos = Vector2(tank.pos)
        if self.stuck_frames > 25:
            self.escape = Vector2(1, 0).rotate(random.uniform(0, 360))
            self.escape_frames = 40
            self.stuck_frames = 0
        if self.escape_frames > 0:
            self.escape_frames -= 1
            inputs["move_x"], inputs["move_y"] = self.escape.x, self.escape.y
            return inputs

        enemies = [t for t in game.tanks if t.alive and t is not tank and not game.same_team(t.player_id, tank.player_id)]
        target = min(enemies, key=lambda t: t.pos.distance_to(tank.pos), default=None)
        goal = None

        # Battleground: get back into the safe zone first
        zone = game.zone
        if zone is not None:
            center = Vector2(zone["x"], zone["y"])
            safe_r = min(zone["r"], zone["nr"] if zone.get("shrinking") or zone["timer"] < 8000 else zone["r"])
            if tank.pos.distance_to(center) > max(30, safe_r - 40):
                goal = center
        crates = [c for c in game.loot.crates if zone is None or Vector2(c.pos).distance_to((zone["x"], zone["y"])) < zone["r"]]

        if goal is None and (tank.weapon is None or (tank.health < tank.max_health * 0.4 and any(c.kind == "health" for c in crates))):
            wanted = "health" if tank.weapon is not None else "weapon"
            choices = [c for c in crates if c.kind == wanted] or crates
            if choices:
                goal = min(choices, key=lambda c: c.pos.distance_to(tank.pos)).pos
        # Only fight enemies we could actually see (about one screen away). Before, every armed bot
        # drove straight at the nearest enemy anywhere on the map: everyone met at once and a
        # Battleground match was over in ~30 s. Out of sight, bots loot and roam instead.
        sight = 380 if game.rules == "br" else 700
        if target is not None and target.pos.distance_to(tank.pos) > sight:
            target_in_sight = False
            if goal is None and crates:
                goal = min(crates, key=lambda c: c.pos.distance_to(tank.pos)).pos
            elif goal is None and zone is not None and random.random() < 0.02:
                self.wander = (Vector2(zone["x"], zone["y"]) - tank.pos).normalize() if \
                    Vector2(zone["x"], zone["y"]) != tank.pos else self.wander
        else:
            target_in_sight = target is not None
        if goal is None and target_in_sight:
            to_target = target.pos - tank.pos
            distance = to_target.length()
            if distance > 200:
                goal = target.pos
            elif distance < 100:
                goal = tank.pos - to_target          # back off
            else:                                     # circle-strafe
                goal = tank.pos + to_target.rotate(90 if self.player_id % 2 else -90)
        if goal is None:
            if random.random() < 0.01:
                self.wander = self.wander.rotate(random.uniform(-120, 120))
            goal = tank.pos + self.wander * 100

        direction = Vector2(goal) - tank.pos
        if direction.length() > 6:
            direction = direction.normalize()
            # avoid walls right in front of us
            ahead = tank.pos + direction * 24
            if not game.map.bounds.collidepoint(ahead) or any(b.rect.collidepoint(ahead) for b in game.map.tank_blockers()):
                direction = direction.rotate(70 if self.player_id % 2 else -70)
            inputs["move_x"], inputs["move_y"] = direction.x, direction.y

        if target_in_sight and tank.weapon is not None:
            to_target = target.pos + target.velocity * 10 - tank.pos
            aim = Vector2(1, 0).angle_to(to_target) + random.uniform(-8, 8) * (1 - self.skill)
            inputs["aim_angle"] = aim
            error = abs((aim - tank.barrel_angle + 180) % 360 - 180)
            in_range = to_target.length() < 320
            if error < 10 and in_range and line_is_clear(tank.pos, target.pos, blockers):
                self.reaction += 1
                inputs["shoot"] = self.reaction > 12 * (1.2 - self.skill)
            else:
                self.reaction = 0
        return inputs
