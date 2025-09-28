# Clipmap Settings - don't touch unless you know what you're doing!
TILE_SIZE = 256
MAX_LEVEL = 8
HILBERT_ORDER, ZOOM_FACTOR = 16, 2
MAX_CACHE_ITEMS = 1024
MIN_ZOOM, MAX_ZOOM, INITIAL_ZOOM = 1/256, 16, 1/64

# Colors
COLOR_OCTET_1, COLOR_OCTET_2   = "#f76a81", "#85fa6e"
COLOR_OCTET_3, COLOR_OCTET_4   = "#f869b2", "#ffffff"
COLOR_DOTS,    COLOR_BORDER    = "#9aa0bc", "#ff00ff"
COLOR_INFO_BG, COLOR_INFO_TEXT = "#101216", "#ebebeb"

# Subnet block sizes
BLOCK_SIZE_32, BLOCK_SIZE_24, BLOCK_SIZE_16, BLOCK_SIZE_8 = 1, 16, 256, 4096
SUBNET_BORDER_WIDTH = 2

# Font config
# Use FONT_PATH for a font path, else if you want an installed font use FONT_NAME
FONT_PATH, FONT_NAME = "Jersey10-Regular.ttf", None
MIN_FONT_SIZE, MIN_RENDER_PIXELS, MAX_RENDER_PIXELS = 20, 48, 1200
PANEL_PADDING, FONT_SCALE_MULTIPLIER = 8, 0.08

# RDAP stuffs
RDAP_ENDPOINTS = [
    "https://rdap.arin.net/registry/ip/{}",
    "https://rdap.db.ripe.net/ip/{}", 
    "https://rdap.apnic.net/ip/{}",
    "https://rdap.lacnic.net/rdap/ip/{}",
    "https://rdap.afrinic.net/rdap/ip/{}",
    "https://client.rdap.org/?object={}&type=ip"
]
RDAP_REQUEST_TIMEOUT, RDAP_WORKER_THROTTLE, LOOKUP_DEBOUNCE = 6.0, 0.05, 0.35

# Bloom PPE
BLOOM_ENABLED, BLOOM_STRENGTH, BLOOM_RADIUS = True, 0.5, 16