# =====================================================================
#  part2_combat/fx.py  —  JUICE: cartoon explosions, sparks, smoke,
#                          debris, muzzle flashes, tracks, screen shake
# =====================================================================
# The game produces EVENTS (plain dicts, so they also travel over the
# network), e.g. {"t": "boom", "x": 300, "y": 220, "s": 1.5}.
# FX.event() turns each event into particles + a sound.
# Particles live in the world (x, y on the ground, z = height) and are
# drawn as chunky pixel shapes, so debris flies UP and bounces back down.
# =====================================================================
import math
import random

import pygame

from part2_combat.weapons import WEAPONS
from part1_engine.view import YS
from part4_ui.assets import get_font, play_sound

GRAVITY = 0.32
OUTLINE = (28, 20, 30)
PUFF_COLORS = [(255, 252, 230), (255, 236, 120), (255, 176, 60), (230, 110, 50), (120, 112, 112), (90, 86, 90)]


class Particle:
    __slots__ = ("x", "y", "z", "vx", "vy", "vz", "life", "max_life", "size", "color", "kind", "grow")

    def __init__(self, x, y, z, vx, vy, vz, life, size, color, kind, grow=0.0):
        self.x, self.y, self.z = x, y, z
        self.vx, self.vy, self.vz = vx, vy, vz
        self.life = self.max_life = life
        self.size = size
        self.color = color
        self.kind = kind          # "spark", "debris", "puff", "smoke", "dust"
        self.grow = grow


