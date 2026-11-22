# =====================================================================
#  part1_engine/game.py  —  ONE MATCH OF DRIFT TANK
#  OWNER: Person 1 (Engine)
# =====================================================================
#
# WHERE THE GAME RUNS (mode)
#   "local" : 1-2 players on one keyboard + the number of bots you chose
#   "host"  : this computer runs the match; laptops + phones join over Wi-Fi
#   "join"  : this laptop only sends its inputs and draws the host's state
#   "demo"  : bots fighting behind the main menu
#
# RULES
#   "br"  BATTLEGROUND: one life each, a safe zone shrinks every ~minute,
#         outside it you lose health. Last tank standing wins.
#   "tdm" TEAM DEATHMATCH: red team (P1, P3) vs blue team (P2, P4),
#         you respawn, first team to KILL_LIMIT kills wins.
#
# EVERY FRAME (step):
#   1. collect inputs   (keyboard / mouse / network / phones / bots)
#   2. update()         the rules — only on local/host/demo  (Lesson 6 - B2)
#   3. send / apply     get_state() -> clients, apply_state() on clients
#   4. draw()           renderer.py + HUD
# =====================================================================
import math
import random

import pygame
from pygame.math import Vector2

from shared.settings import Settings, MATCH_TIME
from part1_engine.view import Camera
from part1_engine.tank import Tank
from part1_engine.bot import Bot
from part1_engine.network import Host, Client, get_lan_ip
from part1_engine.touch import TouchControls
from part1_engine.webnet import WebHost
from shared import web
from part1_engine import renderer
from part2_combat.weapons import WEAPONS, WEAPON_ORDER, splash_targets
from part2_combat.fx import FX
from part3_world.maps import GameMap, MAP_IDS, WORLD_W, WORLD_H
from part3_world.loot import LootManager, LootCrate
from part4_ui.scoreboard import Scoreboard
from part4_ui import game_hud, art
from part4_ui.assets import play_sound

COUNTDOWN_MS = 3000
NEVER = 10 ** 12

# One player per computer, so every action gets the comfy keys:
#   drive  = WASD or ARROWS      barrel = Q/E or J/K (or just aim with the MOUSE)
#   fire   = SPACE (or left mouse button)
KEYS = {"up": [pygame.K_w, pygame.K_UP], "down": [pygame.K_s, pygame.K_DOWN],
        "left": [pygame.K_a, pygame.K_LEFT], "right": [pygame.K_d, pygame.K_RIGHT],
        "barrel_left": [pygame.K_q, pygame.K_j], "barrel_right": [pygame.K_e, pygame.K_k],
        "shoot": [pygame.K_SPACE]}
BARREL_KEYS = (pygame.K_q, pygame.K_e, pygame.K_j, pygame.K_k)


def team_of(player_id):
    return 0 if player_id in (1, 3) else 1


class ProjectileView:
    """What a client knows about a bullet: just enough to draw it."""
    __slots__ = ("weapon", "pos", "angle")

    def __init__(self, weapon, x, y, angle):
        self.weapon, self.pos, self.angle = weapon, Vector2(x, y), angle


