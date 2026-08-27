import sys
import pygame

from grid import Grid


pygame.init()
pygame.font.init()


WIDTH = 800; HEIGHT = 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))


clock = pygame.time.Clock()

grid_size = (18, 24)
cell_size = 28

grid_width = grid_size[1] * cell_size
grid_height = grid_size[0] * cell_size

grid_x = (WIDTH - grid_width) // 2
grid_y = (HEIGHT - grid_height) // 2 + 15

grid = Grid(
    grid_x,
    grid_y,
    [],
    grid_size,
    cell_size
)

objects = [grid]

while True:
    # tempo entre um frame e outro
    dt = clock.tick(60) / 1000

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        # mouse
        elif event.type == pygame.MOUSEBUTTONDOWN:

            if event.button == 1:
                grid.handle_mouse(event.pos)

        # teclado
        elif event.type == pygame.KEYDOWN:

            if event.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit()

            elif (
                event.key == pygame.K_UP
                or event.key == pygame.K_w
            ):
                grid.set_direction(
                    0,
                    -1,
                    "UP"
                )

            elif (
                event.key == pygame.K_DOWN
                or event.key == pygame.K_s
            ):
                grid.set_direction(
                    0,
                    1,
                    "DOWN"
                )

            elif (
                event.key == pygame.K_LEFT
                or event.key == pygame.K_a
            ):
                grid.set_direction(
                    -1,
                    0,
                    "LEFT"
                )

            elif (
                event.key == pygame.K_RIGHT
                or event.key == pygame.K_d
            ):
                grid.set_direction(
                    1,
                    0,
                    "RIGHT"
                )

    #atualiza
    for obj in objects:
        obj.update(dt)

    # Desenha
    screen.fill((15, 15, 15))

    for obj in objects:
        obj.draw(screen)

    pygame.display.flip()