class FX:
    def __init__(self):
        self.particles = []
        self.tracks = []          # [x, y, angle, born]
        self.texts = []           # [x, y, text, color, born]
        self.beams = []           # [x1, y1, x2, y2, color, born]
        self.flashes = []         # [x, y, angle, color, born]
        self.rings = []           # [x, y, radius, color, born]
        self.shake = 0.0
        self.ground = None        # baked floor: scorch marks are painted onto it
        self.now = 0
        self.sound = True

    def set_ground(self, surface):
        self.ground = surface
        self.particles.clear()
        self.tracks.clear()

    # ---------- events ----------
    def event(self, ev, sound=True):
        snd = sound and self.sound
        t = ev.get("t")
        x, y = ev.get("x", 0), ev.get("y", 0)
        if t == "shot":
            stats = WEAPONS.get(ev.get("w"), WEAPONS["machinegun"])
            self.flashes.append([x, y, ev.get("a", 0), stats["color"], self.now])
            self.sparks(x, y, 3, stats["color"], z=12, speed=2)
            if stats.get("beam"):
                a = math.radians(ev.get("a", 0))
                self.beams.append([x, y, x + math.cos(a) * 520, y + math.sin(a) * 520, stats["color"], self.now])
            if snd:
                play_sound(stats["sound"])
            self.add_shake(stats["shake"] * 0.4)
        elif t == "boom":
            size = ev.get("s", 1.0)
            self.explosion(x, y, size)
            if snd:
                play_sound("big_explosion" if size >= 1.4 else "explosion")
        elif t == "hit":
            self.sparks(x, y, 8, (255, 220, 130), z=10)
            if snd:
                play_sound("hit")
        elif t in ("wallhit", "bounce"):
            self.sparks(x, y, 5, (255, 236, 180), z=8)
            self.dust(x, y, 2)
        elif t == "break":
            color = {"crate": (170, 108, 56), "metal": (136, 146, 160), "barricade": (190, 190, 180),
                     "barrel": (204, 52, 44)}.get(ev.get("k"), (160, 140, 120))
            self.debris(x, y, 12, color)
            self.dust(x, y, 6)
            if snd:
                play_sound("break")
        elif t == "pick":
            color = WEAPONS.get(ev.get("w"), {}).get("color", (255, 255, 255))
            self.texts.append([x, y, ev.get("text", ""), color, self.now])
            self.rings.append([x, y, 20, color, self.now])
            if snd:
                play_sound("pickup")
        elif t == "heal":
            self.texts.append([x, y, ev.get("text", "+HP"), (120, 255, 140), self.now])
            self.rings.append([x, y, 20, (120, 255, 140), self.now])
            if snd:
                play_sound("heal")
        elif t == "die":
            self.explosion(x, y, 2.0)
            self.debris(x, y, 18, (70, 68, 78))
            if snd:
                play_sound("big_explosion")
        elif t == "spawn":
            self.rings.append([x, y, 26, (140, 220, 255), self.now])
            if snd:
                play_sound("spawn", 0.6)
        elif t == "empty":
            self.texts.append([x, y, "NO WEAPON", (255, 130, 110), self.now])
            if snd:
                play_sound("empty", 0.6)
        elif t == "drop":
            self.dust(x, y, 8)
            self.add_shake(1.5)
            if snd:
                play_sound("crate_drop", 0.6)

    # ---------- emitters ----------
    def add_shake(self, amount):
        self.shake = min(10.0, self.shake + amount)

    def explosion(self, x, y, size=1.0):
        """Cartoon explosion: a cluster of puffs that go white -> yellow -> orange -> grey smoke."""
        for _ in range(int(7 * size) + 3):
            a = random.uniform(0, math.tau)
            d = random.uniform(0, 10 * size)
            sp = random.uniform(0.2, 0.9) * size
            self.particles.append(Particle(x + math.cos(a) * d, y + math.sin(a) * d, random.uniform(4, 14),
                                           math.cos(a) * sp, math.sin(a) * sp * 0.7, random.uniform(0.1, 0.6),
                                           random.randint(26, 40), random.uniform(5, 10) * size, None, "puff", 0.25))
        self.rings.append([x, y, 30 * size, (255, 236, 160), self.now])
        self.sparks(x, y, int(12 * size), (255, 214, 100), z=8, speed=3.2 * size)
        self.debris(x, y, int(5 * size), (250, 220, 170))
        self.add_shake(3.5 * size)
        if self.ground is not None:                       # scorch mark on the floor
            r = int(12 * size)
            scorch = pygame.Surface((r * 4, r * 3), pygame.SRCALPHA)
            for _ in range(8):
                pygame.draw.circle(scorch, (30, 20, 20, 36), (r * 2 + random.randint(-r, r), r * 1.5 + random.randint(-r // 2, r // 2)),
                                   random.randint(r // 2, r))
            self.ground.blit(scorch, (x - r * 2, y * YS - r * 1.5))

    def sparks(self, x, y, count, color, z=8, speed=2.5):
        for _ in range(count):
            a = random.uniform(0, math.tau)
            sp = random.uniform(0.4, 1.0) * speed
            self.particles.append(Particle(x, y, z, math.cos(a) * sp, math.sin(a) * sp, random.uniform(0.5, 3),
                                           random.randint(10, 20), 2, color, "spark"))

    def debris(self, x, y, count, color):
        for _ in range(count):
            a = random.uniform(0, math.tau)
            sp = random.uniform(0.6, 2.6)
            self.particles.append(Particle(x, y, 8, math.cos(a) * sp, math.sin(a) * sp, random.uniform(2, 5),
                                           random.randint(50, 90), random.choice((2, 3, 3, 4)), color, "debris"))

    def dust(self, x, y, count, color=(206, 180, 150)):
        for _ in range(count):
            a = random.uniform(0, math.tau)
            sp = random.uniform(0.1, 0.8)
            self.particles.append(Particle(x + random.uniform(-4, 4), y + random.uniform(-4, 4), 1,
                                           math.cos(a) * sp, math.sin(a) * sp, random.uniform(0.05, 0.3),
                                           random.randint(22, 40), random.uniform(3, 5), color, "dust", 0.08))

    def smoke_trail(self, x, y, z=10):
        self.particles.append(Particle(x, y, z, random.uniform(-0.15, 0.15), random.uniform(-0.15, 0.15), 0.2,
                                       random.randint(24, 36), random.uniform(2.5, 4), (150, 146, 150), "smoke", 0.12))

    def track(self, x, y, hull_angle):
        self.tracks.append([x, y, hull_angle, self.now])
        if len(self.tracks) > 400:
            del self.tracks[:40]

    # ---------- update ----------
    def update(self, now):
        self.now = now
        alive = []
        for p in self.particles:
            p.life -= 1
            if p.life <= 0:
                continue
            p.x += p.vx
            p.y += p.vy
            p.z += p.vz
            if p.kind in ("spark", "debris"):
                p.vz -= GRAVITY
                if p.z < 0:
                    p.z = 0
                    p.vz *= -0.35
                    p.vx *= 0.55
                    p.vy *= 0.55
            else:
                p.vx *= 0.92
                p.vy *= 0.92
                p.size += p.grow
            alive.append(p)
        self.particles = alive
        self.tracks = [t for t in self.tracks if now - t[3] < 6000]
        self.texts = [t for t in self.texts if now - t[4] < 1200]
        self.beams = [b for b in self.beams if now - b[5] < 200]
        self.flashes = [f for f in self.flashes if now - f[4] < 60]
        self.rings = [r for r in self.rings if now - r[4] < 380]
        self.shake *= 0.84
        if self.shake < 0.3:
            self.shake = 0.0

    def offset(self):
        if self.shake <= 0:
            return (0, 0)
        return (random.uniform(-self.shake, self.shake), random.uniform(-self.shake, self.shake))

    # ---------- draw (onto the small pixel view, with the camera) ----------
    def draw_ground(self, surf, cam):
        view = cam.view_rect().inflate(40, 40)
        dots = self.__dict__.setdefault("_track_dots", {})
        for x, y, angle, born in self.tracks:
            if not view.collidepoint(x, y):
                continue
            level = int(7 * (1 - (self.now - born) / 6000))
            if level <= 0:
                continue
            if level not in dots:
                d = pygame.Surface((3, 3), pygame.SRCALPHA)
                d.fill((20, 10, 10, level * 9))
                dots[level] = d
            vx, vy = cam.to_view(x, y)
            surf.blit(dots[level], (vx - 1, vy - 1))
        for x, y, radius, color, born in self.rings:
            k = (self.now - born) / 380
            r = int(radius * (0.3 + k))
            vx, vy = cam.to_view(x, y)
            if r > 2:
                pygame.draw.ellipse(surf, color, (vx - r, vy - r * 0.7, r * 2, r * 1.4), max(1, int(3 * (1 - k))))

    def draw(self, surf, cam):
        view = cam.view_rect().inflate(60, 60)
        puffs = []
        for p in self.particles:
            if not view.collidepoint(p.x, p.y):
                continue
            vx, vy = cam.to_view(p.x, p.y, p.z)
            k = p.life / p.max_life
            if p.kind == "spark":
                surf.fill(p.color, (vx, vy, 2, 2))
            elif p.kind == "debris":
                surf.fill(OUTLINE, (vx - 1, vy - 1, p.size + 2, p.size + 2))
                surf.fill(p.color, (vx, vy, p.size, p.size))
            elif p.kind == "puff":
                puffs.append((p, vx, vy, k))
            else:
                r = max(1, int(p.size))
                color = p.color
                s = pygame.Surface((r * 2 + 2, r * 2 + 2), pygame.SRCALPHA)
                pygame.draw.circle(s, color + (int(170 * k),), (r + 1, r + 1), r)
                surf.blit(s, (vx - r, vy - r))
        # explosion puffs: draw dark outlines first, then the colours (cartoon look)
        for p, vx, vy, k in puffs:
            r = int(p.size * (0.6 + 0.6 * (1 - k)) if k > 0.3 else p.size * k * 2.2)
            if r > 0:
                pygame.draw.circle(surf, OUTLINE, (vx, vy), r + 1)
        for p, vx, vy, k in puffs:
            r = int(p.size * (0.6 + 0.6 * (1 - k)) if k > 0.3 else p.size * k * 2.2)
            if r <= 0:
                continue
            stage = min(len(PUFF_COLORS) - 1, int((1 - k) * len(PUFF_COLORS)))
            color = PUFF_COLORS[stage]
            pygame.draw.circle(surf, color, (vx, vy), r)
            if r > 3:
                hi = PUFF_COLORS[max(0, stage - 1)]
                pygame.draw.circle(surf, hi, (vx - r // 3, vy - r // 3), max(1, r // 2))
        for x, y, angle, color, born in self.flashes:
            vx, vy = cam.to_view(x, y, 12)
            a = math.radians(angle)
            dx, dy = math.cos(a), math.sin(a)
            tip = (vx + dx * 12, vy + dy * 12)
            side = (-dy * 4, dx * 4)
            pygame.draw.polygon(surf, (255, 246, 170), [(vx + side[0], vy + side[1]), tip, (vx - side[0], vy - side[1])])
            pygame.draw.circle(surf, (255, 255, 230), (vx, vy), 3)
        for x1, y1, x2, y2, color, born in self.beams:
            k = 1 - (self.now - born) / 200
            a = cam.to_view(x1, y1, 12)
            b = cam.to_view(x2, y2, 12)
            pygame.draw.line(surf, color, a, b, max(1, int(5 * k)))
            pygame.draw.line(surf, (255, 255, 255), a, b, max(1, int(2 * k)))

    def draw_texts(self, surf, cam):
        font = get_font(8, "pixel")
        for x, y, text, color, born in self.texts:
            age = (self.now - born) / 1200
            vx, vy = cam.to_view(x, y, 30 + age * 22)
            img = font.render(text, False, color)
            sh = font.render(text, False, OUTLINE)
            if age > 0.7:
                a = int(255 * (1 - age) / 0.3)
                img.set_alpha(a)
                sh.set_alpha(a)
            px = vx - img.get_width() // 2
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                surf.blit(sh, (px + dx, vy + dy))
            surf.blit(img, (px, vy))
