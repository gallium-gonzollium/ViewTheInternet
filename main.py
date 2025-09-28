import math
import os
import webbrowser
import pygame
from config  import *
from hilbert import xy2d, int_to_ipv4
from cache   import clear_tile_caches
from camera  import Camera
from tiles   import draw_visible_tiles, draw_subnet_border
from panels  import register_panels_for_mouse, schedule_rdap_lookups, render_panels
from ui      import create_font, render_ip_octets, hud_render
from context import ContextMenu
from startup import startup_procedure

STATE_TITLE, STATE_RUNNING, STATE_SETTINGS, STATE_VIEW_CONFIG, STATE_HELP, STATE_CREDITS = "title", "running", "settings", "view_config", "help", "credits"
GITHUB_URL = "https://github.com/gallium-gonzollium/ViewTheInternet"

def draw_button(screen, rect, text, font, bg=(40,40,40), fg=(230,230,230), border=(0,0,0)):
    pygame.draw.rect(screen, bg, rect)
    pygame.draw.rect(screen, border, rect, 1)
    surf = font.render(text, True, fg)
    screen.blit(surf, surf.get_rect(center=rect.center))

def dim_background(screen, alpha=128):
    overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
    overlay.fill((0,0,0,alpha))
    screen.blit(overlay, (0,0))

