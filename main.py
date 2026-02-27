import json
import logging
import os
import socket
import sys
from datetime import datetime, timedelta

from config import (
    SINGLE_INSTANCE_PORT, LOG_FILE, DEFAULT_CITY,
    SETTINGS_FILE, CITIES,
)

# Configure logging
_log_handlers = [logging.FileHandler(LOG_FILE, encoding="utf-8")]
if not getattr(sys, "frozen", False):
    _log_handlers.append(logging.StreamHandler())
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=_log_handlers,
)
logger = logging.getLogger(__name__)


def enforce_single_instance():
    """Bind a socket as a mutex. Exits if another instance is running."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(("127.0.0.1", SINGLE_INSTANCE_PORT))
        return sock
    except OSError:
        print("Another instance is already running. Exiting.")
        sys.exit(0)


# --- Settings persistence ---

def _load_settings() -> dict:
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {}


def _save_settings(settings: dict) -> None:
    try:
        with open(SETTINGS_FILE, "w") as f:
            json.dump(settings, f, indent=2)
    except IOError:
        logger.error("Failed to save settings")


# --- App state ---
_prayer_times: dict | None = None
_next_prayer_name: str | None = None
_next_prayer_time: datetime | None = None
_current_city: str = DEFAULT_CITY


def get_current_city() -> str:
    return _current_city


def get_next_prayer(prayer_times: dict) -> tuple[str, datetime]:
    """Return (prayer_name, prayer_datetime) for the next upcoming prayer."""
    from api import get_prayer_times as fetch_times

    now = datetime.now()

    for name in ["Fajr", "Sunrise", "Dhuhr", "Asr", "Maghrib", "Isha"]:
        time_str = prayer_times.get(name, "")
        if " " in time_str:
            time_str = time_str.split(" ")[0]
        try:
            h, m = time_str.split(":")
            prayer_dt = now.replace(hour=int(h), minute=int(m), second=0, microsecond=0)
            if prayer_dt > now:
                return name, prayer_dt
        except (ValueError, AttributeError):
            continue

    # All prayers passed — get tomorrow's Fajr
    tomorrow = now + timedelta(days=1)
    tomorrow_times = fetch_times(tomorrow, city=_current_city)
    if tomorrow_times:
        fajr_str = tomorrow_times.get("Fajr", "")
        if " " in fajr_str:
            fajr_str = fajr_str.split(" ")[0]
        try:
            h, m = fajr_str.split(":")
            fajr_dt = tomorrow.replace(hour=int(h), minute=int(m), second=0, microsecond=0)
            return "Fajr", fajr_dt
        except (ValueError, AttributeError):
            pass

    # Ultimate fallback
    fajr_str = prayer_times.get("Fajr", "05:30")
    if " " in fajr_str:
        fajr_str = fajr_str.split(" ")[0]
    try:
        h, m = fajr_str.split(":")
        fajr_dt = (now + timedelta(days=1)).replace(
            hour=int(h), minute=int(m), second=0, microsecond=0
        )
        return "Fajr", fajr_dt
    except (ValueError, AttributeError):
        return "Fajr", now + timedelta(hours=6)


def get_countdown(next_prayer_time: datetime) -> str:
    """Return countdown string in HH:MM:SS format."""
    delta = next_prayer_time - datetime.now()
    if delta.total_seconds() < 0:
        return "00:00:00"
    total_secs = int(delta.total_seconds())
    hours = total_secs // 3600
    minutes = (total_secs % 3600) // 60
    seconds = total_secs % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def _update_next_prayer():
    global _next_prayer_name, _next_prayer_time
    if _prayer_times:
        _next_prayer_name, _next_prayer_time = get_next_prayer(_prayer_times)


def refresh_wallpaper():
    """Regenerate wallpaper with current prayer data and set it."""
    from wallpaper import generate_wallpaper, set_wallpaper

    _update_next_prayer()
    countdown = ""
    if _next_prayer_time:
        countdown = get_countdown(_next_prayer_time)

    city_display = CITIES.get(_current_city, _current_city)

    try:
        generate_wallpaper(_prayer_times, _next_prayer_name, countdown, city_display)
        set_wallpaper()
    except Exception:
        logger.exception("Failed to refresh wallpaper")


def fetch_daily():
    """Fetch today's prayer times from API for the current city."""
    global _prayer_times
    from api import get_prayer_times as fetch_times

    times = fetch_times(city=_current_city)
    if times:
        _prayer_times = times
        logger.info("Daily prayer times updated for %s", _current_city)
        _schedule_notifications()
    else:
        logger.warning("Failed to fetch daily prayer times for %s", _current_city)


def _schedule_notifications():
    """Schedule prayer notifications based on current prayer times."""
    import scheduler
    from notifications import schedule_prayer_notifications

    sched = scheduler.get_scheduler()
    if sched and _prayer_times:
        schedule_prayer_notifications(sched, _prayer_times)


def on_city_change(city_key: str):
    """Handle city switch from tray menu."""
    global _current_city
    if city_key == _current_city:
        return

    _current_city = city_key
    logger.info("City changed to: %s", city_key)

    # Persist choice
    settings = _load_settings()
    settings["city"] = city_key
    _save_settings(settings)

    # Re-fetch and refresh immediately
    fetch_daily()
    refresh_wallpaper()


def get_tray_info() -> tuple[str | None, str | None]:
    """Return (next_prayer_name, countdown_str) for the tray tooltip."""
    _update_next_prayer()
    if _next_prayer_name and _next_prayer_time:
        return _next_prayer_name, get_countdown(_next_prayer_time)
    return None, None


def on_exit():
    """Clean shutdown."""
    import scheduler
    scheduler.stop()
    logger.info("App exiting")


def _check_updates_background():
    """Check for updates in the background and notify if available."""
    import updater
    has_update, version = updater.check_for_updates()
    if has_update:
        updater.show_update_notification(version)


def main():
    global _current_city

    import scheduler
    from tray import create_tray

    _lock = enforce_single_instance()

    logger.info("Waktu Solat starting...")

    # Load saved city preference
    settings = _load_settings()
    saved_city = settings.get("city")
    if saved_city and saved_city in CITIES:
        _current_city = saved_city
        logger.info("Restored city preference: %s", _current_city)

    # 1. Fetch today's prayer times
    fetch_daily()

    # 2. Generate and set wallpaper immediately
    refresh_wallpaper()

    # 3. Start scheduler
    scheduler.start(refresh_wallpaper, fetch_daily)

    # 4. Check for updates in the background (non-blocking)
    import threading
    update_thread = threading.Thread(target=_check_updates_background, daemon=True)
    update_thread.start()

    # 5. Start tray icon (blocking)
    try:
        create_tray(get_tray_info, refresh_wallpaper, on_exit, on_city_change, get_current_city)
    except KeyboardInterrupt:
        on_exit()


if __name__ == "__main__":
    main()
