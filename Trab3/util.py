from collections import defaultdict
from collections.abc import Callable
from typing import Any

import pygame


class EventHandler:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._observers = defaultdict(list)
        return cls._instance

    def subscribe(self, event_type: str, callback: Callable[..., None]) -> None:
        if callback not in self._observers[event_type]:
            self._observers[event_type].append(callback)

    def unsubscribe(self, event_type: str, callback: Callable[..., None]) -> None:
        callbacks = self._observers.get(event_type, [])
        if callback in callbacks:
            callbacks.remove(callback)

    def emit(self, event_type: str, **data: Any) -> None:
        for callback in tuple(self._observers.get(event_type, ())):
            callback(**data)

    def notify(self, event_type: str, data: Any = None) -> None:
        for callback in tuple(self._observers.get(event_type, ())):
            callback(data)

    def clear(self) -> None:
        self._observers.clear()


SPAWN_PROJECTILE = "spawn_projectile"
DESTROY_PROJECTILE = "destroy_projectile"
SPAWN_ENEMY = "spawn_enemy"
DESTROY_ENEMY = "destroy_enemy"
ENEMY_HIT = "enemy_hit"
ENEMY_KILLED = "enemy_killed"
PLAYER_HIT = "player_hit"
SPAWN_POWERUP = "spawn_powerup"
POWERUP_COLLECTED = "powerup_collected"
WAVE_STARTED = "wave_started"


def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(value, maximum))


def circle_collision(p1, r1: float, p2, r2: float) -> bool:
    return pygame.Vector2(p1).distance_squared_to(p2) <= (r1 + r2) ** 2


circle_collistiion = circle_collision


def draw_text(surface, text, font, color, position, anchor="topleft"):
    image = font.render(text, True, color)
    rect = image.get_rect()
    setattr(rect, anchor, position)
    surface.blit(image, rect)
    return rect


def colored_sprite(color, size=(32, 32), circle=True):
    sprite = pygame.Surface(size, pygame.SRCALPHA)
    if circle:
        pygame.draw.circle(sprite, color, (size[0] // 2, size[1] // 2), size[0] // 2)
    else:
        sprite.fill(color)
    return sprite
