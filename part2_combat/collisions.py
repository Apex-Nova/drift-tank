"""Functions that check when bullets, tanks, and walls touch."""


def rect_touches_wall(rect, walls):
    """Kya rect kisi zinda wall ko touch karta hai? True ya False do."""
    return any(
        getattr(wall, "alive", True) and rect.colliderect(wall.rect)
        for wall in walls
    )


def handle_bullet_wall_collisions(bullets, walls):
    """Wall se takrane par bullet hatao; breakable wall ko damage do."""
    for bullet in bullets:
        if not bullet.alive:
            continue

        for wall in walls:
            if not getattr(wall, "alive", True):
                continue
            if not bullet.rect.colliderect(wall.rect):
                continue

            bullet.alive = False
            if getattr(wall, "destructible", False):
                wall.hit(bullet.damage)
            break  # Ek bullet ek hi wall ko hit karegi.


def handle_bullet_tank_collisions(bullets, tanks, scoreboard=None):
    """Tank ko hit hone par damage do aur kill ko scoreboard par bhejo.

    Shooter ko ignore karte hain. Pehli hit ke baad bullet khatam hoti hai.
    """
    for bullet in bullets:
        if not bullet.alive:
            continue

        for tank in tanks:
            if not getattr(tank, "alive", True) or tank is bullet.owner:
                continue
            if not bullet.rect.colliderect(tank.rect):
                continue

            tank.take_damage(bullet.damage)
            bullet.alive = False

            if not tank.alive and scoreboard is not None:
                scoreboard.register_kill(bullet.owner, tank)
            break  # Ek bullet ek hi tank ko damage karegi.


def resolve_collisions(bullets, walls, tanks, scoreboard=None):
    """Pehle wall, phir tank collision check karo.

    Bullet move karne ke baad call karo. Wall peeche ke tank ko bachayegi.
    """
    handle_bullet_wall_collisions(bullets, walls)
    handle_bullet_tank_collisions(bullets, tanks, scoreboard)