class Game:
    def __init__(self, mode="local", host_ip=None, map_id=None, bots=0, name="", prefs=None,
                 rules="br", humans=1, seed=None, network=None, online=False):
        self.mode = mode
        self.rules = rules
        self.running = True
        self.result = None
        self.prefs = prefs or {}
        self.network = None
        self.my_id = 1
        self.paused = False
        self.mouse_active = False
        self.mouse_pos = (0, 0)
        self.mouse_down = False
        self.touch = TouchControls()        # on-screen sticks for phones / tablets
        self.fx = FX()
        self.events = []
        self.killfeed = []
        self.announcement = None
        self.names = {}
        self.deaths = {1: 0, 2: 0, 3: 0, 4: 0}
        self.winner = None
        self.win_team = None
        self.phase = "countdown"
        self.phase_started = pygame.time.get_ticks()
        self.now = self.phase_started
        self.frame = 0
        self.track_marks = {}
        self.silent = mode == "demo"
        self.ready = False                 # joiner: pressed READY in the waiting room
        self.lobby = []                    # joiner: waiting-room list sent by the host
        self.zone = None
        self.zone_plan = []
        self.match_start = self.now
        self.humans = []
        self.spectate_id = None
        self.time_left = MATCH_TIME

        if mode == "join":
            # the phone/web version connects first (WebClient) and hands us the connection
            if network is not None:
                self.network = network
            elif web.is_room_code(host_ip or ""):      # 5-digit code = online room
                from part1_engine.relaynet import RelayClient
                self.network = RelayClient(host_ip, name)
            else:
                self.network = Client(host_ip, name)
            self.my_id = self.network.player_id
            map_id = self.network.map_id
            seed = self.network.seed
            self.rules = self.network.rules or rules
        self.load_map(map_id or random.choice(MAP_IDS), seed)
        self.camera = Camera(self.map.bounds)

        self.tanks = []
        self.bots = {}
        self.projectiles = []
        self.scoreboard = Scoreboard()
        self.loot = LootManager(self.map, self.now)
        bots = max(0, bots)
        if mode == "local":
            humans = 1                      # one player per computer (no keyboard sharing)
            self.humans = [1]
            for player_id in self.humans:
                self.add_player(player_id, "P%d" % player_id)
            for player_id in range(humans + 1, min(4, humans + bots) + 1):
                self.add_bot(player_id)
        elif mode == "host":
            self.humans = [1]
            self.add_player(1, name or "HOST")
            bot_ids = list(range(2, min(4, 1 + bots) + 1))
            for player_id in bot_ids:
                self.add_bot(player_id)
            if web.IS_WEB:      # Android app: the native plugin opens the ports
                # online=True: internet room (relay). The website can only do that (no ports).
                self.network = WebHost(self.map.id, self.rules, reserved=set(bot_ids), seed=self.map.seed,
                                       online=online or not web.can_host())
            elif online:          # Mac / Windows: internet room through the relay
                from part1_engine.relaynet import RelayHost
                self.network = RelayHost(self.map.id, self.rules, reserved=set(bot_ids), seed=self.map.seed)
            else:
                self.network = Host(self.map.id, self.rules, reserved=set(bot_ids), seed=self.map.seed)
        elif mode == "demo":
            self.rules = "tdm"
            for player_id in range(1, 5):
                self.add_bot(player_id, skill=0.85)
            self.phase = "playing"
        self.player1 = self.tanks[0] if self.tanks else None
        if mode != "join":
            self.start_match(keep_phase=(mode == "demo"), new_map=False)
        if mode == "host":
            self.phase = "lobby"           # wait in the waiting room until the host presses START
        self.update_camera(instant=True)

    # ------------------------------------------------------------------
    #  setup
    # ------------------------------------------------------------------
    def load_map(self, map_id, seed=None):
        self.map = GameMap(map_id, seed)
        self.map.bake()
        self.fx.set_ground(self.map.ground)
        self.track_marks = {}
        if hasattr(self, "camera"):
            self.camera = Camera(self.map.bounds)

    def add_player(self, player_id, name):
        spawn = self.map.spawn_point(player_id)
        tank = Tank(spawn.x, spawn.y, art.tank_color(player_id, self.rules == "tdm"), name,
                    speed=Settings.TANK_SPEED, player_id=player_id)
        tank.team = team_of(player_id)
        tank.hull_angle = tank.target_angle = tank.barrel_angle = Vector2(1, 0).angle_to(Vector2(self.map.bounds.center) - spawn)
        tank.shield_until = self.now + Settings.SPAWN_SHIELD_MS
        self.tanks.append(tank)
        self.names[player_id] = name
        return tank

    def add_bot(self, player_id, skill=0.75):
        tank = self.add_player(player_id, "BOT %d" % player_id)
        tank.is_bot = True
        self.bots[player_id] = Bot(player_id, skill)
        return tank

    def find_tank(self, player_id):
        for tank in self.tanks:
            if tank.player_id == player_id:
                return tank
        return None

    def start_match(self, keep_phase=False, map_id=None, new_map=True):
        """(Re)start: a freshly generated map, everyone at their spawn, unarmed."""
        if new_map:
            self.load_map(map_id or self.map.id)
        if self.network is not None and self.mode == "host":
            self.network.map_id = self.map.id
            self.network.seed = self.map.seed
        self.now = pygame.time.get_ticks()
        self.projectiles = []
        self.loot = LootManager(self.map, self.now)
        self.scoreboard.reset()
        self.deaths = {1: 0, 2: 0, 3: 0, 4: 0}
        self.killfeed = []
        self.winner = None
        self.win_team = None
        self.spectate_id = None
        for tank in self.tanks:
            spawn = self.map.spawn_point(tank.player_id)
            tank.respawn(spawn.x, spawn.y, self.now)
            tank.zone_damage = 0.0
            tank.hull_angle = tank.target_angle = tank.barrel_angle = Vector2(1, 0).angle_to(Vector2(self.map.bounds.center) - spawn)
        self.match_start = self.now + (0 if keep_phase else COUNTDOWN_MS)
        self.plan_zone()
        if not keep_phase:
            self.phase = "countdown"
            self.phase_started = self.now
        self.update_camera(instant=True)

    # ------------------------------------------------------------------
    #  Battleground zone
    # ------------------------------------------------------------------
    def plan_zone(self):
        self.zone_plan = []
        self.zone = None
        if self.rules != "br":
            return
        c = Vector2(WORLD_W / 2, WORLD_H / 2)
        r = math.hypot(WORLD_W, WORLD_H) / 2 + 20
        t = 0
        for wait, shrink, new_r, dps in Settings.ZONE_STAGES:
            nc = Vector2(c)
            if new_r > 0:
                room = max(0.0, (r - new_r) * 0.45)
                nc = c + Vector2(random.uniform(0, room), 0).rotate(random.uniform(0, 360))
                nc.x = max(new_r * 0.5 + 64, min(WORLD_W - new_r * 0.5 - 64, nc.x))
                nc.y = max(new_r * 0.5 + 64, min(WORLD_H - new_r * 0.5 - 64, nc.y))
            self.zone_plan.append({"wait_end": t + wait * 1000, "end": t + (wait + shrink) * 1000,
                                   "c0": Vector2(c), "r0": r, "c1": nc, "r1": new_r, "dps": dps})
            t += (wait + shrink) * 1000
            c, r = nc, new_r
        self.update_zone()

    def update_zone(self):
        if not self.zone_plan:
            self.zone = None
            return
        elapsed = max(0, self.now - self.match_start)
        for i, st in enumerate(self.zone_plan):
            if elapsed < st["end"]:
                if elapsed < st["wait_end"]:
                    c, r, shrinking, timer = st["c0"], st["r0"], False, st["wait_end"] - elapsed
                else:
                    k = (elapsed - st["wait_end"]) / (st["end"] - st["wait_end"])
                    c = st["c0"].lerp(st["c1"], k)
                    r = st["r0"] + (st["r1"] - st["r0"]) * k
                    shrinking, timer = True, st["end"] - elapsed
                self.zone = {"x": c.x, "y": c.y, "r": r, "nx": st["c1"].x, "ny": st["c1"].y, "nr": st["r1"],
                             "dps": st["dps"], "stage": i + 1, "timer": timer, "shrinking": shrinking}
                return
        last = self.zone_plan[-1]
        self.zone = {"x": last["c1"].x, "y": last["c1"].y, "r": last["r1"], "nx": last["c1"].x, "ny": last["c1"].y,
                     "nr": last["r1"], "dps": last["dps"] + 10, "stage": len(self.zone_plan), "timer": 0, "shrinking": False}

    def outside_zone(self, pos):
        z = self.zone
        return z is not None and Vector2(pos).distance_to((z["x"], z["y"])) > z["r"]

    # ------------------------------------------------------------------
    #  inputs
    # ------------------------------------------------------------------
    def read_keys(self, keys, controls):
        """Keyboard -> inputs dict (Lesson 6 - B1). W is always straight up the screen."""
        inputs = {}
        for action, key_list in controls.items():
            inputs[action] = any(keys[k] for k in key_list)
        move = Vector2(inputs["right"] - inputs["left"], inputs["down"] - inputs["up"])
        if move.length_squared() > 0:
            move = move.normalize()
        inputs["move_x"], inputs["move_y"] = move.x, move.y
        inputs["aim_angle"] = None
        return inputs

    def mouse_aim(self, inputs, tank):
        """Player 1 can aim with the mouse and fire with the left button."""
        if not self.mouse_active or tank is None:
            return inputs
        wx, wy = self.camera.to_world(*self.mouse_pos)
        inputs["aim_angle"] = Vector2(1, 0).angle_to(Vector2(wx, wy) - tank.pos)
        inputs["shoot"] = inputs.get("shoot") or self.mouse_down
        return inputs

    def local_inputs(self, keys, tank):
        """This computer's player: keyboard + mouse, and touch sticks if a finger was used."""
        inputs = self.mouse_aim(self.read_keys(keys, KEYS), tank)
        if self.touch.active:
            touch = self.touch.inputs()
            if touch["move_x"] or touch["move_y"]:
                inputs["move_x"], inputs["move_y"] = touch["move_x"], touch["move_y"]
            if touch["aim_angle"] is not None:
                inputs["aim_angle"] = touch["aim_angle"]
            inputs["shoot"] = inputs.get("shoot") or touch["shoot"]
        return inputs

    def collect_inputs(self):
        keys = pygame.key.get_pressed()
        all_inputs = {}
        if self.mode == "local" and not self.paused:
            all_inputs[1] = self.local_inputs(keys, self.find_tank(1))
        elif self.mode == "host":
            if not self.paused:
                all_inputs[1] = self.local_inputs(keys, self.find_tank(1))
            for player_id, inputs in list(self.network.inputs.items()):
                all_inputs[player_id] = inputs
        elif self.mode == "join":
            mine = self.find_tank(self.my_id)
            inputs = {} if self.paused else self.local_inputs(keys, mine)
            inputs["ready"] = self.ready
            self.network.send_inputs(inputs)
        if not (self.paused and self.mode == "local"):
            for player_id, bot in self.bots.items():
                tank = self.find_tank(player_id)
                if tank is not None:
                    all_inputs[player_id] = bot.think(self, tank)
        return all_inputs

    # ------------------------------------------------------------------
    #  the rules  (host / local / demo only)
    # ------------------------------------------------------------------
    def same_team(self, a, b):
        return self.rules == "tdm" and a != b and team_of(a) == team_of(b)

    def update(self, all_inputs):
        now = self.now
        if self.phase == "lobby":
            return                         # nobody moves until the host starts the match
        if self.phase == "countdown":
            if now - self.phase_started >= COUNTDOWN_MS:
                self.phase = "playing"
                self.phase_started = now
                self.match_start = now
                self.scoreboard.reset()
                self.events.append({"t": "go"})
            return
        if self.phase == "over":
            if self.mode == "demo" and now - self.phase_started > 4000:
                self.start_match(keep_phase=True, map_id=random.choice(MAP_IDS))
                self.phase = "playing"
            return

        was_shrinking = bool(self.zone and self.zone["shrinking"])
        self.update_zone()
        if self.zone is not None and self.zone["shrinking"] and not was_shrinking:
            self.events.append({"t": "zone"})
        if self.zone is not None:
            self.loot.zone_center = Vector2(self.zone["x"], self.zone["y"])
            self.loot.zone_radius = max(40, self.zone["r"])
        blockers = self.map.tank_blockers()
        for tank in self.tanks:
            if not tank.alive:
                if self.rules == "tdm" and now >= tank.respawn_at:
                    spawn = self.best_spawn(tank)
                    tank.respawn(spawn.x, spawn.y, now)
                    self.events.append({"t": "spawn", "id": tank.player_id, "x": spawn.x, "y": spawn.y})
                continue
            inputs = all_inputs.get(tank.player_id) or {}
            tank.move(inputs, blockers, self.map.bounds, self.map.is_ice(tank.pos.x, tank.pos.y))
            if inputs.get("shoot"):
                if tank.weapon is None:
                    if now - tank.last_shot_time > 700:
                        tank.last_shot_time = now
                        self.events.append({"t": "empty", "id": tank.player_id, "x": tank.pos.x, "y": tank.pos.y})
                else:
                    weapon = tank.weapon
                    shots = tank.shoot(now)
                    if shots:
                        self.projectiles.extend(shots)
                        muzzle = tank.pos + tank.aim * 18
                        self.events.append({"t": "shot", "id": tank.player_id, "x": round(muzzle.x), "y": round(muzzle.y),
                                            "a": round(tank.barrel_angle), "w": weapon})
            if self.zone is not None and self.outside_zone(tank.pos):       # the zone hurts
                tank.zone_damage += self.zone["dps"] / Settings.FPS
                if tank.zone_damage >= 1:
                    amount = int(tank.zone_damage)
                    tank.zone_damage -= amount
                    self.damage_tank(tank, amount, 0, "zone", shield_ok=False)
        self.push_tanks_apart(blockers)
        self.update_projectiles()
        self.events.extend(self.loot.landing_events(now, getattr(self, "_last_now", now)))
        self._last_now = now
        self.events.extend(self.loot.update(now, self.tanks))
        self.check_winner()

    def check_winner(self):
        now = self.now
        if self.rules == "tdm":
            red, blue = self.team_scores()
            if max(red, blue) >= Settings.KILL_LIMIT or self.scoreboard.time_left() == 0:
                self.win_team = 0 if red > blue else 1 if blue > red else None
                team_tanks = [t for t in self.tanks if self.win_team is None or t.team == self.win_team]
                best = max(team_tanks, key=lambda t: self.scoreboard.kills.get(t.player_id, 0), default=None)
                self.end_match(best.player_id if best else None)
        else:
            if len(self.tanks) < 2:
                return
            alive = [t for t in self.tanks if t.alive]
            if len(alive) <= 1:
                winner = alive[0].player_id if alive else self.leader_id()
                self.end_match(winner)

    def end_match(self, winner):
        self.phase = "over"
        self.phase_started = self.now
        self.winner = winner
        self.events.append({"t": "over", "win": winner})

    def team_scores(self):
        red = sum(k for pid, k in self.scoreboard.kills.items() if team_of(pid) == 0)
        blue = sum(k for pid, k in self.scoreboard.kills.items() if team_of(pid) == 1)
        return red, blue

    def best_spawn(self, tank):
        enemies = [t.pos for t in self.tanks if t.alive and t is not tank and not self.same_team(t.player_id, tank.player_id)]
        options = [self.map.spawn_point(i) for i in ((1, 3) if tank.team == 0 else (2, 4))]
        if not enemies:
            return options[0]
        return max(options, key=lambda p: min(p.distance_to(e) for e in enemies))

    def push_tanks_apart(self, blockers):
        alive = [t for t in self.tanks if t.alive]
        for i, a in enumerate(alive):
            for b in alive[i + 1:]:
                diff = a.pos - b.pos
                dist = diff.length()
                if 0 < dist < 22:
                    push = diff.normalize() * (22 - dist) / 2
                    for tank, sign in ((a, 1), (b, -1)):
                        old = Vector2(tank.pos)
                        tank.pos += push * sign
                        tank.rect.center = tank.pos
                        if not self.map.bounds.contains(tank.rect) or any(tank.rect.colliderect(w.rect) for w in blockers):
                            tank.pos = old
                            tank.rect.center = tank.pos
                    a.velocity, b.velocity = a.velocity * 0.7 + b.velocity * 0.3, b.velocity * 0.7 + a.velocity * 0.3

    def update_projectiles(self):
        walls = self.map.bullet_blockers()
        for p in self.projectiles:
            event, wall = p.update(walls, self.map.bounds)
            if event == "bounce":
                self.events.append({"t": "bounce", "x": round(p.pos.x), "y": round(p.pos.y)})
            elif event == "wall":
                if p.splash:
                    self.explode(p.pos, p.splash, p.damage, p.owner_id, 1.2, p.weapon)
                else:
                    self.events.append({"t": "wallhit", "x": round(p.pos.x), "y": round(p.pos.y)})
                    if wall is not None and wall.destructible:
                        self.damage_object(wall, p.damage, p.owner_id)
            elif event == "expired" and p.splash:
                self.explode(p.pos, p.splash, p.damage, p.owner_id, 1.0, p.weapon)
            if not p.alive:
                continue
            for tank in self.tanks:
                if not tank.alive or tank.player_id == p.owner_id or tank.player_id in p.hit_ids:
                    continue
                if self.same_team(tank.player_id, p.owner_id):
                    continue
                if tank.rect.inflate(p.radius * 2, p.radius * 2).collidepoint(p.pos):
                    if p.splash:
                        p.alive = False
                        self.explode(p.pos, p.splash, p.damage, p.owner_id, 1.3, p.weapon)
                    else:
                        self.damage_tank(tank, p.damage, p.owner_id, p.weapon)
                        self.events.append({"t": "hit", "x": round(p.pos.x), "y": round(p.pos.y)})
                        if p.pierce:
                            p.hit_ids.add(tank.player_id)
                        else:
                            p.alive = False
                    break
        self.projectiles = [p for p in self.projectiles if p.alive]

    def explode(self, pos, radius, damage, owner_id, size, weapon="rocket"):
        self.events.append({"t": "boom", "x": round(pos.x), "y": round(pos.y), "s": size})
        for tank, amount in splash_targets(pos, radius, damage, self.tanks, owner_id, self.same_team):
            self.damage_tank(tank, amount, owner_id, weapon)
        for obj in self.map.objects:
            if obj.alive and obj.destructible and Vector2(obj.rect.center).distance_to(pos) < radius + 8:
                self.damage_object(obj, damage, owner_id)

    def damage_object(self, obj, amount, attacker_id):
        obj.hit(amount)
        if obj.alive:
            return
        self.map.object_destroyed()
        center = Vector2(obj.rect.center)
        self.events.append({"t": "break", "x": round(center.x), "y": round(center.y), "k": obj.kind})
        if obj.explosive:
            self.explode(center, 64, 40, attacker_id, 1.6, weapon="barrel")

    def damage_tank(self, tank, amount, attacker_id, weapon, shield_ok=True):
        if not shield_ok:
            tank_shield, tank.shield_until = tank.shield_until, 0
        died = tank.take_damage(amount, self.now, attacker_id)
        if not shield_ok:
            tank.shield_until = tank_shield
        if not died:
            return
        if self.rules == "br":
            tank.respawn_at = NEVER
        self.deaths[tank.player_id] = self.deaths.get(tank.player_id, 0) + 1
        killer = self.find_tank(attacker_id)
        if killer is not None and killer is not tank:
            self.scoreboard.register_kill(killer, tank)
        self.events.append({"t": "die", "id": tank.player_id, "x": round(tank.pos.x), "y": round(tank.pos.y)})
        self.events.append({"t": "kill", "k": attacker_id, "v": tank.player_id, "w": weapon})

    # ------------------------------------------------------------------
    #  networking  (Lesson 6 - B3 get_state / Lesson 8 apply_state)
    # ------------------------------------------------------------------
    def get_state(self):
        tanks = []
        for t in self.tanks:
            tanks.append({"id": t.player_id, "x": round(t.pos.x, 1), "y": round(t.pos.y, 1),
                          "h": round(t.hull_angle), "b": round(t.barrel_angle), "hp": t.health, "al": t.alive,
                          "w": t.weapon, "am": t.ammo, "sh": t.shield_until > self.now, "fl": t.flash_until > self.now,
                          "rc": round(t.recoil), "vx": round(t.velocity.x, 2), "vy": round(t.velocity.y, 2),
                          "rs": max(0, min(99999, t.respawn_at - self.now)) if not t.alive else 0,
                          "n": self.names.get(t.player_id, "P%d" % t.player_id)})
        projectiles = [[WEAPON_ORDER.index(p.weapon), round(p.pos.x), round(p.pos.y), round(p.angle)] for p in self.projectiles]
        zone = None
        if self.zone:
            zone = {k: (round(v, 1) if isinstance(v, float) else v) for k, v in self.zone.items()}
        return {"type": "state", "now": self.now, "phase": self.phase, "pt": self.now - self.phase_started,
                "map": self.map.id, "seed": self.map.seed, "rules": self.rules, "left": self.time_left_value(), "tanks": tanks, "pr": projectiles,
                "cr": self.loot.to_state(), "dead": [o.index for o in self.map.objects if not o.alive],
                "dmg": [o.index for o in self.map.objects if o.alive and o.destructible and o.health < o.max_health * 0.5],
                "k": self.scoreboard.kills, "d": self.deaths, "ev": self.events, "win": self.winner,
                "wt": self.win_team, "zone": zone,
                "lobby": self.lobby_list() if self.phase == "lobby" else None}

    def apply_state(self, state):
        if state["map"] != self.map.id or state.get("seed") != self.map.seed:
            self.load_map(state["map"], state.get("seed"))
        self.rules = state.get("rules", self.rules)
        self.now = state["now"]
        self.phase = state["phase"]
        self.phase_started = self.now - state["pt"]
        self.time_left = state["left"]
        self.winner = state.get("win")
        self.win_team = state.get("wt")
        self.zone = state.get("zone")
        self.lobby = state.get("lobby") or []
        seen = []
        for d in state["tanks"]:
            seen.append(d["id"])
            tank = self.find_tank(d["id"])
            if tank is None:
                tank = self.add_player(d["id"], d["n"])
            self.names[d["id"]] = d["n"]
            tank.pos = Vector2(d["x"], d["y"])
            tank.rect.center = tank.pos
            tank.hull_angle, tank.barrel_angle = d["h"], d["b"]
            tank.aim = Vector2(1, 0).rotate(tank.barrel_angle)
            tank.health, tank.alive = d["hp"], d["al"]
            tank.weapon, tank.ammo = d["w"], d["am"]
            tank.shield_until = self.now + 100 if d["sh"] else 0
            tank.flash_until = self.now + 50 if d["fl"] else 0
            tank.recoil = d["rc"]
            tank.velocity = Vector2(d["vx"], d["vy"])
            tank.respawn_at = self.now + d["rs"] if self.rules == "tdm" else NEVER
            tank.color = art.tank_color(d["id"], self.rules == "tdm")
        self.tanks = [t for t in self.tanks if t.player_id in seen]
        self.projectiles = [ProjectileView(WEAPON_ORDER[w], x, y, a) for w, x, y, a in state["pr"]]
        self.loot.crates = [LootCrate(c["id"], (c["x"], c["y"]), c["k"], c["w"], c["t"]) for c in state["cr"]]
        dead, damaged = set(state["dead"]), set(state["dmg"])
        changed = False
        for obj in self.map.objects:
            alive = obj.index not in dead
            if obj.alive != alive:
                obj.alive = alive
                changed = True
            if obj.destructible and obj.index in damaged:
                obj.health = min(obj.health, obj.max_health * 0.4)
        if changed:
            self.map.object_destroyed()
        for player_id, kills in state["k"].items():
            self.scoreboard.kills[int(player_id)] = kills
        for player_id, deaths in state["d"].items():
            self.deaths[int(player_id)] = deaths

    # ------------------------------------------------------------------
    #  who is who (for the camera / HUD)
    # ------------------------------------------------------------------
    def local_ids(self):
        """Players who look at THIS screen."""
        if self.mode == "local":
            return list(self.humans)
        if self.mode == "host":
            phones = list(self.network.phones) if self.network else []
            return [1] + phones
        if self.mode == "join":
            return [self.my_id]
        return []

    def my_team(self):
        ids = self.local_ids()
        return team_of(ids[0]) if ids and self.rules == "tdm" else None

    def leader_id(self):
        kills = self.scoreboard.kills
        best = max(kills.values()) if kills else 0
        if best <= 0:
            return None
        top = [pid for pid, k in kills.items() if k == best and self.find_tank(pid)]
        return top[0] if len(top) == 1 else None

    def label(self, player_id):
        if player_id == self.my_id and self.mode in ("host", "join"):
            return "YOU"
        return self.names.get(player_id, "P%d" % player_id)

    def update_camera(self, instant=False):
        ids = self.local_ids()
        focus = [t.pos for t in self.tanks if t.player_id in ids and t.alive]
        if not focus:
            # spectating: follow whoever is still fighting
            alive = [t for t in self.tanks if t.alive]
            if self.mode == "demo":
                focus = [t.pos for t in alive]
            elif alive:
                if self.spectate_id is None or not any(t.player_id == self.spectate_id for t in alive):
                    self.spectate_id = alive[0].player_id
                focus = [self.find_tank(self.spectate_id).pos]
        if self.zone and self.mode == "demo" and not focus:
            focus = [(self.zone["x"], self.zone["y"])]
        self.camera.follow(focus or [self.map.bounds.center], instant=instant,
                           padding=220 if self.mode == "demo" else 150)

    # ------------------------------------------------------------------
    #  presentation (runs everywhere, also on clients)
    # ------------------------------------------------------------------
    def present_events(self, events):
        for ev in events:
            t = ev.get("t")
            if t == "kill":
                self.killfeed.append((ev["k"], ev["v"], ev.get("w"), self.now))
                self.killfeed = self.killfeed[-5:]
            elif t == "go":
                self.announcement = ("GO!", (120, 255, 140), self.now + 900)
                if not self.silent:
                    play_sound("go")
            elif t == "zone":
                self.announcement = ("ZONE CLOSING!", (255, 110, 190), self.now + 1600)
                if not self.silent:
                    play_sound("zone_warning")
            elif t == "over" and not self.silent:
                play_sound("confirm")
            self.fx.event(ev, sound=not self.silent)

    def cosmetic_update(self):
        """Track marks, drift dust, rocket smoke — from positions, so clients get them too."""
        for tank in self.tanks:
            if not tank.alive:
                if self.frame % 7 == 0:
                    self.fx.smoke_trail(tank.pos.x + random.uniform(-6, 6), tank.pos.y + random.uniform(-6, 6), 8)
                continue
            last = self.track_marks.get(tank.player_id)
            if last is None or last.distance_to(tank.pos) > 3:
                side = Vector2(0, 9).rotate(tank.hull_angle)
                self.fx.track(tank.pos.x + side.x, tank.pos.y + side.y, tank.hull_angle)
                self.fx.track(tank.pos.x - side.x, tank.pos.y - side.y, tank.hull_angle)
                self.track_marks[tank.player_id] = Vector2(tank.pos)
            if tank.is_drifting() and self.frame % 3 == 0:
                back = tank.pos - Vector2(1, 0).rotate(tank.hull_angle) * 12
                dust = (236, 242, 250) if self.map.theme_name == "frost" else (214, 176, 140)
                self.fx.dust(back.x, back.y, 1, dust)
        for p in self.projectiles:
            if p.weapon == "rocket":
                self.fx.smoke_trail(p.pos.x, p.pos.y, 10)

    def phone_statuses(self):
        statuses = {}
        for player_id in list(self.network.phones):
            tank = self.find_tank(player_id)
            if tank is None:
                continue
            statuses[player_id] = {"t": "status", "id": player_id, "hp": tank.health, "max": tank.max_health,
                                   "weapon": WEAPONS[tank.weapon]["name"] if tank.weapon else None, "ammo": tank.ammo,
                                   "alive": tank.alive, "kills": self.scoreboard.kills.get(player_id, 0),
                                   "color": list(tank.color)}
        return statuses

    # ------------------------------------------------------------------
    #  waiting room (lobby): host waits for players, then presses START
    # ------------------------------------------------------------------
    def lobby_list(self):
        """[[id, name, ready, kind], ...] for the waiting-room panel. kind: host / bot / player."""
        rows = []
        for tank in sorted(self.tanks, key=lambda t: t.player_id):
            pid = tank.player_id
            if pid == 1:
                rows.append([pid, self.names.get(pid, "HOST"), True, "host"])
            elif tank.is_bot:
                rows.append([pid, self.names.get(pid, "BOT"), True, "bot"])
            else:
                is_controller = self.network is not None and pid in getattr(self.network, "phones", {})
                ready = is_controller or bool(self.network and self.network.inputs.get(pid, {}).get("ready"))
                rows.append([pid, self.names.get(pid, "P%d" % pid), ready, "player"])
        return rows

    def everyone_ready(self):
        return all(row[2] for row in (self.lobby_list() if self.mode == "host" else self.lobby))

    def begin_match(self):
        """Host pressed START in the waiting room."""
        if self.mode == "host" and self.phase == "lobby" and self.everyone_ready():
            play_sound("confirm")
            self.start_match(new_map=False)

    def toggle_ready(self):
        if self.mode == "join" and self.phase == "lobby":
            self.ready = not self.ready
            play_sound("confirm" if self.ready else "click")

    def sync_players(self):
        """Host: a tank appears when a laptop/phone joins and disappears when it leaves."""
        connected = self.network.connected_ids()
        for player_id in connected:
            if self.find_tank(player_id) is None:
                tank = self.add_player(player_id, self.network.names.get(player_id, "P%d" % player_id))
                tank.respawn(tank.pos.x, tank.pos.y, self.now)
                if self.zone is not None and self.outside_zone(tank.pos):
                    p = self.map.random_free_point(near=(self.zone["x"], self.zone["y"]), radius=max(40, self.zone["r"] - 40))
                    tank.respawn(p.x, p.y, self.now)
                self.events.append({"t": "spawn", "id": player_id, "x": tank.pos.x, "y": tank.pos.y})
                self.announcement = ("PLAYER %d JOINED" % player_id, tank.color, self.now + 1500)
        for tank in list(self.tanks):
            if tank.player_id != 1 and not tank.is_bot and tank.player_id not in connected:
                self.tanks.remove(tank)
                self.announcement = ("PLAYER %d LEFT" % tank.player_id, (200, 200, 200), self.now + 1500)
        for player_id, name in list(self.network.names.items()):
            self.names[player_id] = name
            tank = self.find_tank(player_id)
            if tank is not None:
                tank.name = name

    # ------------------------------------------------------------------
    #  one frame
    # ------------------------------------------------------------------
    def step(self):
        # After leave() the connection is closed (network = None) but the App may still call
        # step() once more in the same frame (several updates per frame on phones) -> stop here.
        if not self.running or (self.mode in ("host", "join") and self.network is None):
            return
        self.frame += 1
        self.events = []
        if self.network is not None and hasattr(self.network, "poll"):
            self.network.poll()                 # web version: pick up network messages
        if self.mode == "join":
            self.collect_inputs()
            if not self.network.connected:
                self.leave("The host closed the game.")
                return
            state = self.network.latest_state
            if state is not None:
                self.apply_state(state)
            self.present_events(self.network.take_events())
        else:
            self.now = pygame.time.get_ticks()
            if self.mode == "host":
                self.sync_players()
            all_inputs = self.collect_inputs()
            if not (self.paused and self.mode == "local"):
                self.update(all_inputs)
            if self.mode == "host":
                self.network.send_state(self.get_state())
                if self.frame % 6 == 0:
                    self.network.send_phone_status(self.phone_statuses())
            self.present_events(self.events)
        if self.phase == "countdown":
            left = 3 - (self.now - self.phase_started) // 1000
            if left > 0 and left != getattr(self, "_last_count", None):
                self._last_count = left
                if not self.silent:
                    play_sound("countdown", 0.6)
                self.announcement = (str(left), (255, 230, 120), self.now + 900)
        if self.zone and not self.silent and self.frame % 40 == 0 and self.phase == "playing":
            if any(t.alive and t.player_id in self.local_ids() and self.outside_zone(t.pos) for t in self.tanks):
                play_sound("zone_hurt")
        if web.IS_WEB and self.frame % 60 == 1:
            cg_name = web.cg_name()                 # CrazyGames username may arrive a bit after start
            if cg_name and self.mode == "host" and self.names.get(1) in ("HOST", "", None):
                self.names[1] = cg_name
                if self.find_tank(1) is not None:
                    self.find_tank(1).name = cg_name
            code = self.online_room_code()          # CrazyGames: share our room so friends can Join / Invite
            if code:
                joinable = len([t for t in self.tanks if not t.is_bot]) < 4
                web.cg_call("dtCG.room(%s, %s)" % (web.js_str(code), "true" if joinable else "false"))
        self.cosmetic_update()
        self.fx.update(self.now)
        self.update_camera()

    def leave(self, message=None):
        self.running = False
        self.result = ("menu", message)
        self.close()

    def online_room_code(self):
        """5-digit code of the online room we're in (host or joiner), else None."""
        net = self.network
        code = getattr(net, "ip", None) if self.mode == "host" else getattr(net, "code", None)
        if getattr(net, "online", False) and code and web.is_room_code(str(code)):
            return str(code)
        return None

    def close(self):
        if web.IS_WEB:
            web.cg_call("dtCG.leftRoom()")          # CrazyGames: we left the room
        if self.network is not None:
            self.network.close()
            self.network = None

    # ------------------------------------------------------------------
    #  App screen interface
    # ------------------------------------------------------------------
    def handle_event(self, event):
        if self.touch.handle_event(event):
            if self.touch.pause_tapped:
                self.touch.pause_tapped = False
                if self.phase != "over":
                    self.paused = not self.paused
                    self.touch.release_all()
                    play_sound("click")
            return
        if getattr(event, "touch", False) and event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
            # a finger also sends a fake mouse event: only use it to tap HUD buttons
            if event.type == pygame.MOUSEBUTTONDOWN:
                game_hud.handle_click(self, event.pos)
            return
        if event.type == pygame.MOUSEMOTION:
            self.mouse_pos = event.pos
            self.mouse_active = True
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.mouse_pos = event.pos
            if game_hud.handle_click(self, event.pos):
                return
            self.mouse_down = True
            self.mouse_active = True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.mouse_down = False
        elif event.type == pygame.KEYDOWN:
            if event.key in BARREL_KEYS:
                self.mouse_active = False          # keys take the barrel back from the mouse
            if event.key == pygame.K_ESCAPE:
                if self.phase in ("over", "lobby"):
                    self.leave()
                else:
                    self.paused = not self.paused
                    play_sound("click")
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE) and self.phase == "lobby":
                self.begin_match() if self.mode == "host" else self.toggle_ready()
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER) and self.phase == "over" and self.mode in ("local", "host"):
                self.start_match()
            elif event.key == pygame.K_TAB and not any(t.alive for t in self.tanks if t.player_id in self.local_ids()):
                alive = [t.player_id for t in self.tanks if t.alive]
                if alive:                              # spectate the next player
                    i = alive.index(self.spectate_id) if self.spectate_id in alive else -1
                    self.spectate_id = alive[(i + 1) % len(alive)]
            elif self.paused and event.key == pygame.K_m:
                self.leave()

    def update_screen(self):
        self.step()

    def draw(self, surface):
        renderer.draw_world(self, surface)
        game_hud.draw(self, surface)
        if self.phase not in ("over", "lobby") and not self.paused:
            self.touch.draw(surface)

    def join_info(self):
        if self.mode != "host" or self.network is None:
            return None
        if getattr(self.network, "error", None):
            return self.network.error, None
        ip = self.network.ip if hasattr(self.network, "ip") else get_lan_ip()
        return ip or "starting...", self.network.phone_url()

    def time_left_value(self):
        if self.mode == "join":
            return self.time_left
        if self.rules == "br":
            return max(0, (self.now - self.match_start) // 1000) if self.phase != "countdown" else 0
        if self.phase == "countdown":
            return MATCH_TIME
        return self.scoreboard.time_left()
