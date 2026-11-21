# =====================================================================
#  part1_engine/view.py  —  CAMERA + 3/4 TOP-DOWN DRAWING HELPERS
# =====================================================================
#
# The game world is flat (x, y in world pixels, 32 per tile). We draw it
# like a classic 3/4 top-down game: the floor is seen from above, and
# anything with HEIGHT (walls, crates, tanks) is drawn shifted UP by its
# height, so you also see its front face.
#
#     view point = (x - camera_left,  y - camera_top - z)
#
# PIXEL ART: the world is drawn 1:1 onto a small surface (e.g. 640 x 360)
# and then scaled up with NO smoothing, so every pixel stays crisp.
# The camera can zoom out (draw a bigger area, scale up less) when the
# players it follows are far apart.
#
# TANKS use "sprite stacking": a 3D model cut into 1-pixel-high slices.
# Each slice is rotated to the tank's angle and drawn 1 px above the one
# below it -> a chunky 3D tank that can face ANY direction.
# =====================================================================
import math

import pygame
from pygame.math import Vector2

from shared.settings import Settings

W, H = Settings.SCREEN_WIDTH, Settings.SCREEN_HEIGHT
OUTLINE = (28, 20, 30)
YS = 0.75            # camera tilt: the floor is squashed to 75% height, so you see front faces


def shade(color, factor):
    return tuple(max(0, min(255, int(c * factor))) for c in color[:3])


