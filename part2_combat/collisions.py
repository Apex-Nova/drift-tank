def bullets_vs_walls(bullets, walls):
    """Destroy bullets that hit live walls and damage destructible walls."""
    for bullet in bullets:
        if not bullet.alive:
            continue

        for wall in walls:
            if not getattr(wall, "alive", True):
                continue

            if bullet.rect.colliderect(wall.rect):
                if getattr(wall, "destructible", False):
                    wall.hit(bullet.damage)

                bullet.alive = False
                break


def bullets_vs_tanks(bullets, tanks, scoreboard=None):
    """Damage tanks hit by bullets and optionally report kills."""
    for bullet in bullets:
        if not bullet.alive:
            continue

        for tank in tanks:
            if tank is bullet.owner:
                continue
            if not getattr(tank, "alive", True):
                continue

            if bullet.rect.colliderect(tank.rect):
                was_alive = getattr(tank, "alive", True)
                tank.take_damage(bullet.damage)
                bullet.alive = False

                if (
                    was_alive
                    and not getattr(tank, "alive", True)
                    and scoreboard is not None
                ):
                    scoreboard.register_kill(bullet.owner, tank)

                break


def rect_touches_wall(rect, walls):
    """Return True if rect overlaps any live wall."""
    return any(
        getattr(wall, "alive", True) and rect.colliderect(wall.rect)
        for wall in walls
    )