from abc import ABC, abstractmethod
from pathlib import Path
import random
import pygame


class obj(ABC):
    def __init__(self, x, y, sprites):
        self.x = x
        self.y = y
        self.sprites = sprites

    def draw(self, screen):
        for sprite in self.sprites:
            screen.blit(sprite, (self.x, self.y))

    @abstractmethod
    def update(self, dt):
        pass


class Cell(obj):
    def __init__(self, x, y, sprites, cell_size):
        super().__init__(x, y, sprites)
        self.cell_size = cell_size

    def draw(self, screen):
        # célula
        pygame.draw.rect(
            screen,
            (25, 25, 25),
            (self.x, self.y, self.cell_size, self.cell_size)
        )

        # grade
        pygame.draw.rect(
            screen,
            (15, 15, 15),
            (self.x, self.y, self.cell_size, self.cell_size),
            1
        )

    def update(self, dt):
        return


class Grid(obj):
    def __init__(
        self,
        x,
        y,
        sprites,
        grid_size,
        cell_size=28
    ):
        super().__init__(x, y, sprites)

        self.rows = grid_size[0]
        self.cols = grid_size[1]
        self.cell_size = cell_size

        self.width = self.cols * self.cell_size
        self.height = self.rows * self.cell_size

        self.font = pygame.font.Font(None, 18)
        self.game_over_font = pygame.font.Font(None, 48)

        self.cells = []

        for row in range(self.rows):
            linha = []

            for col in range(self.cols):
                cell_x = self.x + col * self.cell_size
                cell_y = self.y + row * self.cell_size

                cell = Cell(
                    cell_x,
                    cell_y,
                    [],
                    self.cell_size
                )

                linha.append(cell)

            self.cells.append(linha)

        # sprites
        sprite_path = (
            Path(__file__).parent
            / "images"
            / "snake.png"
        )

        self.sprite_sheet = pygame.image.load(
            str(sprite_path)
        ).convert()

        self.sprite_sheet.set_colorkey((0, 0, 0))

        self.head_sprites = {
            "UP": self.get_sprite(1, 3),
            "LEFT": self.get_sprite(2, 3),
            "DOWN": self.get_sprite(3, 3),
            "RIGHT": self.get_sprite(4, 3),
        }

        self.body_sprite = self.get_sprite(5, 3)

        self.food_sprite = self.get_sprite(6, 0)

        self.restart()

    def get_sprite(self, column, row):

        sprite_size = 8

        rect = pygame.Rect(
            column * sprite_size,
            row * sprite_size,
            sprite_size,
            sprite_size
        )

        sprite = self.sprite_sheet.subsurface(rect).copy()

        sprite.set_colorkey((0, 0, 0))

        sprite = pygame.transform.scale(
            sprite,
            (self.cell_size, self.cell_size)
        )

        return sprite

    def restart(self):
        center_col = self.cols // 2
        center_row = self.rows // 2

        self.snake = [
            (center_col, center_row),
            (center_col - 1, center_row),
            (center_col - 2, center_row),
        ]

        self.direction = (1, 0)
        self.next_direction = (1, 0)

        self.direction_name = "RIGHT"

        self.score = 0
        self.game_over = False

        # movimento da cobre
        self.move_timer = 0
        self.move_interval = 0.16

        self.spawn_food()

    def spawn_food(self):
        empty_cells = []

        for row in range(self.rows):
            for col in range(self.cols):
                position = (col, row)

                if position not in self.snake:
                    empty_cells.append(position)

        if empty_cells:
            self.food = random.choice(empty_cells)

    def set_direction(self, dx, dy, name):
        # cobra n volta para trás
        opposite = (-self.direction[0], -self.direction[1])

        if (dx, dy) == opposite:
            return

        self.next_direction = (dx, dy)
        self.direction_name = name

    def handle_mouse(self, mouse_position):

        mouse_x, mouse_y = mouse_position

        # ignora clicks fora da grade
        if not (
            self.x <= mouse_x < self.x + self.width
            and
            self.y <= mouse_y < self.y + self.height
        ):
            return

        clicked_col = (mouse_x - self.x) // self.cell_size
        clicked_row = (mouse_y - self.y) // self.cell_size

        head_col, head_row = self.snake[0]

        difference_x = clicked_col - head_col
        difference_y = clicked_row - head_row

        # decide direção da cobra de acordo com a direção do click
        if abs(difference_x) > abs(difference_y):
            if difference_x > 0:
                self.set_direction(1, 0, "RIGHT")

            elif difference_x < 0:
                self.set_direction(-1, 0, "LEFT")

        else:
            if difference_y > 0:
                self.set_direction(0, 1, "DOWN")

            elif difference_y < 0:
                self.set_direction(0, -1, "UP")

    def move_snake(self):
        self.direction = self.next_direction

        head_col, head_row = self.snake[0]

        dx, dy = self.direction

        new_head = (
            head_col + dx,
            head_row + dy
        )

        new_col, new_row = new_head

        # colisão
        if (
            new_col < 0
            or new_col >= self.cols
            or new_row < 0
            or new_row >= self.rows
        ):
            self.game_over = True
            return

        ate_food = new_head == self.food

        # se n comer, a cauda continua se movendo
        if ate_food:
            body_to_check = self.snake
        else:
            body_to_check = self.snake[:-1]

        # colisão c o próprio corpo
        if new_head in body_to_check:
            self.game_over = True
            return

        self.snake.insert(0, new_head)

        if ate_food:
            self.score += 1
            self.spawn_food()

        else:
            self.snake.pop()

    def update(self, dt):

        if self.game_over:
            return

        # movimento
        self.move_timer += dt

        if self.move_timer >= self.move_interval:
            self.move_timer = 0
            self.move_snake()

    def grid_to_screen(self, position):
        col, row = position

        screen_x = self.x + col * self.cell_size
        screen_y = self.y + row * self.cell_size

        return screen_x, screen_y

    def draw(self, screen):
        for row in self.cells:
            for cell in row:
                cell.draw(screen)

        food_x, food_y = self.grid_to_screen(self.food)

        screen.blit(
            self.food_sprite,
            (food_x, food_y)
        )

        for position in self.snake[1:]:
            body_x, body_y = self.grid_to_screen(position)

            screen.blit(
                self.body_sprite,
                (body_x, body_y)
            )

        head_x, head_y = self.grid_to_screen(
            self.snake[0]
        )

        head_sprite = self.head_sprites[
            self.direction_name
        ]

        screen.blit(
            head_sprite,
            (head_x, head_y)
        )

        score_text = self.font.render(
            f"Pontos: {self.score}",
            True,
            (240, 240, 240)
        )

        screen.blit(
            score_text,
            (self.x, self.y - 27)
        )

        if self.game_over:
            overlay = pygame.Surface(
                (self.width, self.height),
                pygame.SRCALPHA
            )

            screen.blit(
                overlay,
                (self.x, self.y)
    )

            game_over_text = self.game_over_font.render(
                "GAME OVER",
                True,
                (255, 255, 255)
            )   

            game_over_rect = game_over_text.get_rect(
                center=(
                    self.x + self.width // 2,
                    self.y + self.height // 2 - 20
                )
            )

            screen.blit(
                game_over_text,
                game_over_rect
            )