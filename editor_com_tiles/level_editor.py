import pygame
import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def asset_path(*parts):
    return os.path.join(BASE_DIR, *parts)
from abc import ABC, abstractmethod

pygame.init()

def singleton(class_):
    instances = { }
    def getinstance(*args, **kwargs):
        if class_ not in instances:
            instances[class_] = class_(*args, **kwargs)	
        return instances[class_]
    return getinstance

class editor_obj():
    def __init__(self, pos, sprite, dir = None):
        self.pos = pos
        self.sprite = sprite
        self.data = {"pos" : pos, "imagem" : {"dir": "", "dim" : [1,1]}}
        if dir:
            self.load(dir)
        self.following = False

    def update (self):
        if self.following:
            self.pos = pygame.mouse.get_pos()
            self.data["pos"]= self.pos

    def draw (self, screen):
         screen.blit(self.sprite, self.pos)

    def load (self, dir):
        s = pygame.image.load(dir).convert_alpha()
        self.sprite = s
        self.data["imagem"]["dir"] = dir
        self.data["imagem"]["dim"] = s.get_size()

class Background_layer (editor_obj):
    def __init__(self, imagem, profundidade):
        super().__init__((0,0), pygame.transform.scale(imagem, (600, 400)))
        self.profundidade = profundidade


    
        

@singleton
class Editor():
    
    def __init__(self):
        self.state = State_tiles()
        self.highlighted_object = None
        self.lvl_objs = []
        self.background = []
        self.bg_dir = []
        self.columns, self.rows, self.tile_size = 7, 4, 80
        self.active_collision = True
        self.grid = [[None for _ in range(self.rows)] for _ in range(self.columns)]


    def change_states(self, state):
        if state == "Posicionando":
            self.set_state(State_posicionando())
        elif state == "Movendo":
            self.set_state(State_movendo())
        elif state == "Background":
            self.set_state(State_background())
        elif state == "Tileset":
            self.set_state(State_tiles())


    def add_background(self, bg, dir):
        self.background.append(bg)
        self.bg_dir.append(dir)
        self.background.sort(key = lambda bg : bg.profundidade, reverse = True)

    def set_state(self, state):
        self.state = state


class Editor_states(ABC):

    def check_buttons (self, pos):
        for b in buttons:
            if (b.handle_click(pos, 1)):
                return True
        return False


    @abstractmethod
    def click(self, pos):
        pass

class State_movendo(Editor_states):
    def click(self, pos):

            if not self.check_buttons(pos):
                for o in Editor().lvl_objs:
                    if  o.sprite.get_rect(topleft = o.pos).collidepoint(event.pos):
                        place_obj = False
                        o.following = True
                        Editor().highlighted_object = o
                        break

class State_posicionando(Editor_states):
    def click(self, pos):

        if not self.check_buttons(pos):
            sprite = pygame.transform.scale(
                pygame.image.load(asset_path("images", "duck", "step.png")), duck_size)
            o = editor_obj(event.pos, sprite, dir = asset_path("images", "duck", "step.png"))
            Editor().lvl_objs.append(o)


class State_tiles(Editor_states):


    def __init__(self):
        super().__init__()
        self.tileset = pygame.image.load(asset_path("images", "tileset", "tileset.png")).convert()
        TILE_SIZE = 80
        self.tiles= []
        for _ in range (16):
            self.tiles.append(pygame.Surface((TILE_SIZE,TILE_SIZE))) 

        coords = [[0,0], [0,1], [1,0], [2,2],
                  [3,1], [0,2], [3,2], [0,3],
                  [1,3], [2,3], [2,0], [3,0],
                  [3,3], [2,1], [1,2], [1,1]]

        for tile, pos in zip(self.tiles, coords):
            tile.blit(self.tileset, [-pos[0]* TILE_SIZE, -pos[1]*TILE_SIZE])
        
    def click(self, pos):
        x, y = pos[0] // Editor().tile_size, pos[1] // Editor().tile_size
        if not (0 <= x < Editor().columns and 0 <= y < Editor().rows):
            return
        if event.button == 3:
            Editor().grid[x][y] = None
        else:
            Editor().grid[x][y] = Tile_cell((x, y), self.tiles, Editor().active_collision)
        self.resolve_all()

    @staticmethod
    def resolve_all():
        for column in Editor().grid:
            for tile in column:
                if tile:
                    tile.resolve()
        



