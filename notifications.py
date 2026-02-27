import logging
from datetime import datetime, timedelta

from winotify import Notification, audio

logger = logging.getLogger(__name__)

# Minutes before prayer to send notification
NOTIFY_BEFORE_MINUTES = 10

# Job ID prefix for notification jobs
NOTIFICATION_JOB_PREFIX = "notify_"


def show_notification(prayer_name: str, minutes_until: int = NOTIFY_BEFORE_MINUTES) -> None:
    """Display a Windows toast notification for upcoming prayer."""
    try:
        toast = Notification(
            app_id="Waktu Solat",
            title=f"{prayer_name} in {minutes_until} minutes",
            msg="Time to prepare for prayer",
            duration="short",
        )
        toast.set_audio(audio.Default, loop=False)
        toast.show()
        logger.info("Notification shown for %s", prayer_name)
    except Exception:
        logger.exception("Failed to show notification for %s", prayer_name)


def schedule_prayer_notifications(scheduler, prayer_times: dict) -> None:
    """Schedule notifications for all upcoming prayers.

    Clears existing notification jobs and schedules new ones
    for prayers that haven't passed yet.
    """
    if not prayer_times:
        return

    # Clear existing notification jobs
    clear_notification_jobs(scheduler)

    now = datetime.now()
    prayers_to_notify = ["Fajr", "Dhuhr", "Asr", "Maghrib", "Isha"]  # Skip Sunrise

    for prayer_name in prayers_to_notify:
        time_str = prayer_times.get(prayer_name, "")
        if " " in time_str:
            time_str = time_str.split(" ")[0]

        try:
            h, m = time_str.split(":")
            prayer_dt = now.replace(hour=int(h), minute=int(m), second=0, microsecond=0)
            notify_dt = prayer_dt - timedelta(minutes=NOTIFY_BEFORE_MINUTES)

            # Only schedule if notification time is in the future
            if notify_dt > now:
                job_id = f"{NOTIFICATION_JOB_PREFIX}{prayer_name}"
                scheduler.add_job(
                    show_notification,
                    "date",
                    run_date=notify_dt,
                    args=[prayer_name, NOTIFY_BEFORE_MINUTES],
                    id=job_id,
                    replace_existing=True,
                )
                logger.info(
                    "Scheduled notification for %s at %s",
                    prayer_name,
                    notify_dt.strftime("%H:%M"),
                )
        except (ValueError, AttributeError):
            logger.warning("Could not parse time for %s: %s", prayer_name, time_str)
            continue


def clear_notification_jobs(scheduler) -> None:
    """Remove all existing notification jobs from the scheduler."""
    jobs = scheduler.get_jobs()
    for job in jobs:
        if job.id.startswith(NOTIFICATION_JOB_PREFIX):
            job.remove()
            logger.debug("Removed notification job: %s", job.id)
