import random
import sys

import pygame
from constants import *
from PIL import Image
import numpy as np
import matplotlib.pyplot as plt
import math


class Food:
    def __init__(self, x, y):
        self.position = {
            "x": x,
            "y": y
        }


class Snake:
    def __init__(self, _start_pos):
        row = _start_pos[0]
        col = _start_pos[1]
        floor_tile = FLOOR_ONE_TILE if ((row % 2 == 1 and col % 2 == 1) or
                                        (row % 2 == 0 and col % 2 == 0)) else FLOOR_TWO_TILE
        self.positions = [SnakePart((_start_pos[0], _start_pos[1]), "w", floor_tile)]
        self.positions[0].update_tile(SNAKE_HEAD_TILE)
        self.size = 3

    def move(self, movement, key):
        snake_head = self.positions[0]
        new_pos = {
            "x": snake_head.position["x"] + movement[0],
            "y": snake_head.position["y"] + movement[1]
        }

        row = new_pos["x"]
        col = new_pos["y"]
        floor_tile = FLOOR_ONE_TILE if ((row % 2 == 1 and col % 2 == 1) or
                                        (row % 2 == 0 and col % 2 == 0)) else FLOOR_TWO_TILE
        new_part = SnakePart(new_pos, key, floor_tile)
        new_part.update_tile(SNAKE_HEAD_TILE)
        self.positions.insert(0, new_part)
        if len(self.positions) > self.size:
            self.positions.pop()

        for index in range(len(self.positions) - 1):
            if index == 0:
                continue
            self.positions[index].update_tile(SNAKE_BODY_TILE)
        self.positions[-1].update_tile(SNAKE_TAIL_TILE)

    def check_if_collide_self(self) -> bool:
        snake_head = self.positions[0]

        for snake_part in self.positions:
            if snake_part == snake_head:
                continue

            if (snake_head.position["x"] == snake_part.position["x"] and
                    snake_head.position["y"] == snake_part.position["y"]):
                return True

        return False

    def check_food_collision(self, food: Food) -> bool:
        snake_head = self.positions[0]

        if snake_head.position["x"] == food.position["x"] and snake_head.position["y"] == food.position["y"]:
            return True

        return False


class SnakePart:
    def __init__(self, _pos, _direction, _floor_tile):
        self.prev = None
        self.next = None
        self.position = {
            "x": _pos[0] if type(_pos) is tuple else _pos["x"],
            "y": _pos[1] if type(_pos) is tuple else _pos["y"]
        }
        self.snake_tile = None
        self.direction = _direction

    def update_tile(self, TILE):
        self.snake_tile = TILE


