import json
import logging
import os
from datetime import datetime, timedelta

import requests

from config import (
    API_URL, CACHE_FILE, COUNTRY,
    CALCULATION_METHOD, PRAYER_NAMES, DEFAULT_CITY,
)

logger = logging.getLogger(__name__)


def _load_cache() -> dict:
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            logger.warning("Failed to read cache file")
    return {}


def _save_cache(cache: dict) -> None:
    try:
        with open(CACHE_FILE, "w") as f:
            json.dump(cache, f, indent=2)
    except IOError:
        logger.error("Failed to write cache file")


def _fetch_from_api(date_str: str, city: str) -> dict | None:
    """Fetch prayer times from Aladhan API for a given date (DD-MM-YYYY) and city."""
    try:
        resp = requests.get(
            API_URL,
            params={
                "city": city,
                "country": COUNTRY,
                "method": CALCULATION_METHOD,
                "date": date_str,
            },
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        timings = data["data"]["timings"]
        return {name: timings[name] for name in PRAYER_NAMES}
    except Exception:
        logger.exception("API fetch failed for %s / %s", city, date_str)
        return None


def get_prayer_times(date: datetime | None = None, city: str | None = None) -> dict | None:
    """Get prayer times for the given date and city.

    Returns a dict like {"Fajr": "05:42", "Sunrise": "07:01", ...} or None.
    Uses cache first, falls back to API, then previous day's cache.
    Cache is keyed by city+date to support switching.
    """
    if date is None:
        date = datetime.now()
    if city is None:
        city = DEFAULT_CITY

    date_str = date.strftime("%Y-%m-%d")
    api_date = date.strftime("%d-%m-%Y")
    cache_key = f"{city}|{date_str}"

    cache = _load_cache()

    # Check cache
    if cache_key in cache:
        logger.info("Using cached prayer times for %s", cache_key)
        return cache[cache_key]

    # Fetch from API
    times = _fetch_from_api(api_date, city)
    if times:
        cache[cache_key] = times
        _save_cache(cache)
        logger.info("Fetched and cached prayer times for %s", cache_key)
        return times

    # Fallback: try previous day's cache for same city
    prev_date = (date - timedelta(days=1)).strftime("%Y-%m-%d")
    prev_key = f"{city}|{prev_date}"
    if prev_key in cache:
        logger.warning("Using previous day's cache as fallback for %s", cache_key)
        return cache[prev_key]

    logger.error("No prayer times available for %s", cache_key)
    return None
