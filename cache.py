import os
from collections import OrderedDict
import pygame
from config import MAX_CACHE_ITEMS

class LRUCache:
    def __init__(self, max_items=MAX_CACHE_ITEMS):
        self.max_items = max_items
        self.od = OrderedDict()

    def get(self, key):
        if key in self.od:
            self.od.move_to_end(key)
            return self.od[key]

    def put(self, key, value):
        self.od[key] = value
        self.od.move_to_end(key)
        if len(self.od) > self.max_items:
            self.od.popitem(last=False)

    def contains(self, key):
        return key in self.od

    def clear(self):
        self.od.clear()

_tile_cache = LRUCache()
_scaled_tile_cache = LRUCache(max_items=MAX_CACHE_ITEMS * 4)

def load_tile(level, tx, ty):
    key = (level, tx, ty)
    if (cached := _tile_cache.get(key)) is not None:
        return cached
        
    fn = os.path.join(f"level{level}", f"tile_{tx}_{ty}.png")
    if not os.path.isfile(fn):
        _tile_cache.put(key, None)
        return None
        
    try:
        s = pygame.image.load(fn).convert()
    except Exception:
        _tile_cache.put(key, None)
        return None
            
    _tile_cache.put(key, s)
    return s

def get_scaled_tile(level, tx, ty, w, h):
    key = (level, tx, ty, int(w), int(h))
    if cached := _scaled_tile_cache.get(key):
        return cached
        
    if not (base := load_tile(level, tx, ty)):
        _scaled_tile_cache.put(key, None)
        return None
        
    try:
        scaled = pygame.transform.scale(base, (int(w), int(h)))
    except Exception:
        scaled = base
        
    _scaled_tile_cache.put(key, scaled)
    return scaled

def clear_tile_caches():
    _tile_cache.clear()
    _scaled_tile_cache.clear()