class SnakeGame:
    def __init__(self, title, window_size: tuple, fps=60, scale=1):
        pygame.init()
        self.screen = pygame.display.set_mode(window_size)
        self.clock = pygame.time.Clock()
        self.tile_size = 16 * scale
        self.window_size = pygame.math.Vector2(self.screen.get_width(), self.screen.get_height())

        self.title = title
        self.version = None
        self.running = False
        self.surface = None
        self.background_color = "#37DB7A"
        self.mouse_pos = pygame.math.Vector2()
        self.tile_set = pygame.image.load("tileset.png").convert()
        self.food_img = pygame.image.load("food.png").convert()
        self.tile_map = []
        self.movement = {"w": (-1, 0), "s": (1, 0), "a": (0, -1), "d": (0, 1)}
        self.last_movement = None

        # Food
        self.foods = []

        # Snake
        self.snake_speed = 4
        self.snake = Snake((self.window_size.x // self.tile_size // 2, self.window_size.y // self.tile_size // 2))

        # Game Frames
        self.fps = fps
        self.frame = 0
        self.lowest_fps = 60
        self.fps_array = []

    def update_tile_map(self):
        rows = int(self.window_size.y / self.tile_size)
        cols = int(self.window_size.x / self.tile_size)

        positions = {}
        for snake_position in self.snake.positions:
            pos = snake_position.position
            positions[(int(pos["x"]), int(pos["y"]))] = snake_position.snake_tile

        for row in range(len(self.tile_map)):
            for col in range(len(self.tile_map[row])):
                if row == 0 or col == 0 or row == rows - 1 or col == cols - 1:
                    continue

                tile_id = self.tile_map[row][col]

                if (row, col) in positions.keys():
                    self.tile_map[row][col] = positions[(row, col)]

                elif tile_id in [SNAKE_HEAD_TILE, SNAKE_BODY_TILE, SNAKE_TAIL_TILE] and (
                        row, col) not in positions.keys():
                    self.tile_map[row][col] = FLOOR_ONE_TILE if ((row % 2 == 1 and col % 2 == 1) or
                                                                 (row % 2 == 0 and col % 2 == 0)) else FLOOR_TWO_TILE

    def game_over(self):
        snake_head = self.snake.positions[0]
        rows = int(self.window_size.y / self.tile_size)
        cols = int(self.window_size.x / self.tile_size)

        if (snake_head.position["x"] in [0, rows - 1] or
                snake_head.position["y"] in [0, cols - 1]):
            return True

        if self.snake.check_if_collide_self():
            return True

        return False

    def generate_food(self):
        if self.frame & 16 != 0 or len(self.foods) >= 1:
            return

        tile_id = -1
        while tile_id == -1:
            row = random.choice(range(len(self.tile_map)))
            col = random.choice(range(len(self.tile_map[row])))
            choice = self.tile_map[row][col]

            if choice in [FLOOR_ONE_TILE, FLOOR_TWO_TILE]:
                tile_id = FOOD_TILE
                self.tile_map[row][col] = tile_id
                self.foods.append(Food(row, col))

    def events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.MOUSEMOTION:
                self.mouse_pos = pygame.math.Vector2(pygame.mouse.get_pos())

            if event.type == pygame.KEYDOWN:
                if event.unicode in ("w", "a", "s", "d"):
                    key_pressed = event.unicode
                    dx = self.movement[key_pressed][0]
                    dy = self.movement[key_pressed][1]

                    if self.last_movement is not None:
                        if self.last_movement[0] == (-self.movement[key_pressed][0], -self.movement[key_pressed][1]):
                            return

                    if (0 < self.snake.positions[0].position["x"] + dx < self.window_size.x / self.tile_size - 1 and
                            0 < self.snake.positions[0].position["y"] + dy < self.window_size.y / self.tile_size - 1):
                        self.last_movement = (self.movement[key_pressed], key_pressed)
                if event.unicode == "q":
                    self.snake.size += 1

    def render(self):
        surface = pygame.Surface(self.window_size, pygame.SRCALPHA)

        for row in range(len(self.tile_map)):
            for col in range(len(self.tile_map[row])):
                tile_id = self.tile_map[row][col]

                image_surface = pygame.Surface((16, 16), pygame.SRCALPHA)
                src_rect = pygame.Rect(tile_id % 3 * self.tile_size, tile_id // 3 * self.tile_size, self.tile_size,
                                       self.tile_size)
                if tile_id is FOOD_TILE:
                    image_surface.blit(self.food_img, (0, 0))
                else:
                    image_surface.blit(self.tile_set, (0, 0), src_rect)

                dest_pos = (col * self.tile_size, row * self.tile_size)
                if tile_id in [3, 5]:
                    angles = {
                        "w": 0,
                        "a": 90,
                        "s": 180,
                        "d": 270
                    }
                    angle = self.snake.positions[0] if tile_id == 3 else self.snake.positions[-1]
                    angle = angles[angle.direction]
                    rotated_image_surface = pygame.transform.rotate(image_surface, angle)
                    surface.blit(rotated_image_surface, dest_pos)
                else:
                    surface.blit(image_surface, dest_pos)

        self.surface.blit(surface, (0, 0))

    def update(self):
        self.surface = pygame.Surface(self.window_size)

        self.generate_food()

        if self.frame % self.snake_speed == 0 and self.last_movement:
            self.snake.move(self.last_movement[0], self.last_movement[1])

        for food in self.foods:
            if self.snake.check_food_collision(food):
                self.foods.remove(food)
                self.snake.size += 1
                row, col = food.position["x"], food.position["y"]
                self.tile_map[row][col] = FLOOR_ONE_TILE if ((row % 2 == 1 and col % 2 == 1) or
                                                             (row % 2 == 0 and col % 2 == 0)) else FLOOR_TWO_TILE

        self.update_tile_map()
        self.render()

        if self.game_over():
            game.running = False

        self.screen.blit(self.surface, (0, 0))

    def main(self):
        self.events()
        self.update()
        fps = math.floor(self.clock.get_fps())
        if self.frame > 10:
            self.lowest_fps = fps if fps < self.lowest_fps else self.lowest_fps
            self.fps_array.append(fps)

        pygame.display.update()
        self.clock.tick(self.fps)
        self.frame += 1

    def start(self):
        rows = int(self.window_size.y / self.tile_size)
        cols = int(self.window_size.x / self.tile_size)

        for row in range(rows):
            tile_map_row = []
            for col in range(cols):
                if row == 0 or col == 0 or row == rows - 1 or col == cols - 1:
                    tile_id = BORDER_TILE
                elif (row % 2 == 1 and col % 2 == 1) or (row % 2 == 0 and col % 2 == 0):
                    tile_id = FLOOR_ONE_TILE
                else:
                    tile_id = FLOOR_TWO_TILE

                tile_map_row.append(tile_id)

            self.tile_map.append(tile_map_row)
        self.generate_food()
        self.running = True


if __name__ == "__main__":
    game = SnakeGame("Snake", (720, 720))
    game.start()
    while game.running:
        game.main()
    pygame.quit()
    sys.exit()
