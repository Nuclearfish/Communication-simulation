import math
import sys
import pygame


WIDTH = 960
HEIGHT = 640
FPS = 60

TANK_SIZE = (48, 60)
TANK_SPEED = 3.0
TANK_ROT_SPEED = 2.0
BULLET_SPEED = 7.0
BULLET_LIFETIME = 120
MAX_HEALTH = 5

BG_COLOR = (20, 24, 32)
PANEL_COLOR = (30, 34, 46)
WHITE = (240, 240, 245)
RED = (240, 92, 92)
BLUE = (96, 170, 255)
YELLOW = (255, 220, 90)


class Tank:
    def __init__(self, x, y, color, controls):
        self.x = x
        self.y = y
        self.angle = 0.0
        self.color = color
        self.controls = controls
        self.health = MAX_HEALTH
        self.cooldown = 0

    def update(self, keys, walls):
        move = 0
        rotate = 0
        if keys[self.controls["forward"]]:
            move += 1
        if keys[self.controls["backward"]]:
            move -= 1
        if keys[self.controls["left"]]:
            rotate -= 1
        if keys[self.controls["right"]]:
            rotate += 1

        self.angle = (self.angle + rotate * TANK_ROT_SPEED) % 360
        if move:
            angle_rad = math.radians(self.angle)
            dx = math.sin(angle_rad) * TANK_SPEED * move
            dy = -math.cos(angle_rad) * TANK_SPEED * move
            new_rect = self.get_rect(dx, dy)
            if not any(new_rect.colliderect(wall) for wall in walls):
                self.x += dx
                self.y += dy

        self.x = max(40, min(WIDTH - 40, self.x))
        self.y = max(40, min(HEIGHT - 80, self.y))

        if self.cooldown > 0:
            self.cooldown -= 1

    def can_fire(self, keys):
        return keys[self.controls["fire"]] and self.cooldown == 0

    def fire(self):
        self.cooldown = FPS // 4
        angle_rad = math.radians(self.angle)
        vx = math.sin(angle_rad) * BULLET_SPEED
        vy = -math.cos(angle_rad) * BULLET_SPEED
        spawn_x = self.x + math.sin(angle_rad) * 30
        spawn_y = self.y - math.cos(angle_rad) * 30
        return Bullet(spawn_x, spawn_y, vx, vy, self.color)

    def get_rect(self, dx=0, dy=0):
        rect = pygame.Rect(0, 0, TANK_SIZE[0], TANK_SIZE[1])
        rect.center = (self.x + dx, self.y + dy)
        return rect

    def draw(self, surface):
        base = pygame.Surface(TANK_SIZE, pygame.SRCALPHA)
        pygame.draw.rect(base, self.color, (6, 10, 36, 40), border_radius=8)
        pygame.draw.rect(base, (20, 20, 20), (14, 0, 20, 18), border_radius=6)
        pygame.draw.circle(base, (30, 30, 30), (24, 30), 12)
        turret = pygame.Surface((8, 40), pygame.SRCALPHA)
        pygame.draw.rect(turret, (40, 40, 40), (0, 0, 8, 40), border_radius=4)
        base.blit(turret, (20, -18))
        rotated = pygame.transform.rotate(base, self.angle)
        rect = rotated.get_rect(center=(self.x, self.y))
        surface.blit(rotated, rect.topleft)


class Bullet:
    def __init__(self, x, y, vx, vy, color):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.lifetime = BULLET_LIFETIME

    def update(self, walls):
        self.x += self.vx
        self.y += self.vy
        self.lifetime -= 1
        rect = pygame.Rect(self.x - 4, self.y - 4, 8, 8)
        return any(rect.colliderect(wall) for wall in walls)

    def draw(self, surface):
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), 4)


class Explosion:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        self.radius = 2
        self.alive = True

    def update(self):
        self.radius += 2
        if self.radius > 18:
            self.alive = False

    def draw(self, surface):
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.radius, 2)