def mix(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


class Camera:
    MAX_ZOOM = 2.0       # normal: 1 world px = 2 screen px
    MIN_ZOOM = 1.05

    def __init__(self, world_rect):
        self.world = pygame.Rect(world_rect)
        self.x, self.y = self.world.center
        self.zoom = self.MAX_ZOOM
        self.shake = (0, 0)

    @property
    def view_size(self):
        return (math.ceil(W / self.zoom), math.ceil(H / self.zoom))

    def follow(self, points, instant=False, padding=150):
        """Keep all `points` (world positions) on screen; zoom out if they're far apart."""
        if not points:
            return
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
        span_w = max(xs) - min(xs) + padding * 2
        span_h = (max(ys) - min(ys)) * YS + padding * 2
        target_zoom = max(self.MIN_ZOOM, min(self.MAX_ZOOM, W / span_w, H / span_h))
        k = 1.0 if instant else 0.08
        self.zoom += (target_zoom - self.zoom) * k
        self.zoom = round(self.zoom * 40) / 40          # few distinct sizes -> reuse surfaces
        self.x += (cx - self.x) * (1.0 if instant else 0.12)
        self.y += (cy - self.y) * (1.0 if instant else 0.12)
        self.clamp()

    def clamp(self):
        vw, vh = self.view_size
        margin = 60
        if self.world.width + margin * 2 <= vw:
            self.x = self.world.centerx
        else:
            self.x = max(self.world.left - margin + vw / 2, min(self.world.right + margin - vw / 2, self.x))
        world_h = self.world.height * YS
        if world_h + margin * 2 + 40 <= vh:
            self.y = self.world.centery
        else:
            vy = self.y * YS
            vy = max(self.world.top * YS - margin - 40 + vh / 2, min(world_h + margin + 30 - vh / 2, vy))
            self.y = vy / YS

    @property
    def left(self):
        return int(self.x - self.view_size[0] / 2) - int(self.shake[0])

    @property
    def top(self):
        """Top of the view, in VIEW pixels (world y is squashed by YS)."""
        return int(self.y * YS - self.view_size[1] / 2) - int(self.shake[1])

    def to_view(self, x, y, z=0):
        """World (x, y on the ground, z = height) -> pixel on the small view surface."""
        return (int(round(x)) - self.left, int(round(y * YS - z)) - self.top)

    def to_world(self, sx, sy):
        """Real screen pixel (1280x720) -> world point on the ground (mouse aiming)."""
        return (self.left + sx / self.zoom, (self.top + sy / self.zoom) / YS)

    def view_rect(self):
        """The part of the WORLD that is visible."""
        vw, vh = self.view_size
        return pygame.Rect(self.left, int(self.top / YS), vw, int(vh / YS))


# ---------------------------------------------------------------------
#  outlines + shadows (what makes it look like pixel art)
# ---------------------------------------------------------------------
def outlined(img, color=OUTLINE):
    """Return img with a 1-px dark outline around its shape."""
    mask = pygame.mask.from_surface(img, 40)
    sil = mask.to_surface(setcolor=color + (255,), unsetcolor=(0, 0, 0, 0))
    out = pygame.Surface((img.get_width() + 2, img.get_height() + 2), pygame.SRCALPHA)
    for dx, dy in ((0, 1), (2, 1), (1, 0), (1, 2)):
        out.blit(sil, (dx, dy))
    out.blit(img, (1, 1))
    return out


def silhouette(img, color=(0, 0, 0, 80)):
    mask = pygame.mask.from_surface(img, 40)
    return mask.to_surface(setcolor=color, unsetcolor=(0, 0, 0, 0))


# ---------------------------------------------------------------------
#  sprite stacking
# ---------------------------------------------------------------------
class StackModel:
    BUCKETS = 72          # cached in 5 degree steps

    def __init__(self, slices, z_start=0):
        self.slices = slices
        self.z_start = z_start
        self.cache = {}

    def _bucket(self, angle):
        return round((angle % 360) / (360 / self.BUCKETS)) % self.BUCKETS

    def render(self, angle):
        """(surface, (ax, ay)) — (ax, ay) is the point to put on the model's ground center."""
        b = self._bucket(angle)
        if b in self.cache:
            return self.cache[b]
        a = b * (360 / self.BUCKETS)
        rotated = []
        for s in self.slices:
            r = pygame.transform.rotate(s, -a)
            rotated.append(pygame.transform.scale(r, (r.get_width(), max(1, round(r.get_height() * YS)))))
        rw, rh = rotated[0].get_size()
        n = len(rotated)
        canvas = pygame.Surface((rw, rh + n + self.z_start), pygame.SRCALPHA)
        base = canvas.get_height() - rh - self.z_start
        for i, r in enumerate(rotated):
            canvas.blit(r, (0, base - i))
        canvas = outlined(canvas)
        anchor = (rw / 2 + 1, base + rh / 2 + self.z_start + 1)
        self.cache[b] = (canvas, anchor)
        return self.cache[b]

    def shadow(self, angle):
        key = ("sh", self._bucket(angle))
        if key not in self.cache:
            a = self._bucket(angle) * (360 / self.BUCKETS)
            r = pygame.transform.rotate(self.slices[0], -a)
            r = pygame.transform.scale(r, (r.get_width(), max(1, round(r.get_height() * YS))))
            self.cache[key] = (silhouette(r, (20, 10, 20, 90)), (r.get_width() / 2, r.get_height() / 2))
        return self.cache[key]


def build_slices(parts, size=48):
    """parts: boxes / cylinders in model space (x forward, y right, z up, origin = center).
    Every slice is shaded: darker near the bottom, a bright rim on each part's top layer."""
    top = max(p["z1"] for p in parts)
    bottom = min(p["z0"] for p in parts)
    c = size // 2
    slices = []
    for z in range(bottom, top):
        s = pygame.Surface((size, size), pygame.SRCALPHA)
        for p in parts:
            if not (p["z0"] <= z < p["z1"]):
                continue
            t = (z - p["z0"] + 1) / (p["z1"] - p["z0"])
            is_top = z == p["z1"] - 1
            base = p["color"]
            color = shade(base, 1.0) if is_top else shade(base, 0.55 + 0.3 * t)
            if p["shape"] == "box":
                x0, x1, y0, y1 = p["x0"], p["x1"], p["y0"], p["y1"]
                if p.get("taper") and z >= p.get("taper_from", p["z0"]):
                    x1 -= (z - p.get("taper_from", p["z0"]) + 1) * p["taper"]
                rect = pygame.Rect(c + x0, c + y0, max(1, round(x1 - x0)), y1 - y0)
                pygame.draw.rect(s, color, rect)
                if is_top:
                    # light from the top-left: bright top-left edge, dark bottom-right edge
                    pygame.draw.line(s, shade(base, 1.25), rect.topleft, (rect.right - 1, rect.top))
                    pygame.draw.line(s, shade(base, 1.18), rect.topleft, (rect.left, rect.bottom - 1))
                    pygame.draw.line(s, shade(base, 0.72), (rect.left, rect.bottom - 1), (rect.right - 1, rect.bottom - 1))
                    for sx in range(int(rect.left) + 2, int(rect.right) - 1, p.get("stripes", 999)):
                        pygame.draw.line(s, shade(base, 1.45), (sx, rect.top + 1), (sx, rect.bottom - 2))
                    for detail in p.get("details", []):
                        dx, dy, dw, dh, dcol = detail
                        pygame.draw.rect(s, dcol, (c + dx, c + dy, dw, dh))
            else:
                center = (c + p.get("cx", 0), c + p.get("cy", 0))
                pygame.draw.circle(s, color, center, p["r"])
                if is_top:
                    pygame.draw.circle(s, shade(base, 1.22), (center[0] - 1, center[1] - 1), max(1, p["r"] - 2))
                    pygame.draw.circle(s, color, (center[0], center[1]), max(1, p["r"] - 3))
                    for detail in p.get("details", []):
                        dx, dy, dw, dh, dcol = detail
                        pygame.draw.rect(s, dcol, (c + dx, c + dy, dw, dh))
        slices.append(s)
    return slices, bottom
