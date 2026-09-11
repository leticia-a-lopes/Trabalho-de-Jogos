import math
from abc import ABC

import pygame

from bullet import PlayerProjectile
from settings import (
    CYAN,
    HEIGHT,
    INVINCIBLE_DURATION,
    PLAYER_FIRE_DELAY,
    PLAYER_MAX_HEALTH,
    PLAYER_RADIUS,
    PLAYER_SPEED,
    RAPID_FIRE_DELAY,
    RAPID_FIRE_DURATION,
    WIDTH,
    YELLOW,
)
from util import SPAWN_PROJECTILE, EventHandler, clamp


class Player:
    radius = PLAYER_RADIUS
    speed = PLAYER_SPEED
    max_health = PLAYER_MAX_HEALTH

    def __init__(self, pos, bounds=None):
        self.pos = pygame.Vector2(pos)
        self.bounds = bounds or pygame.Rect(0, 0, WIDTH, HEIGHT)
        self.health = self.max_health
        self.alive = True
        self.fire_timer = 0.0
        self.move_input = pygame.Vector2()
        self.aim_direction = pygame.Vector2(1, 0)
        self.is_firing = False
        self.state = NormalState(self)

    @property
    def state_name(self):
        return self.state.label

    def set_input(self, movement, aim_position, firing):
        self.move_input = pygame.Vector2(movement)
        aim = pygame.Vector2(aim_position) - self.pos
        if aim.length_squared() > 0:
            self.aim_direction = aim.normalize()
        self.is_firing = firing

    def update(self, dt):
        if not self.alive:
            return
        self.fire_timer = max(0.0, self.fire_timer - dt)

        movement = self.move_input
        if movement.length_squared() > 1:
            movement = movement.normalize()
        self.pos += movement * self.speed * dt
        self.pos.x = clamp(
            self.pos.x,
            self.bounds.left + self.radius,
            self.bounds.right - self.radius,
        )
        self.pos.y = clamp(
            self.pos.y,
            self.bounds.top + self.radius,
            self.bounds.bottom - self.radius,
        )

        self.state.update(dt)
        if self.is_firing and self.fire_timer <= 0:
            self.shoot()

    def shoot(self):
        projectile = PlayerProjectile(
            self.pos + self.aim_direction * (self.radius + 8),
            self.aim_direction,
        )
        EventHandler().emit(SPAWN_PROJECTILE, projectile=projectile)
        self.fire_timer = self.state.fire_delay

    def draw(self, screen):
        self.state.draw(screen)

    def draw_ship(self, screen, color, visible=True):
        if not visible:
            return
        # jogador em formato de triângulo
        forward = self.aim_direction
        side = pygame.Vector2(-forward.y, forward.x)
        nose = self.pos + forward * 24
        left = self.pos - forward * 13 + side * 14
        right = self.pos - forward * 13 - side * 14
        pygame.draw.polygon(screen, (12, 18, 33), (nose, left, right))
        pygame.draw.polygon(screen, color, (nose, left, right), 3)
        pygame.draw.circle(screen, (229, 250, 255), self.pos, 6)

    def take_damage(self, amount, source=None):
        if self.alive:
            self.state.take_damage(amount, source)

    def apply_damage(self, amount):
        self.health = max(0, self.health - amount)
        if self.health == 0:
            self.alive = False

    def heal(self, amount):
        self.health = min(self.max_health, self.health + amount)

    def activate_powerup(self, kind):
        if kind == "rapid_fire":
            rapid_state = RapidFireState(self)
            if isinstance(self.state, InvincibleState):
                self.state.resume_state = rapid_state
            else:
                self.change_state(rapid_state)
        elif kind == "heal":
            self.heal(30)

    def change_state(self, new_state):
        if isinstance(new_state, type):
            new_state = new_state(self)
        self.state.exit()
        self.state = new_state
        self.state.enter()

    def action_1(self):
        if self.fire_timer <= 0:
            self.shoot()

    def action_2(self):
        self.activate_powerup("rapid_fire")


class PlayerState(ABC):
    label = "NORMAL"
    color = CYAN
    fire_delay = PLAYER_FIRE_DELAY

    def __init__(self, player):
        self.player = player

    def enter(self):
        pass

    def exit(self):
        pass

    def update(self, dt):
        pass

    def draw(self, screen):
        self.player.draw_ship(screen, self.color)

    def take_damage(self, amount, source=None):
        self.player.apply_damage(amount)
        if self.player.alive:
            self.player.change_state(InvincibleState(self.player, self))


class NormalState(PlayerState):
    label = "NORMAL"


class RapidFireState(PlayerState):
    label = "TIRO RÁPIDO"
    color = YELLOW
    fire_delay = RAPID_FIRE_DELAY

    def __init__(self, player, duration=RAPID_FIRE_DURATION):
        super().__init__(player)
        self.remaining = duration

    def update(self, dt):
        self.remaining -= dt
        if self.remaining <= 0:
            self.player.change_state(NormalState(self.player))

    def draw(self, screen):
        pulse = 22 + int(3 * abs(math.sin(self.remaining * 8)))
        pygame.draw.circle(screen, (110, 81, 24), self.player.pos, pulse, 2)
        super().draw(screen)


class InvincibleState(PlayerState):
    label = "INVENCÍVEL"
    color = (255, 255, 255)

    def __init__(self, player, resume_state=None):
        super().__init__(player)
        self.remaining = INVINCIBLE_DURATION
        self.resume_state = resume_state or NormalState(player)

    @property
    def fire_delay(self):
        return self.resume_state.fire_delay

    def update(self, dt):
        self.remaining -= dt
        if self.remaining <= 0:
            self.player.change_state(self.resume_state)

    def draw(self, screen):
        visible = int(self.remaining * 14) % 2 == 0
        pygame.draw.circle(screen, (125, 225, 255), self.player.pos, 25, 2)
        self.player.draw_ship(screen, self.color, visible)

    def take_damage(self, amount, source=None):
        return


ExampleState = NormalState
