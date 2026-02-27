import logging

from apscheduler.schedulers.background import BackgroundScheduler

logger = logging.getLogger(__name__)

_scheduler: BackgroundScheduler | None = None


def get_scheduler() -> BackgroundScheduler | None:
    """Return the scheduler instance for adding notification jobs."""
    return _scheduler


def start(refresh_wallpaper_fn, fetch_daily_fn) -> None:
    """Start the background scheduler with two jobs.

    - refresh_wallpaper_fn: called every 60 seconds
    - fetch_daily_fn: called once at midnight daily
    """
    global _scheduler
    _scheduler = BackgroundScheduler()

    _scheduler.add_job(
        refresh_wallpaper_fn,
        "interval",
        seconds=60,
        id="refresh_wallpaper",
        replace_existing=True,
    )

    _scheduler.add_job(
        fetch_daily_fn,
        "cron",
        hour=0,
        minute=1,
        id="fetch_daily",
        replace_existing=True,
    )

    _scheduler.start()
    logger.info("Scheduler started")


def stop() -> None:
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")
        _scheduler = None
