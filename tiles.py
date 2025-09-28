import math
import pygame
from cache import get_scaled_tile
from ui import hex_to_rgb
from config import TILE_SIZE, SUBNET_BORDER_WIDTH, COLOR_BORDER

COLOR_BORDER_RGB = hex_to_rgb(COLOR_BORDER) if isinstance(COLOR_BORDER, str) else COLOR_BORDER

def draw_visible_tiles(screen, cam_x, cam_y, zoom, screen_w, screen_h, level):
    tile_world = TILE_SIZE * (2 ** level)
    wx0, wy0 = cam_x, cam_y
    wx1, wy1 = cam_x + screen_w / zoom, cam_y + screen_h / zoom
    
    start_x = int(wx0 // tile_world) * tile_world
    start_y = int(wy0 // tile_world) * tile_world
    
    blit_size = max(1, int(TILE_SIZE * zoom * (2 ** level)))
    
    y = start_y
    while y <= wy1:
        x = start_x
        while x <= wx1:
            if surf := get_scaled_tile(level, x, y, blit_size, blit_size):
                screen.blit(surf, (int((x - cam_x) * zoom), int((y - cam_y) * zoom)))
            x += tile_world
        y += tile_world

def draw_subnet_border(screen, cam_x, cam_y, zoom, screen_w, screen_h, bx, by, block_size):
    left = int((bx - cam_x) * zoom)
    top = int((by - cam_y) * zoom)
    w = int(block_size * zoom)
    outer = pygame.Rect(left - SUBNET_BORDER_WIDTH, top - SUBNET_BORDER_WIDTH,
                       w + SUBNET_BORDER_WIDTH * 2, w + SUBNET_BORDER_WIDTH * 2)
    
    if screen_w > outer.left > -outer.width and screen_h > outer.top > -outer.height:
        pygame.draw.rect(screen, COLOR_BORDER_RGB, outer, SUBNET_BORDER_WIDTH)