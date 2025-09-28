import pygame
from config import HILBERT_ORDER, INITIAL_ZOOM, MIN_ZOOM, MAX_ZOOM, ZOOM_FACTOR

class Camera:
    def __init__(self, screen_w: int, screen_h: int):
        self.screen_w, self.screen_h = screen_w, screen_h
        self.zoom = INITIAL_ZOOM
        N = 1 << HILBERT_ORDER
        vw, vh = screen_w / self.zoom, screen_h / self.zoom
        self.x, self.y = (N / 2) - vw / 2, (N / 2) - vh / 2
        self.dragging = False
        self.last_mouse = (0, 0)

    def handle_event(self, ev: pygame.event.Event) -> None:
        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            self.dragging, self.last_mouse = True, ev.pos
        elif ev.type == pygame.MOUSEBUTTONUP and ev.button == 1:
            self.dragging = False
        elif ev.type == pygame.MOUSEMOTION and self.dragging:
            dx, dy = ev.pos[0] - self.last_mouse[0], ev.pos[1] - self.last_mouse[1]
            self.x -= dx / self.zoom
            self.y -= dy / self.zoom
            self.last_mouse = ev.pos
        elif ev.type == pygame.MOUSEWHEEL:
            old_zoom = self.zoom
            self.zoom = max(MIN_ZOOM, min(MAX_ZOOM, old_zoom * (ZOOM_FACTOR ** ev.y)))
            if abs(self.zoom - old_zoom) > 1e-12:
                mx, my = pygame.mouse.get_pos()
                wx, wy = self.x + mx / old_zoom, self.y + my / old_zoom
                self.x, self.y = wx - mx / self.zoom, wy - my / self.zoom