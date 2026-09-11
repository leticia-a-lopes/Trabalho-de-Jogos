import math

import pygame


POWERUP_INFO = {
    "rapid_fire": {
        "color": (255, 216, 87),
        "letter": "R",
        "label": "TIRO RÁPIDO",
    },
    "heal": {
        "color": (102, 238, 146),
        "letter": "+",
        "label": "+30 VIDA",
    },
}


class PowerUp:
    radius = 13

    def __init__(self, pos, kind="rapid_fire"):
        self.pos = pygame.Vector2(pos)
        self.kind = kind
        self.lifetime = 10.0
        self.elapsed = 0.0
        self.alive = True

    def update(self, dt):
        self.elapsed += dt
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.alive = False

    def draw(self, screen, font):
        info = POWERUP_INFO[self.kind]
        bob = math.sin(self.elapsed * 5) * 3
        center = self.pos + pygame.Vector2(0, bob)
        pulse = int(3 + (math.sin(self.elapsed * 7) + 1) * 2)
        pygame.draw.circle(screen, info["color"], center, self.radius + pulse, 1)
        pygame.draw.circle(screen, (18, 25, 44), center, self.radius)
        pygame.draw.circle(screen, info["color"], center, self.radius, 2)
        glyph = font.render(info["letter"], True, info["color"])
        screen.blit(glyph, glyph.get_rect(center=center))
