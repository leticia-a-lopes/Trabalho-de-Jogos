from abc import ABC, abstractmethod

import pygame

from bullet import EnemyProjectile
from util import (
    DESTROY_ENEMY,
    ENEMY_KILLED,
    SPAWN_PROJECTILE,
    EventHandler,
)


ENEMY_STATS = {
    "chaser": {
        "radius": 15,
        "speed": 105,
        "health": 30,
        "damage": 14,
        "score": 100,
        "color": (255, 86, 105),
    },
    "shooter": {
        "radius": 17,
        "speed": 76,
        "health": 45,
        "damage": 12,
        "score": 175,
        "color": (187, 104, 255),
    },
    "tank": {
        "radius": 23,
        "speed": 48,
        "health": 110,
        "damage": 24,
        "score": 300,
        "color": (255, 143, 74),
    },
}


class Enemy:
    def __init__(self, pos, target, kind="chaser", health_scale=1.0):
        stats = ENEMY_STATS[kind]
        self.kind = kind
        self.pos = pygame.Vector2(pos)
        self.target = target
        self.radius = stats["radius"]
        self.speed = stats["speed"]
        self.max_health = round(stats["health"] * health_scale)
        self.health = self.max_health
        self.damage = stats["damage"]
        self.score_value = stats["score"]
        self.color = stats["color"]
        self.alive = True
        self.contact_timer = 0.0
        self.attack_cooldown = 0.6
        self.velocity = pygame.Vector2()
        self.state = ApproachingState(self)

    @property
    def state_name(self):
        return self.state.label

    def update(self, dt):
        if not self.alive:
            return
        self.contact_timer = max(0.0, self.contact_timer - dt)
        self.attack_cooldown = max(0.0, self.attack_cooldown - dt)
        self.state.update(dt)

    def draw(self, screen):
        if self.alive:
            self.state.draw(screen)

    def draw_body(self, screen, color=None):
        color = color or self.color
        if self.kind == "shooter":
            # inimigo atirador em formato de losango
            points = [
                self.pos + pygame.Vector2(0, -self.radius),
                self.pos + pygame.Vector2(self.radius, 0),
                self.pos + pygame.Vector2(0, self.radius),
                self.pos + pygame.Vector2(-self.radius, 0),
            ]
            pygame.draw.polygon(screen, color, points, 3)
            pygame.draw.circle(screen, color, self.pos, 5)
        elif self.kind == "tank":
            # inimigo tanque em formato de quadrado
            rect = pygame.Rect(0, 0, self.radius * 1.6, self.radius * 1.6)
            rect.center = self.pos
            pygame.draw.rect(screen, color, rect, 4, border_radius=4)
            pygame.draw.circle(screen, color, self.pos, 7)
        else:
            # inimigo perseguidor em formato de círculo
            pygame.draw.circle(screen, color, self.pos, self.radius, 3)
            direction = self.target.pos - self.pos
            if direction.length_squared() > 0:
                eye = self.pos + direction.normalize() * 6
                pygame.draw.circle(screen, (255, 226, 229), eye, 4)

        if self.health < self.max_health:
            width = self.radius * 2
            ratio = self.health / self.max_health
            back = pygame.Rect(self.pos.x - width / 2, self.pos.y - self.radius - 10, width, 4)
            pygame.draw.rect(screen, (55, 28, 44), back, border_radius=2)
            pygame.draw.rect(
                screen,
                (102, 238, 146),
                (back.x, back.y, back.width * ratio, back.height),
                border_radius=2,
            )

    def take_damage(self, amount, hit_direction=None):
        if not self.alive:
            return
        self.health -= amount
        if self.health <= 0:
            self.die()
            return
        direction = pygame.Vector2(hit_direction or (0, 0))
        if direction.length_squared() > 0:
            self.pos += direction.normalize() * 7
        self.change_state(StunnedState(self))

    def die(self):
        if not self.alive:
            return
        self.alive = False
        bus = EventHandler()
        bus.emit(ENEMY_KILLED, enemy=self, position=self.pos.copy())
        bus.emit(DESTROY_ENEMY, enemy=self)

    def change_state(self, new_state):
        if isinstance(new_state, type):
            new_state = new_state(self)
        self.state.exit()
        self.state = new_state
        self.state.enter()


class EnemyState(ABC):
    label = "BASE"

    def __init__(self, enemy):
        self.enemy = enemy

    def enter(self):
        pass

    def exit(self):
        pass

    @abstractmethod
    def update(self, dt):
        pass

    def draw(self, screen):
        self.enemy.draw_body(screen)


class ApproachingState(EnemyState):
    label = "APROXIMANDO"

    def update(self, dt):
        enemy = self.enemy
        to_player = enemy.target.pos - enemy.pos
        distance = to_player.length()
        if distance == 0:
            return

        if enemy.kind == "shooter" and distance < 270 and enemy.attack_cooldown <= 0:
            enemy.change_state(AimingState(enemy))
            return

        speed_factor = 1.0
        if enemy.kind == "shooter" and distance < 190:
            speed_factor = -0.5
        enemy.velocity = to_player.normalize() * enemy.speed * speed_factor
        enemy.pos += enemy.velocity * dt


class AimingState(EnemyState):
    label = "MIRANDO"

    def __init__(self, enemy):
        super().__init__(enemy)
        self.remaining = 0.85
        self.aim_direction = pygame.Vector2(1, 0)

    def update(self, dt):
        enemy = self.enemy
        aim = enemy.target.pos - enemy.pos
        if aim.length_squared() > 0:
            self.aim_direction = aim.normalize()
        self.remaining -= dt
        if self.remaining <= 0:
            projectile = EnemyProjectile(
                enemy.pos + self.aim_direction * (enemy.radius + 7),
                self.aim_direction,
                damage=enemy.damage,
            )
            EventHandler().emit(SPAWN_PROJECTILE, projectile=projectile)
            enemy.attack_cooldown = 1.2
            enemy.change_state(RecoveringState(enemy))

    def draw(self, screen):
        self.enemy.draw_body(screen, (255, 198, 239))
        end = self.enemy.pos + self.aim_direction * 115
        pygame.draw.line(screen, (255, 92, 151), self.enemy.pos, end, 1)
        progress = 1.0 - max(0.0, self.remaining) / 0.85
        pygame.draw.circle(
            screen,
            (255, 216, 87),
            self.enemy.pos,
            int(self.enemy.radius + 6 + progress * 8),
            2,
        )


class RecoveringState(EnemyState):
    label = "RECARREGANDO"

    def __init__(self, enemy):
        super().__init__(enemy)
        self.remaining = 0.35

    def update(self, dt):
        self.remaining -= dt
        if self.remaining <= 0:
            self.enemy.change_state(ApproachingState(self.enemy))


class StunnedState(EnemyState):
    label = "ATORDOADO"

    def __init__(self, enemy, duration=0.16):
        super().__init__(enemy)
        self.remaining = duration

    def update(self, dt):
        self.remaining -= dt
        self.enemy.pos -= self.enemy.velocity * dt * 0.35
        if self.remaining <= 0:
            self.enemy.change_state(ApproachingState(self.enemy))

    def draw(self, screen):
        self.enemy.draw_body(screen, (229, 250, 255))
        y = self.enemy.pos.y - self.enemy.radius - 8
        pygame.draw.circle(screen, (255, 216, 87), (self.enemy.pos.x - 5, y), 2)
        pygame.draw.circle(screen, (255, 216, 87), (self.enemy.pos.x + 5, y - 2), 2)
