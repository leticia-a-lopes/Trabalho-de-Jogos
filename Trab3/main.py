import math
import random

import pygame

from enemy import Enemy
from player import Player
from powerup import POWERUP_INFO, PowerUp
from settings import (
    BACKGROUND,
    CYAN,
    FPS,
    HEIGHT,
    PINK,
    TITLE,
    WHITE,
    WIDTH,
    YELLOW,
)
from util import (
    DESTROY_ENEMY,
    DESTROY_PROJECTILE,
    ENEMY_HIT,
    ENEMY_KILLED,
    PLAYER_HIT,
    POWERUP_COLLECTED,
    SPAWN_ENEMY,
    SPAWN_POWERUP,
    SPAWN_PROJECTILE,
    WAVE_STARTED,
    EventHandler,
    circle_collision,
)


ARENA = pygame.Rect(18, 18, WIDTH - 36, HEIGHT - 36)


class Particle:
    def __init__(self, pos, color, velocity=None, lifetime=0.45, radius=3):
        self.pos = pygame.Vector2(pos)
        angle = random.uniform(0, math.tau)
        speed = random.uniform(45, 170)
        self.velocity = velocity or pygame.Vector2(math.cos(angle), math.sin(angle)) * speed
        self.color = color
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.radius = radius

    def update(self, dt):
        self.lifetime -= dt
        self.pos += self.velocity * dt
        self.velocity *= max(0.0, 1.0 - dt * 4)

    def draw(self, screen):
        ratio = max(0.0, self.lifetime / self.max_lifetime)
        color = tuple(int(channel * ratio) for channel in self.color)
        pygame.draw.circle(screen, color, self.pos, max(1, int(self.radius * ratio)))


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption(f"{TITLE} — Estados & Eventos")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.mouse.set_visible(False)
        self.clock = pygame.time.Clock()
        self.font_small = pygame.font.Font(None, 16)
        self.font_medium = pygame.font.Font(None, 24)
        self.font_large = pygame.font.Font(None, 52)
        self.bus = EventHandler()
        self.running = True
        self.paused = False
        self.reset()

    def reset(self):
        self.paused = False
        self.bus.clear()
        self._subscribe_events()
        self.player = Player(ARENA.center, ARENA)
        self.enemies = []
        self.projectiles = []
        self.powerups = []
        self.particles = []
        self.score = 0
        self.kills = 0
        self.wave = 0
        self.pending_enemies = 0
        self.spawn_timer = 0.0
        self.intermission = 0.35
        self.banner = "PREPARE-SE"
        self.banner_timer = 1.3
        self.shake = 0.0
        self.game_over = False

    def _subscribe_events(self):
        self.bus.subscribe(SPAWN_PROJECTILE, self.on_spawn_projectile)
        self.bus.subscribe(DESTROY_PROJECTILE, self.on_destroy_projectile)
        self.bus.subscribe(SPAWN_ENEMY, self.on_spawn_enemy)
        self.bus.subscribe(DESTROY_ENEMY, self.on_destroy_enemy)
        self.bus.subscribe(ENEMY_HIT, self.on_enemy_hit)
        self.bus.subscribe(ENEMY_KILLED, self.on_enemy_killed)
        self.bus.subscribe(PLAYER_HIT, self.on_player_hit)
        self.bus.subscribe(SPAWN_POWERUP, self.on_spawn_powerup)
        self.bus.subscribe(POWERUP_COLLECTED, self.on_powerup_collected)
        self.bus.subscribe(WAVE_STARTED, self.on_wave_started)

    def on_spawn_projectile(self, projectile):
        self.projectiles.append(projectile)
        color = CYAN if projectile.owner == "player" else PINK
        self._burst(projectile.pos, color, amount=3, radius=2)

    def on_destroy_projectile(self, projectile):
        if projectile in self.projectiles:
            self.projectiles.remove(projectile)

    def on_spawn_enemy(self, position, kind):
        health_scale = 1.0 + max(0, self.wave - 1) * 0.075
        self.enemies.append(Enemy(position, self.player, kind, health_scale))

    def on_destroy_enemy(self, enemy):
        if enemy in self.enemies:
            self.enemies.remove(enemy)

    def on_enemy_hit(self, enemy, damage, direction):
        enemy.take_damage(damage, direction)

    def on_enemy_killed(self, enemy, position):
        self.score += enemy.score_value
        self.kills += 1
        self.shake = max(self.shake, 0.12)
        self._burst(position, enemy.color, amount=13, radius=4)

        if self.kills % 7 == 0 or random.random() < 0.10:
            if self.player.health <= 45 and random.random() < 0.65:
                kind = "heal"
            else:
                kind = "rapid_fire"
            self.bus.emit(SPAWN_POWERUP, position=position, kind=kind)

    def on_player_hit(self, amount, source=None):
        old_health = self.player.health
        self.player.take_damage(amount, source)
        if self.player.health < old_health:
            self.shake = 0.28
            self._burst(self.player.pos, PINK, amount=11, radius=4)

    def on_spawn_powerup(self, position, kind):
        self.powerups.append(PowerUp(position, kind))

    def on_powerup_collected(self, powerup):
        if powerup not in self.powerups:
            return
        self.powerups.remove(powerup)
        powerup.alive = False
        self.player.activate_powerup(powerup.kind)
        self._burst(powerup.pos, POWERUP_INFO[powerup.kind]["color"], 14, radius=4)

    def on_wave_started(self, wave):
        self.banner = f"ONDA {wave}"
        self.banner_timer = 1.45

    def run(self):
        while self.running:
            dt = min(self.clock.tick(FPS) / 1000.0, 0.05)
            self.handle_input()
            if not self.paused and not self.game_over:
                self.update(dt)
            self.draw()
        pygame.quit()

    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.paused = not self.paused
                elif event.key == pygame.K_p:
                    self.paused = not self.paused
                elif event.key == pygame.K_r and self.game_over:
                    self.reset()

        keys = pygame.key.get_pressed()
        movement = pygame.Vector2(
            int(keys[pygame.K_d]) - int(keys[pygame.K_a]),
            int(keys[pygame.K_s]) - int(keys[pygame.K_w]),
        )
        stick = pygame.Vector2(
            int(keys[pygame.K_RIGHT]) - int(keys[pygame.K_LEFT]),
            int(keys[pygame.K_DOWN]) - int(keys[pygame.K_UP]),
        )
        if stick.length_squared() > 0:
            aim_position = self.player.pos + stick.normalize() * 200
        else:
            aim_position = pygame.mouse.get_pos()
        firing = (
            bool(stick.length_squared())
            or pygame.mouse.get_pressed()[0]
            or keys[pygame.K_SPACE]
        )
        self.player.set_input(movement, aim_position, firing and not self.paused)

    def update(self, dt):
        self.banner_timer = max(0.0, self.banner_timer - dt)
        self.shake = max(0.0, self.shake - dt)

        self._update_wave(dt)
        self.player.update(dt)
        for enemy in tuple(self.enemies):
            enemy.update(dt)
        for projectile in tuple(self.projectiles):
            projectile.update(dt)
        for powerup in tuple(self.powerups):
            powerup.update(dt)
            if not powerup.alive and powerup in self.powerups:
                self.powerups.remove(powerup)
        for particle in tuple(self.particles):
            particle.update(dt)
            if particle.lifetime <= 0:
                self.particles.remove(particle)

        self._separate_enemies()
        self._check_collisions()
        if not self.player.alive:
            self.shake = 0.0
            self.game_over = True

    def _update_wave(self, dt):
        if self.pending_enemies > 0:
            self.spawn_timer -= dt
            if self.spawn_timer <= 0:
                self.bus.emit(
                    SPAWN_ENEMY,
                    position=self._random_edge_position(),
                    kind=self._choose_enemy_kind(),
                )
                self.pending_enemies -= 1
                self.spawn_timer = max(0.22, 0.72 - self.wave * 0.035)
        elif not self.enemies:
            self.intermission -= dt
            if self.intermission <= 0:
                self._start_wave()

    def _start_wave(self):
        self.wave += 1
        self.pending_enemies = 4 + self.wave * 2
        self.spawn_timer = 0.0
        self.intermission = 2.5
        self.bus.emit(WAVE_STARTED, wave=self.wave)

    def _choose_enemy_kind(self):
        roll = random.random()
        if self.wave >= 4 and roll < min(0.08 + self.wave * 0.012, 0.22):
            return "tank"
        if self.wave >= 2 and roll < min(0.28 + self.wave * 0.015, 0.48):
            return "shooter"
        return "chaser"

    def _random_edge_position(self):
        margin = 30
        side = random.randrange(4)
        if side == 0:
            return random.randrange(40, WIDTH - 40), -margin
        if side == 1:
            return WIDTH + margin, random.randrange(40, HEIGHT - 40)
        if side == 2:
            return random.randrange(40, WIDTH - 40), HEIGHT + margin
        return -margin, random.randrange(40, HEIGHT - 40)

    def _check_collisions(self):
        for projectile in tuple(self.projectiles):
            if not projectile.alive:
                continue
            if projectile.owner == "player":
                for enemy in tuple(self.enemies):
                    if circle_collision(projectile.pos, projectile.radius, enemy.pos, enemy.radius):
                        self.bus.emit(
                            ENEMY_HIT,
                            enemy=enemy,
                            damage=projectile.damage,
                            direction=projectile.velocity,
                        )
                        projectile.destroy()
                        break
            elif circle_collision(
                projectile.pos,
                projectile.radius,
                self.player.pos,
                self.player.radius,
            ):
                self.bus.emit(PLAYER_HIT, amount=projectile.damage, source=projectile)
                projectile.destroy()

        for enemy in tuple(self.enemies):
            touching_player = circle_collision(
                enemy.pos,
                enemy.radius,
                self.player.pos,
                self.player.radius,
            )
            if touching_player:
                if enemy.contact_timer <= 0:
                    enemy.contact_timer = 0.7
                    self.bus.emit(PLAYER_HIT, amount=enemy.damage, source=enemy)
                self._separate_enemy_from_player(enemy)

        for powerup in tuple(self.powerups):
            if circle_collision(
                powerup.pos, powerup.radius, self.player.pos, self.player.radius
            ):
                self.bus.emit(POWERUP_COLLECTED, powerup=powerup)

    def _separate_enemies(self):
        for index, enemy in enumerate(self.enemies):
            for other in self.enemies[index + 1 :]:
                offset = enemy.pos - other.pos
                minimum = enemy.radius + other.radius + 3
                distance_sq = offset.length_squared()
                if 0 < distance_sq < minimum * minimum:
                    push = offset.normalize() * 0.7
                    enemy.pos += push
                    other.pos -= push

    def _separate_enemy_from_player(self, enemy):
        offset = enemy.pos - self.player.pos
        distance = offset.length()
        if distance == 0:
            if enemy.velocity.length_squared() > 0:
                direction = -enemy.velocity.normalize()
            else:
                direction = pygame.Vector2(1, 0)
        else:
            direction = offset / distance

        minimum_distance = enemy.radius + self.player.radius + 2
        if distance < minimum_distance:
            enemy.pos += direction * (minimum_distance - distance)

    def _burst(self, position, color, amount=8, radius=3):
        for _ in range(amount):
            self.particles.append(Particle(position, color, radius=radius))

    def draw(self):
        if self.game_over:
            self._draw_game_over()
            pygame.display.flip()
            return

        self.screen.fill(BACKGROUND)
        offset = pygame.Vector2()
        if self.shake > 0:
            offset.xy = random.randint(-4, 4), random.randint(-4, 4)

        world = pygame.Surface((WIDTH, HEIGHT))
        world.fill(BACKGROUND)
        for powerup in self.powerups:
            powerup.draw(world, self.font_small)
        for projectile in self.projectiles:
            projectile.draw(world)
        for enemy in self.enemies:
            enemy.draw(world)
            self._text(
                world,
                enemy.state_name,
                self.font_small,
                WHITE,
                (enemy.pos.x, enemy.pos.y + enemy.radius + 9),
                "midtop",
            )
        self.player.draw(world)
        for particle in self.particles:
            particle.draw(world)
        self.screen.blit(world, offset)

        self._draw_hud()
        if self.paused:
            self._draw_overlay("PAUSADO", "P ou ESC para continuar")
        pygame.display.flip()

    def _draw_hud(self):
        health_ratio = self.player.health / self.player.max_health
        pygame.draw.rect(self.screen, (39, 25, 42), (30, 28, 224, 18), border_radius=7)
        pygame.draw.rect(
            self.screen,
            (102, 238, 146) if health_ratio > 0.35 else PINK,
            (30, 28, 224 * health_ratio, 18),
            border_radius=7,
        )
        self._text(
            self.screen,
            f"VIDA {self.player.health:03d}",
            self.font_small,
            WHITE,
            (142, 37),
            "center",
        )
        self._text(self.screen, f"PONTOS  {self.score:06d}", self.font_medium, WHITE, (30, 56))
        self._text(
            self.screen,
            f"ONDA {self.wave}   RESTAM {len(self.enemies) + self.pending_enemies}",
            self.font_medium,
            WHITE,
            (WIDTH - 30, 28),
            "topright",
        )

        state_color = YELLOW if self.player.state_name == "TIRO RÁPIDO" else CYAN
        if self.player.state_name == "INVENCÍVEL":
            state_color = WHITE
        self._text(
            self.screen,
            f"ESTADO: {self.player.state_name}",
            self.font_small,
            state_color,
            (WIDTH - 30, 62),
            "topright",
        )

        if self.banner_timer > 0:
            self._text(
                self.screen,
                self.banner,
                self.font_large,
                CYAN,
                (WIDTH / 2, 100),
                "midtop",
            )
        mouse = pygame.Vector2(pygame.mouse.get_pos())
        pygame.draw.circle(self.screen, CYAN, mouse, 9, 1)
        pygame.draw.line(self.screen, CYAN, mouse - (13, 0), mouse - (5, 0), 1)
        pygame.draw.line(self.screen, CYAN, mouse + (5, 0), mouse + (13, 0), 1)
        pygame.draw.line(self.screen, CYAN, mouse - (0, 13), mouse - (0, 5), 1)
        pygame.draw.line(self.screen, CYAN, mouse + (0, 5), mouse + (0, 13), 1)

    def _draw_game_over(self):
        self.screen.fill((0, 0, 0))
        self._text(
            self.screen,
            "FIM DE JOGO",
            self.font_large,
            PINK,
            (WIDTH / 2, HEIGHT / 2 - 70),
            "center",
        )
        self._text(
            self.screen,
            f"Pontos: {self.score}",
            self.font_medium,
            WHITE,
            (WIDTH / 2, HEIGHT / 2),
            "center",
        )
        self._text(
            self.screen,
            f"Onda: {self.wave}   Eliminações: {self.kills}",
            self.font_small,
            WHITE,
            (WIDTH / 2, HEIGHT / 2 + 38),
            "center",
        )
        self._text(
            self.screen,
            "R para reiniciar",
            self.font_small,
            WHITE,
            (WIDTH / 2, HEIGHT / 2 + 85),
            "center",
        )

    def _draw_overlay(self, title, subtitle):
        veil = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        veil.fill((3, 6, 15, 205))
        self.screen.blit(veil, (0, 0))
        self._text(
            self.screen,
            title,
            self.font_large,
            CYAN,
            (WIDTH / 2, HEIGHT / 2 - 45),
            "center",
        )
        self._text(
            self.screen,
            subtitle,
            self.font_medium,
            WHITE,
            (WIDTH / 2, HEIGHT / 2 + 28),
            "center",
        )

    @staticmethod
    def _text(surface, text, font, color, position, anchor="topleft"):
        image = font.render(str(text), True, color)
        rect = image.get_rect()
        setattr(rect, anchor, position)
        surface.blit(image, rect)


if __name__ == "__main__":
    Game().run()
