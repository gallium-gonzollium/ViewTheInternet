import os
import pygame
from config import *

_font_cache = {}

def create_font(size: int) -> pygame.font.Font:
    if size not in _font_cache:
        if FONT_PATH and os.path.exists(FONT_PATH):
            _font_cache[size] = pygame.font.Font(FONT_PATH, size)
        else:
            _font_cache[size] = pygame.font.SysFont(FONT_NAME, size)
    return _font_cache[size]

def hex_to_rgb(h: str) -> tuple:
    if not isinstance(h, str):
        return tuple(h[:3]) if hasattr(h, '__getitem__') else (255,255,255)
    s = h.lstrip('#')
    return tuple(int(s[i:i+2], 16) for i in (0, 2, 4)) if len(s) == 6 else (255,255,255)

def render_text_with_border(font: pygame.font.Font, text: str, color: tuple, border_color=(0,0,0), border=1) -> pygame.Surface:
    fg_surf = font.render(text, True, color)
    w, h = fg_surf.get_size()
    surf = pygame.Surface((w + border*2, h + border*2), pygame.SRCALPHA)
    
    border_surf = font.render(text, True, border_color)
    for ox in range(-border, border+1):
        for oy in range(-border, border+1):
            if ox or oy:
                surf.blit(border_surf, (ox + border, oy + border))
    surf.blit(fg_surf, (border, border))
    return surf

OCTET_COLS = [hex_to_rgb(c) for c in (COLOR_OCTET_1, COLOR_OCTET_2, COLOR_OCTET_3, COLOR_OCTET_4)]
DOT_COL = hex_to_rgb(COLOR_DOTS)
INFO_TEXT_COL = hex_to_rgb(COLOR_INFO_TEXT)

def render_ip_octets(screen: pygame.Surface, ip_str: str, screen_h: int, ip_font: pygame.font.Font, cached: dict) -> dict:
    if ip_str != cached.get("last_ip"):
        parts = []
        for i, octet in enumerate(ip_str.split(".")):
            parts.append(render_text_with_border(ip_font, octet, OCTET_COLS[i], border=2))
            if i < 3:
                parts.append(render_text_with_border(ip_font, ".", DOT_COL, border=2))
        cached = {"parts": parts, "last_ip": ip_str}

    if parts := cached.get("parts"):
        y0 = screen_h - 6 - max(p.get_height() for p in parts)
        x = 6
        for p in parts:
            screen.blit(p, (x, y0))
            x += p.get_width()
    
    return cached

def hud_render(screen: pygame.Surface, hud_font: pygame.font.Font, clock: pygame.time.Clock, cache: dict, zoom: float, level: int) -> None:
    hud_text = f"Zoom:{zoom:.3f} @ {level} - FPS:{clock.get_fps():.1f}"
    if hud_text != cache.get("last_hud"):
        cache.update({"last_hud": hud_text, "surf": render_text_with_border(hud_font, hud_text, INFO_TEXT_COL, border=1)})
    if surf := cache.get("surf"):
        screen.blit(surf, (6, 6))