def build_walls():
    walls = []
    walls.append(pygame.Rect(220, 120, 60, 220))
    walls.append(pygame.Rect(680, 300, 60, 220))
    walls.append(pygame.Rect(420, 200, 120, 40))
    walls.append(pygame.Rect(320, 420, 160, 40))
    return walls


def draw_ui(surface, font, tanks):
    panel_rect = pygame.Rect(0, HEIGHT - 60, WIDTH, 60)
    pygame.draw.rect(surface, PANEL_COLOR, panel_rect)
    for idx, tank in enumerate(tanks):
        label = f"Player {idx + 1}"
        text = font.render(label, True, WHITE)
        x = 20 + idx * 240
        surface.blit(text, (x, HEIGHT - 48))
        for heart in range(MAX_HEALTH):
            color = tank.color if heart < tank.health else (70, 70, 80)
            pygame.draw.rect(surface, color, (x + 110 + heart * 22, HEIGHT - 42, 18, 18), border_radius=4)


def draw_instructions(surface, font):
    lines = [
        "Player 1: WASD to move, Space to fire",
        "Player 2: Arrow keys to move, Right Ctrl to fire",
        "First to drop enemy health to zero wins.",
    ]
    for idx, line in enumerate(lines):
        text = font.render(line, True, WHITE)
        surface.blit(text, (20, 20 + idx * 24))


def reset_match():
    tank1 = Tank(200, 500, BLUE, {
        "forward": pygame.K_w,
        "backward": pygame.K_s,
        "left": pygame.K_a,
        "right": pygame.K_d,
        "fire": pygame.K_SPACE,
    })
    tank2 = Tank(760, 140, RED, {
        "forward": pygame.K_UP,
        "backward": pygame.K_DOWN,
        "left": pygame.K_LEFT,
        "right": pygame.K_RIGHT,
        "fire": pygame.K_RCTRL,
    })
    return [tank1, tank2]


def main():
    pygame.init()
    pygame.display.set_caption("Tank Battle")
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("arial", 20)
    large_font = pygame.font.SysFont("arial", 32)

    walls = build_walls()
    tanks = reset_match()
    bullets = []
    explosions = []
    winner = None

    running = True
    while running:
        dt = clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN and winner is not None:
                if event.key == pygame.K_RETURN:
                    tanks = reset_match()
                    bullets.clear()
                    explosions.clear()
                    winner = None

        keys = pygame.key.get_pressed()
        if winner is None:
            for tank in tanks:
                tank.update(keys, walls)
                if tank.can_fire(keys):
                    bullets.append(tank.fire())

        for bullet in bullets[:]:
            hit_wall = bullet.update(walls)
            if bullet.lifetime <= 0 or hit_wall:
                bullets.remove(bullet)
                explosions.append(Explosion(bullet.x, bullet.y, YELLOW))
                continue
            for tank in tanks:
                if pygame.Rect(tank.x - 22, tank.y - 26, 44, 52).collidepoint(bullet.x, bullet.y):
                    tank.health -= 1
                    bullets.remove(bullet)
                    explosions.append(Explosion(bullet.x, bullet.y, YELLOW))
                    if tank.health <= 0:
                        winner = "Player 2" if tank is tanks[0] else "Player 1"
                    break

        for explosion in explosions[:]:
            explosion.update()
            if not explosion.alive:
                explosions.remove(explosion)

        screen.fill(BG_COLOR)
        for wall in walls:
            pygame.draw.rect(screen, (70, 80, 90), wall, border_radius=6)
        draw_instructions(screen, font)
        for tank in tanks:
            tank.draw(screen)
        for bullet in bullets:
            bullet.draw(screen)
        for explosion in explosions:
            explosion.draw(screen)
        draw_ui(screen, font, tanks)

        if winner is not None:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 160))
            screen.blit(overlay, (0, 0))
            text = large_font.render(f"{winner} wins!", True, WHITE)
            subtext = font.render("Press Enter to play again", True, WHITE)
            screen.blit(text, (WIDTH / 2 - text.get_width() / 2, HEIGHT / 2 - 40))
            screen.blit(subtext, (WIDTH / 2 - subtext.get_width() / 2, HEIGHT / 2 + 8))

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