def apply_bloom(screen, strength: float, radius: int):
    try:
        sw, sh = screen.get_size()
        factor = max(1, int(radius))
        small = pygame.transform.smoothscale(screen, (sw//factor, sh//factor))
        bloom = pygame.transform.smoothscale(small, (sw, sh))
        brightness = max(0.0, min(1.0, strength))
        dimmer = pygame.Surface((sw, sh)).convert_alpha()
        dimmer.fill((int(255 * brightness),) * 3 + (255,))
        bloom.blit(dimmer, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        screen.blit(bloom, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
    except:
        pass

def main():
    startup_procedure()
    pygame.init()
    info = pygame.display.Info()
    SCREEN_W, SCREEN_H = info.current_w, info.current_h
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), pygame.FULLSCREEN)
    pygame.display.set_caption("View the Internet")
    clock = pygame.time.Clock()

    hud_font, ip_font = create_font(18), create_font(48)
    title_font, menu_font, small_font = create_font(64), create_font(36), create_font(20)

    cam = Camera(SCREEN_W, SCREEN_H)
    context_menu = ContextMenu()
    state, last_lookup_time = STATE_TITLE, 0.0
    octet_cache, panel_text_cache, hud_cache = {}, {}, {}
    config_text = open(os.path.join(os.path.dirname(__file__), "config.py"), "r", encoding="utf-8").read()
    config_lines, config_scroll = config_text.splitlines(), 0

    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        click_pos, click_button = None, None

        context_menu.update()

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT: 
                running = False
                
            if ev.type == pygame.MOUSEBUTTONDOWN:
                if ev.button == 1:  
                    if context_menu.is_visible and context_menu.handle_click(ev.pos):
                        pass
                    else:
                        click_pos, click_button = ev.pos, 1
                        if context_menu.is_visible:
                            context_menu.hide()
                            
                elif ev.button == 3: 
                    if state == STATE_RUNNING:
                        mx, my = ev.pos
                        mouse_wx, mouse_wy = cam.x + mx / cam.zoom, cam.y + my / cam.zoom
                        N = 1 << HILBERT_ORDER
                        hx, hy = int(max(0, min(N-1, mouse_wx))), int(max(0, min(N-1, mouse_wy)))
                        d = xy2d(N, hx, hy)
                        ip_str = int_to_ipv4(d)
                        
                        context_menu.show(ev.pos, ip_str, d)
                    else:
                        context_menu.hide()
            
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                if state in (STATE_SETTINGS, STATE_VIEW_CONFIG, STATE_HELP, STATE_CREDITS):
                    state = STATE_RUNNING
                elif state == STATE_RUNNING:
                    state = STATE_SETTINGS
                if context_menu.is_visible:
                    context_menu.hide()
            
            if state == STATE_RUNNING: 
                cam.handle_event(ev)
            elif state == STATE_VIEW_CONFIG and ev.type == pygame.MOUSEWHEEL:
                config_scroll = max(0, config_scroll - ev.y * 4)

        screen.fill((0,0,0))
        if state != STATE_RUNNING: 
            dim_background(screen, 128)

        if state == STATE_TITLE:
            surf = title_font.render("View the Internet", True, (240,240,240))
            screen.blit(surf, surf.get_rect(centerx=SCREEN_W//2, top=SCREEN_H//6))
            
            btn_w, btn_h = 260, 64
            explore_rect = pygame.Rect(SCREEN_W//2 - btn_w - 20, SCREEN_H//2 - btn_h//2, btn_w, btn_h)
            settings_rect = pygame.Rect(SCREEN_W//2 + 20, SCREEN_H//2 - btn_h//2, btn_w, btn_h)
            
            draw_button(screen, explore_rect, "Explore", menu_font)
            draw_button(screen, settings_rect, "Settings", menu_font)
            
            if click_pos:
                if explore_rect.collidepoint(click_pos): 
                    state = STATE_RUNNING
                elif settings_rect.collidepoint(click_pos): 
                    state = STATE_SETTINGS

        elif state in (STATE_SETTINGS, STATE_HELP, STATE_VIEW_CONFIG, STATE_CREDITS):
            panel_w, panel_h = 520, 420
            panel = pygame.Rect((SCREEN_W - panel_w)//2, (SCREEN_H - panel_h)//2, panel_w, panel_h)
            pygame.draw.rect(screen, (18,18,18), panel)
            pygame.draw.rect(screen, (200,200,200), panel, 1)
            
            btn_w, btn_h, btn_x = panel_w - 40, 44, panel.left + 20
            y0, spacing = panel.top + 20, 10
            buttons = [
                pygame.Rect(btn_x, y0 + (btn_h+spacing)*i, btn_w, btn_h) for i in range(4)
            ] + [pygame.Rect(btn_x, panel.bottom - 20 - btn_h, btn_w, btn_h)]
            labels = ["[Help]", "[GitHub]", "[Credits]", "[Exit]", "Back to Exploration"]
            
            for rect, label in zip(buttons, labels):
                draw_button(screen, rect, label, menu_font)
            
            if click_pos:
                mx, my = click_pos
                if buttons[0].collidepoint((mx,my)): 
                    state = STATE_HELP
                elif buttons[1].collidepoint((mx,my)): 
                    webbrowser.open(GITHUB_URL)
                elif buttons[2].collidepoint((mx,my)): 
                    state = STATE_CREDITS
                elif buttons[3].collidepoint((mx,my)): 
                    running = False
                elif buttons[4].collidepoint((mx,my)): 
                    state = STATE_RUNNING

            if state == STATE_HELP:
                modal_w, modal_h = 640, 280
                modal = pygame.Rect((SCREEN_W - modal_w)//2, (SCREEN_H - modal_h)//2, modal_w, modal_h)
                pygame.draw.rect(screen, (20,20,20), modal)
                pygame.draw.rect(screen, (255,255,255), modal, 1)
                
                help_text = [
                    "Help", 
                    "", 
                    "Left Click to Drag", 
                    "Scroll to Zoom", 
                    "Right Click an IP for more options",
                    "",
                    "Press Escape to open/close settings"
                ]
                ty = modal.top + 12
                for line in help_text:
                    surf = menu_font.render(line, True, (230,230,230)) if line == "Help" else small_font.render(line, True, (230,230,230))
                    screen.blit(surf, (modal.left + 12, ty))
                    ty += surf.get_height() + 6
                
                close_rect = pygame.Rect(modal.centerx - 60, modal.bottom - 56, 120, 36)
                draw_button(screen, close_rect, "Back to Exploration", small_font)
                if click_pos and close_rect.collidepoint(click_pos): 
                    state = STATE_RUNNING

            elif state == STATE_CREDITS:
                modal_w, modal_h = 640, 280
                modal = pygame.Rect((SCREEN_W - modal_w)//2, (SCREEN_H - modal_h)//2, modal_w, modal_h)
                pygame.draw.rect(screen, (20,20,20), modal)
                pygame.draw.rect(screen, (255,255,255), modal, 1)
                
                credits_text = [
                    "Credits",
                    "",
                    "ViewTheInternet v1.0",
                    "Created by Gallium-Gonzollium",
                    "",
                    "Special thanks to:",
                    "Tom Murphy (http://tom7.org/harder/)for the internet data collected in early 2022",
                    "and the UI inspiration",
                ]
                ty = modal.top + 12
                for line in credits_text:
                    surf = menu_font.render(line, True, (230,230,230)) if line == "Credits" else small_font.render(line, True, (230,230,230))
                    screen.blit(surf, (modal.left + 12, ty))
                    ty += surf.get_height() + 6
                
                close_rect = pygame.Rect(modal.centerx - 60, modal.bottom - 56, 120, 36)
                draw_button(screen, close_rect, "Back to Exploration", small_font)
                if click_pos and close_rect.collidepoint(click_pos): 
                    state = STATE_RUNNING

        elif state == STATE_RUNNING:
            cam.zoom = max(cam.zoom, MIN_ZOOM)
            level = max(0, min(MAX_LEVEL, int(round(-math.log2(cam.zoom)))))
            draw_visible_tiles(screen, cam.x, cam.y, cam.zoom, SCREEN_W, SCREEN_H, level)

            mx, my = pygame.mouse.get_pos()
            mouse_wx, mouse_wy = cam.x + mx / cam.zoom, cam.y + my / cam.zoom
            N = 1 << HILBERT_ORDER
            hx, hy = int(max(0, min(N-1, mouse_wx))), int(max(0, min(N-1, mouse_wy)))
            d = xy2d(N, hx, hy)
            ip_str = int_to_ipv4(d)

            for bs in (BLOCK_SIZE_32, BLOCK_SIZE_24, BLOCK_SIZE_16, BLOCK_SIZE_8):
                bx, by = (hx // bs) * bs, (hy // bs) * bs
                draw_subnet_border(screen, cam.x, cam.y, cam.zoom, SCREEN_W, SCREEN_H, bx, by, bs)

            panels = register_panels_for_mouse(hx, hy, cam.x, cam.y, cam.zoom, SCREEN_W, SCREEN_H, d, ip_str)
            last_lookup_time = schedule_rdap_lookups(ip_str, panels, last_lookup_time, LOOKUP_DEBOUNCE)

            current_panels = panels
            current_ip_int = d
            current_ip_str = ip_str

            if BLOOM_ENABLED:
                tile_layer = pygame.Surface((SCREEN_W, SCREEN_H))
                tile_layer.blit(screen, (0, 0))
                
                apply_bloom(tile_layer, BLOOM_STRENGTH, BLOOM_RADIUS)
                
                screen.fill((0, 0, 0))
                screen.blit(tile_layer, (0, 0))
                
                octet_cache = render_ip_octets(screen, current_ip_str, SCREEN_H, ip_font, octet_cache)
                render_panels(screen, current_panels, cam.x, cam.y, cam.zoom, SCREEN_W, SCREEN_H, panel_text_cache, current_ip_int, current_ip_str)
                hud_render(screen, hud_font, clock, hud_cache, cam.zoom, level)
            else:
                octet_cache = render_ip_octets(screen, current_ip_str, SCREEN_H, ip_font, octet_cache)
                render_panels(screen, current_panels, cam.x, cam.y, cam.zoom, SCREEN_W, SCREEN_H, panel_text_cache, current_ip_int, current_ip_str)
                hud_render(screen, hud_font, clock, hud_cache, cam.zoom, level)

            context_menu.draw(screen)

        pygame.display.flip()

    try:
        from rdap import rdap_q, RDAP_WORKER_SHUTDOWN
        rdap_q.put_nowait(RDAP_WORKER_SHUTDOWN)
    except: 
        pass
    clear_tile_caches()
    pygame.quit()

main()