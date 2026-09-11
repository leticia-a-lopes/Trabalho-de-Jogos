import pygame

from settings import ENEMY_BULLET_SPEED, PLAYER_BULLET_SPEED, PROJECTILE_LIFETIME
from util import DESTROY_PROJECTILE, EventHandler


class Projectile:
    def __init__(
        self,
        position,
        direction,
        speed,
        owner,
        damage,
        color,
        radius=5,
        lifetime=PROJECTILE_LIFETIME,
    ):
        self.pos = pygame.Vector2(position)
        self.direction = pygame.Vector2(direction)
        if self.direction.length_squared() == 0:
            self.direction.update(1, 0)
        self.direction.normalize_ip()
        self.velocity = self.direction * speed
        self.owner = owner
        self.damage = damage
        self.color = color
        self.radius = radius
        self.lifetime = lifetime
        self.alive = True
        self.trail = []

    def update(self, dt):
        if not self.alive:
            return
        self.trail.append(self.pos.copy())
        if len(self.trail) > 5:
            self.trail.pop(0)
        self.pos += self.velocity * dt
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.destroy()

    def draw(self, screen):
        if not self.alive:
            return
        for index, point in enumerate(self.trail):
            alpha = (index + 1) / max(1, len(self.trail))
            radius = max(1, int(self.radius * alpha * 0.7))
            faded = tuple(int(channel * alpha * 0.45) for channel in self.color)
            pygame.draw.circle(screen, faded, point, radius)
        pygame.draw.circle(screen, self.color, self.pos, self.radius)
        pygame.draw.circle(screen, (255, 255, 255), self.pos, max(1, self.radius // 2))

    def destroy(self):
        if self.alive:
            self.alive = False
            EventHandler().emit(DESTROY_PROJECTILE, projectile=self)


class PlayerProjectile(Projectile):
    def __init__(self, position, direction, damage=20):
        super().__init__(
            position=position,
            direction=direction,
            speed=PLAYER_BULLET_SPEED,
            owner="player",
            damage=damage,
            color=(92, 244, 255),
            radius=5,
        )


class EnemyProjectile(Projectile):
    def __init__(self, position, direction, damage=12):
        super().__init__(
            position=position,
            direction=direction,
            speed=ENEMY_BULLET_SPEED,
            owner="enemy",
            damage=damage,
            color=(255, 92, 151),
            radius=6,
            lifetime=3.5,
        )
