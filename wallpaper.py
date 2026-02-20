import ctypes
import logging
import os
from datetime import datetime

from PIL import Image, ImageDraw, ImageFont

from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, WALLPAPER_PATH,
    BG_COLOR, ACCENT_GOLD, WHITE, MUTED_TEXT, HIGHLIGHT_BG,
    FONT_PATH, FONT_BOLD_PATH, PRAYER_NAMES,
)

logger = logging.getLogger(__name__)


def _load_font(bold: bool = False, size: int = 20) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    path = FONT_BOLD_PATH if bold else FONT_PATH
    if path:
        try:
            return ImageFont.truetype(path, size)
        except (IOError, OSError):
            pass
    return ImageFont.load_default()


def generate_wallpaper(
    prayer_times: dict | None,
    next_prayer: str | None,
    countdown: str,
    city_display: str = "",
) -> None:
    """Generate wallpaper image and save to WALLPAPER_PATH."""
    width, height = SCREEN_WIDTH, SCREEN_HEIGHT
    img = Image.new("RGB", (width, height), BG_COLOR)
    draw = ImageDraw.Draw(img)

    # Fonts (scaled relative to height for multi-resolution support)
    scale = height / 1080
    font_date = _load_font(False, int(22 * scale))
    font_title = _load_font(True, int(52 * scale))
    font_prayer = _load_font(False, int(30 * scale))
    font_prayer_bold = _load_font(True, int(32 * scale))
    font_countdown = _load_font(False, int(24 * scale))

    # --- Top-left: Current date ---
    now = datetime.now()
    date_str = now.strftime("%A, %d %B %Y")
    draw.text((int(40 * scale), int(30 * scale)), date_str, fill=MUTED_TEXT, font=font_date)

    # --- Center: Title ---
    title = "Waktu Solat"
    title_bbox = draw.textbbox((0, 0), title, font=font_title)
    title_w = title_bbox[2] - title_bbox[0]
    title_x = (width - title_w) // 2
    title_y = int(height * 0.15)
    draw.text((title_x, title_y), title, fill=ACCENT_GOLD, font=font_title)

    # --- Center: City name under title ---
    if city_display:
        font_city = _load_font(False, int(26 * scale))
        city_bbox = draw.textbbox((0, 0), city_display, font=font_city)
        city_w = city_bbox[2] - city_bbox[0]
        city_x = (width - city_w) // 2
        city_y = title_y + (title_bbox[3] - title_bbox[1]) + int(10 * scale)
        draw.text((city_x, city_y), city_display, fill=MUTED_TEXT, font=font_city)

    # --- Center: Prayer times table ---
    if prayer_times is None:
        # No data available
        no_data_text = "Tiada Sambungan"
        no_data_font = _load_font(True, int(36 * scale))
        nd_bbox = draw.textbbox((0, 0), no_data_text, font=no_data_font)
        nd_w = nd_bbox[2] - nd_bbox[0]
        draw.text(
            ((width - nd_w) // 2, height // 2 - int(20 * scale)),
            no_data_text, fill="#ff4444", font=no_data_font,
        )
    else:
        table_top = int(height * 0.30)
        row_height = int(60 * scale)
        col_name_x = width // 2 - int(200 * scale)
        col_time_x = width // 2 + int(100 * scale)

        for i, name in enumerate(PRAYER_NAMES):
            y = table_top + i * row_height
            is_next = (name == next_prayer)

            # Highlight row for next prayer
            if is_next:
                row_pad = int(10 * scale)
                draw.rounded_rectangle(
                    [
                        col_name_x - int(20 * scale),
                        y - row_pad,
                        col_time_x + int(120 * scale),
                        y + row_height - row_pad,
                    ],
                    radius=int(8 * scale),
                    fill=HIGHLIGHT_BG,
                )

            name_font = font_prayer_bold if is_next else font_prayer
            name_color = ACCENT_GOLD if is_next else WHITE
            time_color = ACCENT_GOLD if is_next else WHITE

            time_str = prayer_times.get(name, "--:--")
            # Strip "(+03)" timezone suffix if present
            if " " in time_str:
                time_str = time_str.split(" ")[0]

            draw.text((col_name_x, y), name, fill=name_color, font=name_font)
            draw.text((col_time_x, y), time_str, fill=time_color, font=name_font)

    # --- Bottom-right: Countdown ---
    if next_prayer and countdown:
        countdown_text = f"Next: {next_prayer} in {countdown}"
        ct_bbox = draw.textbbox((0, 0), countdown_text, font=font_countdown)
        ct_w = ct_bbox[2] - ct_bbox[0]
        draw.text(
            (width - ct_w - int(40 * scale), height - int(60 * scale)),
            countdown_text, fill=ACCENT_GOLD, font=font_countdown,
        )

    img.save(WALLPAPER_PATH, "PNG")
    logger.debug("Wallpaper saved to %s", WALLPAPER_PATH)


def set_wallpaper(path: str | None = None) -> None:
    """Set the given image as the Windows desktop wallpaper (Fill mode)."""
    if path is None:
        path = WALLPAPER_PATH
    abs_path = os.path.abspath(path)

    try:
        import winreg
        # Set wallpaper style to Fill (style=10, tile=0)
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Control Panel\Desktop",
            0,
            winreg.KEY_SET_VALUE,
        )
        winreg.SetValueEx(key, "WallpaperStyle", 0, winreg.REG_SZ, "10")
        winreg.SetValueEx(key, "TileWallpaper", 0, winreg.REG_SZ, "0")
        winreg.CloseKey(key)
    except Exception:
        logger.warning("Could not set wallpaper style registry keys")

    result = ctypes.windll.user32.SystemParametersInfoW(20, 0, abs_path, 3)
    if not result:
        logger.error("SystemParametersInfoW failed to set wallpaper")
    else:
        logger.debug("Wallpaper set to %s", abs_path)
