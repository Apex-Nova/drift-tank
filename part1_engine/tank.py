# =====================================================================
#  part1_engine/tank.py  —  THE TANK CLASS
#  OWNER: Person 1 (Engine)          WHEN: Phase 1 → Phase 4
# =====================================================================
#
# WHAT THIS FILE IS
#   One class, Tank. Every player is one Tank object. The SAME class is used
#   for player 1, 2, 3, 4 — what makes them different is the data you pass
#   in when you create them (color, start position, which keys control it).
#
# TOPICS TO STUDY (in this order)
#   1. Python classes: __init__, self, attributes, methods
#   2. pygame.Rect: x, y, width, height, center, move_ip(), clamp_ip()
#   3. pygame.key.get_pressed() — "is this key held right now?"
#      vs KEYDOWN events — "was this key pressed this frame?"
#      (Know which one fits moving and which one fits shooting.)
#   4. Direction as a pair (dx, dy): (0,-1) is up, (1,0) is right, etc.
#      Remember: in Pygame, y grows DOWNWARD.
#   5. Collision-blocked movement: move, check walls, undo if blocked.
#      Study "move X and Y separately" so tanks slide along walls.
#   6. Cooldowns with pygame.time.get_ticks() (milliseconds since start)
#   7. (Phase 4) Drawing an image instead of a rectangle, and rotating it
#      with pygame.transform.rotate() to face the direction it moves
#
# WHAT TO BUILD — step by step
#   [ ] Tank stores: rect, color, health, player id, facing direction, speed,
#       and its key scheme (passed in — don't hardcode WASD inside the class!)
#   [ ] draw(screen): draw it as a colored rectangle (+ a small "barrel"
#       mark showing which way it faces)
#   [ ] Move with its keys; remember which way it last moved (facing)
#   [ ] Can't leave the screen
#   [ ] Can't drive through walls (walls come in as a list of objects with .rect)
#   [ ] shoot(): returns a NEW Bullet (Person 2's class) starting at the
#       front of the tank, flying in the facing direction — or None if the
#       cooldown hasn't finished
#   [ ] take_damage(amount): lowers health; at 0 the tank is no longer alive
#   [ ] (Phase 4) fields that power-ups can change: speed boost, shield,
#       faster cooldown — and a way for them to wear off
#
# CONTRACT (others rely on these names — see docs/CLASS_CONTRACTS.md)
#   rect, health, color, player_id, direction, alive,
#   move/update, shoot(), take_damage(), draw()
#
# HOW TO TEST ALONE
#   Make one tank in game.py with fake walls (a few pygame.Rects) and drive it.
#   Until Person 2's Bullet exists, let shoot() just print "bang".
#
# PRACTICE FIRST (in practice/<your-name>/)
#   "Move a square with the arrow keys" — 1 window, 1 rect, 1 loop.
#   That small exercise is 80% of this file.
# =====================================================================
import pygame
from pygame.math import Vector2
from shared.settings import Settings
from part2_combat.collisions import rect_touches_wall

from part2_combat.bullet import Bullet

class Tank:
    def __init__(self,start_x, start_y, color, name, speed,player_id, score=0, controls=None):

        self.hull_image = pygame.image.load("part1_engine/assets/tank_hull.png").convert_alpha()
        self.gun_image = pygame.image.load("part1_engine/assets/tank_gun.png").convert_alpha()


        self.speed = speed or Settings.TANK_SPEED
        self.color = color
        tint = (self.color[0] // 3, self.color[1] // 3, self.color[2] // 3)
        self.hull_image.fill(tint, special_flags=pygame.BLEND_RGB_ADD)
        self.name = name
        self.player_id = player_id
        self.score = score
        self.controls = controls or {
            "up": pygame.K_UP,
            "down": pygame.K_DOWN,
            "left": pygame.K_LEFT,
            "right": pygame.K_RIGHT
        }
        self.health = Settings.TANK_MAX_HEALTH
        self.alive = True

        self.rect = pygame.Rect(start_x, start_y, 50, 50)
        self.pos = Vector2(self.rect.center)

        self.barrel_angle = 0           # barrel angles
        self.barrel_speed = 3           # barrel angles
        self.aim = Vector2(1, 0)        # barrel angles

        self.hull_angle = 0
        self.target_angle = 0
        self.hull_turn_speed = 4

        self.last_shot_time = 0
    def shoot(self):    
        current_time = pygame.time.get_ticks()
        if current_time - self.last_shot_time >= Settings.TANK_SHOOT_COOLDOWN:
            self.last_shot_time = current_time
            return Bullet(self, self.aim)
        return None

    def take_damage(self, amount):
        self.health -= amount
        if self.health <= 0:
            self.alive = False

    def move(self, keys, walls):
        arrow =  Vector2(0, 0)
        if keys[self.controls["up"]] and not(self.rect.top <= 0):
            arrow -= Vector2(0, 1)
        if keys[self.controls["down"]] and not(self.rect.bottom >= Settings.SCREEN_HEIGHT):
            arrow += Vector2(0, 1)
        if keys[self.controls["left"]] and not(self.rect.left <= 0):
            arrow -= Vector2(1, 0)
        if keys[self.controls["right"]] and not(self.rect.right >= Settings.SCREEN_WIDTH):
            arrow += Vector2(1, 0)
        if arrow.length() > 0:
            arrow = arrow.normalize()


        if keys[self.controls["barrel_left"]]:
            self.barrel_angle -= self.barrel_speed
        if keys[self.controls["barrel_right"]]:
            self.barrel_angle += self.barrel_speed
        self.barrel_angle %= 360
        self.aim = Vector2(1, 0).rotate(self.barrel_angle)

        if arrow.length() > 0:
            arrow = arrow.normalize()
            self.target_angle = Vector2(1, 0).angle_to(arrow)




        difference = (self.target_angle - self.hull_angle + 180) % 360 - 180
        if abs(difference) <= self.hull_turn_speed:
            self.hull_angle = self.target_angle
        elif difference > 0:
            self.hull_angle += self.hull_turn_speed
        else:
            self.hull_angle -= self.hull_turn_speed
        drive = Vector2(0, 0)
        if arrow.length() > 0:
            drive = Vector2(1, 0).rotate(self.hull_angle)

        self.pos.x += drive.x * self.speed
        self.rect.center = self.pos
        if rect_touches_wall(self.rect, walls):
            self.pos.x -= drive.x * self.speed
            self.rect.center = self.pos

        self.pos.y += drive.y * self.speed
        self.rect.center = self.pos
        if rect_touches_wall(self.rect, walls):
            self.pos.y -= drive.y * self.speed
            self.rect.center = self.pos 

        screen_rect = pygame.Rect(0, 0, Settings.SCREEN_WIDTH, Settings.SCREEN_HEIGHT)
        clamped = self.rect.clamp(screen_rect)
        if clamped != self.rect:
            self.rect = clamped
            self.pos = Vector2(self.rect.center)    

        


    def draw(self, screen):
        hull = pygame.transform.rotate(self.hull_image, -self.hull_angle)
        screen.blit(hull, hull.get_rect(center=self.rect.center))
        gun = pygame.transform.rotate(self.gun_image, -self.barrel_angle)
        screen.blit(gun, gun.get_rect(center=self.rect.center))