class State_background(Editor_states):
    def click(self, pos):
            if not self.check_buttons(pos):
                dir = r"./images/backgrounds/hills.jpg"
                im = pygame.image.load(dir)
                BG = Background_layer(im, 3)
                Editor().add_background(BG, dir)



class Tile_cell (editor_obj):
    def __init__(self, grid_pos, sprites, collision=True):
        self.grid_pos = grid_pos
        self.sprites   = sprites
        self.collision = collision
        super().__init__((grid_pos[0]*80, grid_pos[1]*80), self.sprites[self.pick_sprite()])
        
    def pick_sprite (self):
        offset_vizinhos = [[-1, 0, 1], [1, 0, 2], [0, -1, 4], [0, 1, 8]]

        result_tile = 0

        for v in offset_vizinhos:
            vizinhox = self.grid_pos[0] + v[0]
            vizinhoy = self.grid_pos[1] + v[1]
            if (0 <= vizinhox < Editor().columns and 0 <= vizinhoy < Editor().rows):
                neighbor = Editor().grid[vizinhox][vizinhoy]
                if neighbor and neighbor.collision == self.collision:
                    result_tile |= v[2]

        
        return result_tile

    def resolve (self):
        n = self.pick_sprite()
        sprite = self.sprites[n]
        if not self.collision:
            sprite = sprite.copy()
            tint = pygame.Surface(sprite.get_size(), pygame.SRCALPHA)
            tint.fill((80, 155, 255, 105))
            sprite.blit(tint, (0, 0))
        self.sprite = sprite


duck_size = [32, 32]

def save_level (lvl_dicionario):
    with open(asset_path("level1.json"), "w") as f:
        json.dump(lvl_dicionario, f)
    return "level1.json"

def save_current_level():
    lvl_dict = { "objetos" : [o.data for o in Editor().lvl_objs],
                 "tiles": [{"grid_pos": tile.grid_pos, "collision": tile.collision,
                            "variant": tile.pick_sprite()}
                           for column in Editor().grid for tile in column if tile]}



    save_level(lvl_dict)


class Button:
    def __init__(self, rect, sprite=None):
        self.rect = pygame.Rect(rect)
        self.sprite = sprite

        if sprite is not None:
            max_w = self.rect.width * 0.8
            max_h = self.rect.height * 0.8

            scale = min(
                max_w / sprite.get_width(),
                max_h / sprite.get_height())
            size = (
                int(sprite.get_width() * scale),
                int(sprite.get_height() * scale))

            self.sprite = pygame.transform.scale(sprite, size)
    
        self.left_callback = None
        self.right_callback = None

    def bind_left(self, callback):
        self.left_callback = callback

    def bind_right(self, callback):
        self.right_callback = callback

    def draw(self, surface):
        pygame.draw.rect(surface, (80, 80, 80), self.rect)
        if self.sprite is not None:
            pos = self.sprite.get_rect(center=self.rect.center)
            surface.blit(self.sprite, pos)
    
    def handle_click(self, mouse_pos, mouse_button):
        if not self.rect.collidepoint(mouse_pos):
            return

        if mouse_button == 1 and self.left_callback:
            self.left_callback()
            return True

        elif mouse_button == 3 and self.right_callback:
            self.right_callback()
            return True



screen = pygame.display.set_mode((600, 400))
pygame.display.set_caption("Pygame Sample")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 20)

running = True

while running:

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.MOUSEBUTTONDOWN:
            Editor().state.click(event.pos)
            
            
        if event.type == pygame.MOUSEBUTTONUP:
            if Editor().highlighted_object:
                Editor().highlighted_object.following = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_c:
                Editor().active_collision = True
            elif event.key == pygame.K_n:
                Editor().active_collision = False
            elif event.key == pygame.K_s:
                save_current_level()



    for o in Editor().lvl_objs:
        o.update()


    screen.fill((30,30,30))

    for linha in Editor().grid:
        for tile in linha:
            if tile:
                tile.draw(screen)

    mode = "COM COLISÃO (C)" if Editor().active_collision else "SEM COLISÃO (N)"
    color = (255, 220, 110) if Editor().active_collision else (130, 190, 255)
    pygame.draw.rect(screen, (30, 30, 30), (0, 320, 600, 80))
    screen.blit(font.render(f"{mode} | C/N alternam | clique: colocar | botão direito: apagar | S: salvar", True, color), (10, 330))

    pygame.display.flip()
    clock.tick(15)

pygame.quit()
