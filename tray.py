import logging
import time

import pystray
from PIL import Image, ImageDraw

from config import CITIES

logger = logging.getLogger(__name__)


def _create_crescent_icon(size: int = 64) -> Image.Image:
    """Generate a simple gold crescent moon icon."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # Outer circle (gold)
    pad = 4
    draw.ellipse([pad, pad, size - pad, size - pad], fill="#c9a84c")
    # Inner circle offset to create crescent
    offset = int(size * 0.25)
    draw.ellipse(
        [pad + offset, pad - 2, size - pad + offset, size - pad - 2],
        fill=(0, 0, 0, 0),
    )
    return img


def create_tray(get_next_prayer_fn, on_refresh, on_exit, on_city_change, get_current_city_fn):
    """Create and run the system tray icon.

    Args:
        get_next_prayer_fn: Callable returning (prayer_name, countdown_str) or (None, None).
        on_refresh: Callable to trigger manual wallpaper refresh.
        on_exit: Callable to trigger clean app shutdown.
        on_city_change: Callable(city_key) to switch city.
        get_current_city_fn: Callable returning current city key string.

    This function blocks (runs the tray message loop).
    """
    icon_image = _create_crescent_icon()

    def _quit(icon, item):
        icon.visible = False
        icon.stop()
        on_exit()

    def _refresh(icon, item):
        on_refresh()

    def _make_city_callback(city_key):
        def _cb(icon, item):
            on_city_change(city_key)
        return _cb

    def _is_current_city(city_key):
        def _check(item):
            return get_current_city_fn() == city_key
        return _check

    # Build city submenu items
    city_items = []
    for city_key, display_name in CITIES.items():
        city_items.append(
            pystray.MenuItem(
                display_name,
                _make_city_callback(city_key),
                checked=_is_current_city(city_key),
                radio=True,
            )
        )

    menu = pystray.Menu(
        pystray.MenuItem("City", pystray.Menu(*city_items)),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Refresh Now", _refresh),
        pystray.MenuItem("Exit", _quit),
    )

    icon = pystray.Icon(
        name="waktu-solat",
        icon=icon_image,
        title="Waktu Solat - Loading...",
        menu=menu,
    )

    def _update_loop(icon):
        icon.visible = True
        while icon.visible:
            try:
                name, countdown = get_next_prayer_fn()
                if name and countdown:
                    icon.title = f"{name} in {countdown}"
                else:
                    icon.title = "Waktu Solat"
            except Exception:
                logger.exception("Error updating tray tooltip")
                icon.title = "Waktu Solat"
            time.sleep(1)

    icon.run(setup=_update_loop)
