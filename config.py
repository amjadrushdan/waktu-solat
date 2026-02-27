import ctypes
import os

# App info
APP_VERSION = "1.1.0"
GITHUB_REPO = "amjadrushdan/waktu-solat"

# Location defaults
DEFAULT_CITY = "Kuala Lumpur"
COUNTRY = "Malaysia"
TIMEZONE = "Asia/Kuala_Lumpur"
CALCULATION_METHOD = 3  # Muslim World League

# Available cities (name -> display name for wallpaper)
CITIES = {
    "Kuala Lumpur": "Kuala Lumpur",
    "George Town": "Penang",
    "Johor Bahru": "Johor Bahru",
    "Kuching": "Kuching",
    "Kota Kinabalu": "Kota Kinabalu",
    "Ipoh": "Ipoh",
    "Melaka": "Melaka",
    "Shah Alam": "Shah Alam",
    "Kuantan": "Kuantan",
    "Kota Bharu": "Kota Bharu",
    "Kuala Terengganu": "Kuala Terengganu",
    "Alor Setar": "Alor Setar",
    "Seremban": "Seremban",
    "Putrajaya": "Putrajaya",
}

# Prayer names to display
PRAYER_NAMES = ["Fajr", "Sunrise", "Dhuhr", "Asr", "Maghrib", "Isha"]

# Screen resolution (detect primary monitor, fallback 1920x1080)
try:
    user32 = ctypes.windll.user32
    user32.SetProcessDPIAware()
    SCREEN_WIDTH = user32.GetSystemMetrics(0)
    SCREEN_HEIGHT = user32.GetSystemMetrics(1)
except Exception:
    SCREEN_WIDTH = 1920
    SCREEN_HEIGHT = 1080

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(BASE_DIR, "cache")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
CACHE_FILE = os.path.join(CACHE_DIR, "prayer_times.json")
WALLPAPER_PATH = os.path.join(ASSETS_DIR, "wallpaper.png")
SETTINGS_FILE = os.path.join(CACHE_DIR, "settings.json")
LOG_FILE = os.path.join(BASE_DIR, "waktu_solat.log")

# Ensure directories exist
os.makedirs(CACHE_DIR, exist_ok=True)
os.makedirs(ASSETS_DIR, exist_ok=True)

# Colors
BG_COLOR = "#0d0d0d"
ACCENT_GOLD = "#c9a84c"
WHITE = "#ffffff"
MUTED_TEXT = "#888888"
HIGHLIGHT_BG = "#1a1a1a"

# Font
FONT_PATH = "C:/Windows/Fonts/arial.ttf"
FONT_BOLD_PATH = "C:/Windows/Fonts/arialbd.ttf"
if not os.path.exists(FONT_PATH):
    FONT_PATH = None
if not os.path.exists(FONT_BOLD_PATH):
    FONT_BOLD_PATH = None

# API
API_URL = "http://api.aladhan.com/v1/timingsByCity"

# Single instance port
SINGLE_INSTANCE_PORT = 47832
