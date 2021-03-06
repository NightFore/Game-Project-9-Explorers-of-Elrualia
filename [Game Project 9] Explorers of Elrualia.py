import pygame
import os
from pygame.locals import *
from os import path

from ScaledGame import *
from Camera import *
from Map import *

vec = pygame.math.Vector2

"""
    Settings
"""
# Main Settings
project_title = "Explorers of Elrualia"
screen_size = WIDTH, HEIGHT = 800, 640
FPS = 60

# Secondary Settings
TILESIZE = 32
GRIDWIDTH = WIDTH / TILESIZE
GRIDHEIGHT = HEIGHT / TILESIZE

# Layer Settings
LAYER_CURSOR = 3
LAYER_PLAYER = 2
LAYER_SELECTION = 1

"""
    Colors
"""
RED = 255, 0, 0
GREEN = 0, 255, 0
BLUE = 0, 0, 255

YELLOW = 255, 255, 0
MAGENTA = 255, 0, 255
CYAN = 0, 255, 255

LIGHTGREY = 100, 100, 100

BLACK = 0, 0, 0
WHITE = 255, 255, 255

"""
    Helpful Functions
"""


def update_time_dependent(sprite):
    sprite.current_time += sprite.dt
    if sprite.current_time >= sprite.animation_time:
        sprite.current_time = 0
        sprite.index = (sprite.index + 1) % len(sprite.images)
        sprite.image = sprite.images[sprite.index]
    sprite.rect = sprite.image.get_rect()
    sprite.rect.center = sprite.pos
    sprite.image = pygame.transform.rotate(sprite.image, 0)


def update_bobbing(sprite):
    offset = BOB_RANGE * (sprite.tween(sprite.step / BOB_RANGE) - 0.5)
    sprite.rect.centery = sprite.pos.y + offset * sprite.dir
    sprite.step += BOB_SPEED
    if sprite.step > BOB_RANGE:
        sprite.step = 0
        sprite.dir *= -1


def load_file(path, image=False):
    file = []
    for file_name in os.listdir(path):
        if image:
            file.append(pygame.image.load(path + os.sep + file_name).convert_alpha())
        else:
            file.append(path + os.sep + file_name)
    return file


def load_image(image_path, image_list):
    images = []
    for image in image_list:
        images.append(pygame.image.load(path.join(image_path, image)).convert_alpha())
    return images


def load_tile_table(filename, width, height, colorkey=(0, 0, 0)):
    image = pygame.image.load(filename).convert()
    image.set_colorkey(colorkey)
    image_width, image_height = image.get_size()
    tile_table = []
    for tile_y in range(int(image_height / height)):
        line = []
        tile_table.append(line)
        for tile_x in range(int(image_width / width)):
            rect = (tile_x * width, tile_y * height, width, height)
            line.append(image.subsurface(rect))
    return tile_table


def transparent_surface(width, height, color, border, colorkey=(0, 0, 0)):
    surface = pygame.Surface((width, height)).convert()
    surface.set_colorkey(colorkey)
    surface.fill(color)
    surface.fill(colorkey, surface.get_rect().inflate(-border, -border))
    return surface



def collision(sprite_1, sprite_2, dx=0, dy=0):
    sprite_1.pos[0] += dx
    sprite_1.pos[1] += dy
    sprite_1.rect.x = sprite_1.pos[0] * TILESIZE
    sprite_1.rect.y = sprite_1.pos[1] * TILESIZE
    collide = pygame.sprite.spritecollide(sprite_1, sprite_2, False)

    sprite_1.pos[0] -= dx
    sprite_1.pos[1] -= dy
    sprite_1.rect.x = sprite_1.pos[0] * TILESIZE
    sprite_1.rect.y = sprite_1.pos[1] * TILESIZE
    return collide



"""
    Game
"""


