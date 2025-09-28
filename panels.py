import math
import time
import pygame
from config import *
from rdap import rdap_cache, enqueue_rdap_query, choose_best_rdap, rdap_summary_from_json
from ui import render_text_with_border, hex_to_rgb, create_font
from hilbert import int_to_ipv4

INFO_BG_RGBA = (*hex_to_rgb(COLOR_INFO_BG), 220) if isinstance(COLOR_INFO_BG, str) else (*COLOR_INFO_BG, 220)

def prefix_len_from_block(bs: int) -> int:
    return 32 - int(round(math.log2(bs * bs)))

def register_panels_for_mouse(hx: int, hy: int, cam_x: float, cam_y: float, zoom: float,
                              screen_w: int, screen_h: int, ip_int: int, ip_str: str):
    panels = {}
    N = 1 << HILBERT_ORDER

    for block_size in (BLOCK_SIZE_8, BLOCK_SIZE_16, BLOCK_SIZE_24, BLOCK_SIZE_32):
        bx, by = (hx // block_size) * block_size, (hy // block_size) * block_size
        if bx + block_size <= 0 or by + block_size <= 0 or bx >= N or by >= N:
            continue

        left = int((bx - cam_x) * zoom)
        top = int((by - cam_y) * zoom)
        w = int(block_size * zoom)
        outer = pygame.Rect(left - 2, top - 2, w + 4, w + 4)
        if not screen_w > outer.left > -outer.width and screen_h > outer.top > -outer.height:
            continue

        if block_size == BLOCK_SIZE_32:
            pfx = prefix_len_from_block(BLOCK_SIZE_24)
            net_int = ip_int & (0xFFFFFFFF << (32 - pfx))
            prefix_text = f"{int_to_ipv4(net_int)}/{pfx}"
            if prefix_text not in panels:
                anchor_x = outer.right + PANEL_PADDING
                if anchor_x + 220 > screen_w:
                    anchor_x = outer.left - PANEL_PADDING - 220
                panels[prefix_text] = {
                    "outer": outer, "anchor": (anchor_x, outer.top),
                    "prefix_text": prefix_text, "block_size": BLOCK_SIZE_24
                }
            continue

        pfx = prefix_len_from_block(block_size)
        net_int = ip_int & (0xFFFFFFFF << (32 - pfx))
        prefix_text = f"{int_to_ipv4(net_int)}/{pfx}"
        anchor_x = outer.right + PANEL_PADDING
        if anchor_x + 220 > screen_w:
            anchor_x = outer.left - PANEL_PADDING - 220
        panels[prefix_text] = {
            "outer": outer, "anchor": (anchor_x, outer.top),
            "prefix_text": prefix_text, "block_size": block_size
        }

    return panels

def schedule_rdap_lookups(ip_str: str, panels: dict, last_time: float, debounce: float) -> float:
    now = time.time()
    if now - last_time <= debounce:
        return last_time

    ip_key = f"ip:{ip_str}"
    if not rdap_cache.contains(ip_key):
        enqueue_rdap_query(ip_key, ip_str)
        last_time = now

    for prefix in panels:
        net_key = f"net:{prefix}"
        if not rdap_cache.contains(net_key):
            enqueue_rdap_query(net_key, prefix)
            last_time = now

    return last_time

def render_panels(screen: pygame.Surface, panels: dict, cam_x: float, cam_y: float, zoom: float,
                  screen_w: int, screen_h: int, text_cache: dict, ip_int: int, ip_str: str):
    for prefix, info in panels.items():
        outer, anchor, block_size = info["outer"], info["anchor"], info["block_size"]
        if not MIN_RENDER_PIXELS <= outer.width <= MAX_RENDER_PIXELS:
            continue

        font_size = max(MIN_FONT_SIZE, int(outer.width * FONT_SCALE_MULTIPLIER))
        font = create_font(font_size)

        net_data = rdap_cache.get(f"net:{prefix}") if rdap_cache.contains(f"net:{prefix}") else None
        ip_data = rdap_cache.get(f"ip:{ip_str}") if rdap_cache.contains(f"ip:{ip_str}") else None
        best_data = choose_best_rdap(net_data, ip_data)
        summary = rdap_summary_from_json(best_data) if best_data else None

        lines = [prefix]
        if summary:
            if summary.get("org"): lines.append(str(summary["org"]))
            if summary.get("country"): lines.append(f"Country: {summary['country']}")
            if summary.get("abuse"): lines.append(f"Abuse: {summary['abuse']}")
            if summary.get("handle") and not summary.get("org"): lines.append(f"Handle: {summary['handle']}")
        else:
            lines.append("(no data)" if rdap_cache.contains(f"net:{prefix}") or rdap_cache.contains(f"ip:{ip_str}") else "fetching...")

        cache_key = (prefix, font_size, tuple(lines))
        if cache_key not in text_cache:
            text_cache[cache_key] = [render_text_with_border(font, line, hex_to_rgb(COLOR_INFO_TEXT), border=1) for line in lines]

        text_surfaces = text_cache[cache_key]
        pad = max(6, PANEL_PADDING * font_size // 12)
        panel_w = max(s.get_width() for s in text_surfaces) + pad * 2
        panel_h = sum(s.get_height() for s in text_surfaces) + pad * 2

        ax, ay = anchor
        panel_rect = pygame.Rect(ax, ay, panel_w, panel_h)
        if panel_rect.right > screen_w:
            panel_rect.right = outer.left - PANEL_PADDING
        panel_rect.top = max(2, min(panel_rect.top, screen_h - panel_h - 2))

        bg = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        bg.fill(INFO_BG_RGBA)
        screen.blit(bg, panel_rect)

        y = panel_rect.top + pad
        for ts in text_surfaces:
            screen.blit(ts, (panel_rect.left + pad, y))
            y += ts.get_height()