class Game:
    def __init__(self):
        pygame.mixer.pre_init(44100, -16, 2, 2048)
        pygame.mixer.init()
        pygame.init()
        pygame.key.set_repeat(300, 75)
        self.gameDisplay = ScaledGame(project_title, screen_size, 60)
        self.clock = pygame.time.Clock()
        self.dt = self.clock.tick(FPS) / 1000
        self.load_data()
        self.new()

    def draw_text(self, text, font_name, size, color, x, y, align="nw"):
        font = pygame.font.Font(font_name, size)
        text_surface = font.render(text, True, color)
        text_rect = text_surface.get_rect()
        if align == "nw":
            text_rect.topleft = (x, y)
        if align == "ne":
            text_rect.topright = (x, y)
        if align == "sw":
            text_rect.bottomleft = (x, y)
        if align == "se":
            text_rect.bottomright = (x, y)
        if align == "n":
            text_rect.midtop = (x, y)
        if align == "s":
            text_rect.midbottom = (x, y)
        if align == "e":
            text_rect.midright = (x, y)
        if align == "w":
            text_rect.midleft = (x, y)
        if align == "center":
            text_rect.center = (x, y)
        self.gameDisplay.blit(text_surface, text_rect)

    def load_data(self):
        game_folder = path.dirname(__file__)
        data_folder = path.join(game_folder, "data")
        graphics_folder = path.join(data_folder, "graphics")
        sfx_folder = path.join(data_folder, "sfx")
        voice_folder = path.join(data_folder, "voice")
        music_folder = path.join(data_folder, "music")
        map_folder = path.join(data_folder, "map")

        # Font
        self.font = None

        # Pause Screen
        self.dim_screen = pygame.Surface(self.gameDisplay.get_size()).convert_alpha()
        self.dim_screen.fill((100, 100, 100, 120))

        # Map
        self.map = Map(path.join(map_folder, "Map_1.tmx"))
        self.map_img = self.map.make_map()
        self.map_rect = self.map_img.get_rect()

        # Characters
        self.player_img = load_tile_table(path.join(graphics_folder, PLAYER_IMG), 32, 32)
        self.skeleton_img = load_tile_table(path.join(graphics_folder, SKELETON_IMG), 32, 32)

        # Music
        self.music = "music_aaron_krogh_310_world_map.mp3"

        # Image Items
        self.item_images = {}

        # Image Effects
        self.effect_images = {}

        # Sound Effects
        self.sounds_effects = {}

        # Sound Voices
        self.sounds_voice = {}

        # Sound Musics
        pygame.mixer.music.load(path.join(music_folder, self.music))

    def new(self):
        self.debug_obstacle = False
        self.debug_atk = False

        self.paused = False
        self.camera = Camera(self.map.width, self.map.height, WIDTH, HEIGHT)
        self.all_sprites = pygame.sprite.LayeredUpdates()
        self.characters = pygame.sprite.Group()
        self.obstacle = pygame.sprite.Group()

        for tile_layer in self.map.tmxdata.layers:
            if tile_layer.name == "collision":
                for x, y, image in tile_layer.tiles():
                    Obstacle(self, x, y, self.map.tmxdata.tilewidth, self.map.tmxdata.tileheight)

        for tile_object in self.map.tmxdata.objects:
            obj_center = vec(tile_object.x + tile_object.width / 2, tile_object.y + tile_object.height / 2)
            if tile_object.name == "cursor":
                self.cursor = Cursor(self, obj_center.x, obj_center.y)
            if tile_object.name == "player":
                self.player = Character(self, obj_center.x, obj_center.y, self.player_img, "Player", PLAYER_WEAPON, PLAYER_MOVEMENT)
            if tile_object.name == "skeleton":
                self.skeleton = Character(self, obj_center.x, obj_center.y, self.skeleton_img, "Skeleton", SKELETON_WEAPON, SKELETON_MOVEMENT)

    def run(self):
        self.playing = True
        pygame.mixer.music.play(-1)
        while self.playing:
            self.dt = self.clock.tick(FPS) / 1000
            self.events()
            if not self.paused:
                self.update()
            self.draw()

    def quit_game(self):
        pygame.quit()
        quit()

    def events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.quit_game()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.quit_game()
                if event.key == pygame.K_p:
                    self.paused = not self.paused

                if event.key == pygame.K_LEFT or event.key == pygame.K_a:
                    self.cursor.move(dx=-1)
                if event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                    self.cursor.move(dx=+1)
                if event.key == pygame.K_UP or event.key == pygame.K_w:
                    self.cursor.move(dy=-1)
                if event.key == pygame.K_DOWN or event.key == pygame.K_s:
                    self.cursor.move(dy=+1)

                if event.key == pygame.K_j:
                    self.debug_obstacle = not self.debug_obstacle
                if event.key == pygame.K_r:
                    if not self.debug_atk:
                        self.player.range = 2
                    else:
                        self.player.range = 1
                    self.debug_atk = not self.debug_atk

                if event.key == pygame.K_h:
                    self.cursor.action()

    def update(self):
        self.all_sprites.update()
        self.camera.update(self.cursor)

    def draw(self):
        # Map
        self.gameDisplay.blit(self.map_img, self.camera.apply_rect(self.map_rect))

        # Selection
        # [0, 0, 1, 0, 0],
        # [0, 1, 1, 1, 0],
        # [1, 1, 1, 1, 1],
        # [0, 1, 1, 1, 0],
        # [0, 0, 1, 0, 0]]
        if self.cursor.selection.alive():
            pos = self.cursor.selection.pos
            mov = self.cursor.selection.sprite.movement
            atk = self.cursor.selection.sprite.range
            index_i = index_j = 0
            for i in range(-mov, mov+1):
                for j in range(-mov, mov+1):
                    if self.cursor.selection_mov[index_i][index_j]:
                        pygame.draw.rect(self.gameDisplay, BLUE, self.camera.apply_rect(pygame.Rect(TILESIZE * (j + pos[0]), TILESIZE * (i + pos[1]), TILESIZE, TILESIZE)))
                    index_j += 1
                index_i += 1
                index_j = 0

            index_i = index_j = 0
            for i in range(-mov-atk, mov+atk+1):
                for j in range(-mov-atk, mov+atk+1):
                    if self.cursor.selection_atk[index_i][index_j]:
                        pygame.draw.rect(self.gameDisplay, RED, self.camera.apply_rect(pygame.Rect(TILESIZE * (j + pos[0]), TILESIZE * (i + pos[1]), TILESIZE, TILESIZE)))
                    index_j += 1
                index_i += 1
                index_j = 0

        # Grid
        for col in range(self.map.width // TILESIZE):
            for row in range(self.map.height // TILESIZE):
                pygame.draw.rect(self.gameDisplay, LIGHTGREY, self.camera.apply_rect(pygame.Rect(TILESIZE * col, TILESIZE * row, TILESIZE, TILESIZE)), 1)

        # Sprite
        for sprite in self.all_sprites:
            self.gameDisplay.blit(sprite.image, self.camera.apply(sprite))

        if self.debug_obstacle:
            for obstacle in self.obstacle:
                pygame.draw.rect(self.gameDisplay, CYAN, self.camera.apply_rect(obstacle.rect), 1)

        # Pause
        if self.paused:
            self.gameDisplay.blit(self.dim_screen, (0, 0))
            self.draw_text("Paused", self.font, 105, RED, WIDTH / 2, HEIGHT / 2, align="center")

        self.gameDisplay.update()


"""
    Others Functions
"""
class Cursor(pygame.sprite.Sprite):
    def __init__(self, game, x, y):
        # Setup
        self.game = game
        self.groups = self.game.all_sprites
        self._layer = LAYER_CURSOR
        pygame.sprite.Sprite.__init__(self, self.groups)

        # Position
        self.pos = [int(x / TILESIZE), int(y / TILESIZE)]

        # Surface
        self.image = transparent_surface(TILESIZE, TILESIZE, YELLOW, 6)
        self.rect = self.image.get_rect()
        self.rect.x = self.pos[0] * TILESIZE
        self.rect.y = self.pos[1] * TILESIZE

        # Action
        self.selection = pygame.sprite.Sprite()
        self.selection_mov = [[]]

    def move(self, dx=0, dy=0):
        if not collision(self, self.game.obstacle, dx, dy):
            if self.selection.alive():
                x_pos = self.selection.sprite.movement + self.pos[0] - self.selection.sprite.pos[0] + dx
                y_pos = self.selection.sprite.movement + self.pos[1] - self.selection.sprite.pos[1] + dy
                mov = self.selection.sprite.movement
                atk = self.selection.sprite.range

                mov_check = atk_check = False
                if 0 <= x_pos < 2*mov+1 and 0 <= y_pos < 2*mov+1:
                    mov_check = self.selection_mov[y_pos][x_pos]
                if 0 <= x_pos+atk < 2*(mov+atk)+1 and 0 <= y_pos+atk < 2*(mov+atk)+1:
                    atk_check = self.selection_atk[y_pos+atk][x_pos+atk]
                if not mov_check and not atk_check:
                    dx = dy = 0

            self.pos[0] += dx
            self.pos[1] += dy
            self.rect.x = self.pos[0] * TILESIZE
            self.rect.y = self.pos[1] * TILESIZE

    def action(self):
        if not self.selection.alive():
            for sprite in self.game.characters:
                if sprite.pos == self.pos:
                    self.selection = Selection(self.game, sprite, self.pos[0], self.pos[1], TILESIZE, TILESIZE)
                    mov = self.selection.sprite.movement
                    atk = self.selection.sprite.range
                    self.selection_mov = [[False] * (mov*2+1) for i in range(mov*2+1)]
                    self.selection_atk = [[False] * ((mov+atk)*2+1) for i in range((mov+atk)*2+1)]

                    # Selection Movement Range Grid
                    for i in range(2*mov+1):
                        for j in range(2*mov+1):
                            if abs(i-mov) + abs(j-mov) <= mov:
                                if not collision(self.selection, self.game.obstacle, j-mov, i-mov) and not collision(self.selection, self.game.characters, j-mov, i-mov):
                                    self.selection_mov[i][j] = True
                    self.selection_mov[mov][mov] = True
                    reachable(self.selection_mov, mov, mov, 1)

                    # Selection Attack Range Grid
                    for i in range(2*mov+1):
                        for j in range(2*mov+1):
                            if self.selection_mov[i][j]:
                                for x in range(-atk, atk+1):
                                    for y in range(-atk, atk+1):
                                        if abs(x) + abs(y) == atk:
                                            if not collision(self.selection, self.game.obstacle, j-mov+y, i-mov+x):
                                                if 0 <= i+x < 2*mov+1 and 0 <= j+y < 2*mov+1:
                                                    if not self.selection_mov[i+x][j+y]:
                                                        self.selection_atk[i+x+atk][j+y+atk] = True
                                                else:
                                                    self.selection_atk[i+x+atk][j+y+atk] = True
        else:
            self.selection.sprite.pos[0] = self.pos[0]
            self.selection.sprite.pos[1] = self.pos[1]
            self.selection.kill()

    def update(self):
        pass

def reachable(list, i_loop, j_loop, rg):
    for i in range(2*i_loop+1):
        for j in range(2*j_loop+1):
            if list[i][j]:
                reach = False
                for x in range(-rg, rg+1):
                    for y in range(-rg, rg+1):
                        if abs(x) + abs(y) == rg and 0 < i+x < 2*i_loop+1 and 0 < j+y < 2*j_loop+1:
                            if list[i+x][j+y]:
                                reach = True
                list[i][j] = reach

class Selection(pygame.sprite.Sprite):
    def __init__(self, game, sprite, x, y, w, h):
        # Setup
        self.game = game
        self.groups = self.game.all_sprites
        self._layer = LAYER_SELECTION
        pygame.sprite.Sprite.__init__(self, self.groups)

        # Settings
        self.sprite = sprite

        # Surface
        self.image = pygame.Surface((TILESIZE, TILESIZE)).convert()
        self.image.fill(BLUE)

        # Position
        self.rect = self.image.get_rect()
        self.pos = [x, y]
        self.rect.x = self.pos[0]*w
        self.rect.y = self.pos[1]*h



class Obstacle(pygame.sprite.Sprite):
    def __init__(self, game, x, y, w, h):
        # Setup
        self.game = game
        self.groups = self.game.obstacle
        pygame.sprite.Sprite.__init__(self, self.groups)

        # Position
        self.rect = pygame.Rect(x, y, w, h)
        self.pos = [x, y]
        self.rect.x = self.pos[0]*w
        self.rect.y = self.pos[1]*h



class Weapon:
    def __init__(self, attack, hit, critical, range, weight):
        self.attack = attack
        self.hit = hit
        self.critical = critical
        self.range = range
        self.weight = weight

class Iron_Sword(Weapon):
    def __init__(self):
        Weapon.__init__(self, 5, 100, 0, 1, 2)

class Character(pygame.sprite.Sprite):
    def __init__(self, game, x, y, image, name, weapon, movement):
        # Setup
        self.game = game
        self.groups = self.game.all_sprites, self.game.characters
        self._layer = LAYER_PLAYER
        pygame.sprite.Sprite.__init__(self, self.groups)

        # Settings
        self.name = name
        self.weapon = weapon
        self.movement = movement

        self.range = self.weapon.range

        # Position
        self.pos = [int(x / TILESIZE), int(y / TILESIZE)]

        # Surface
        self.base_index = 1
        self.index = self.base_index
        self.images = image
        self.images_bottom = self.images[0]
        self.images_left = self.images[1]
        self.images_right = self.images[2]
        self.images_top = self.images[3]
        self.images = self.images_bottom
        self.image = self.images_bottom[self.index]

        self.rect = self.image.get_rect()
        self.rect.x = self.pos[0] * TILESIZE
        self.rect.y = self.pos[1] * TILESIZE

        self.dt = game.dt
        self.current_time = 0
        self.animation_time = 0.50

    def update(self):
        update_time_dependent(self)
        self.current_time += self.dt

        self.rect.x = self.pos[0] * TILESIZE
        self.rect.y = self.pos[1] * TILESIZE

    def attack(self):
        pass



# Characters Settings
PLAYER_IMG = "character_pipoya_male_01_2.png"
PLAYER_WEAPON = Iron_Sword()
PLAYER_MOVEMENT = 3

SKELETON_IMG = "character_pipoya_enemy_04_1.png"
SKELETON_WEAPON = Iron_Sword()
SKELETON_MOVEMENT = 2

g = Game()
while True:
    g.new()
    g.run()
