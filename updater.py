import logging
import os
import sys
import tempfile
import zipfile
from typing import Optional

import requests
from winotify import Notification, audio

from config import APP_VERSION, GITHUB_REPO, BASE_DIR

logger = logging.getLogger(__name__)

# GitHub API endpoint
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"

# Update state
_update_available: bool = False
_latest_version: str = ""
_download_url: str = ""


def get_update_state() -> tuple[bool, str]:
    """Return (update_available, latest_version)."""
    return _update_available, _latest_version


def _parse_version(version_str: str) -> tuple[int, ...]:
    """Parse version string like 'v1.2.3' or '1.2.3' into tuple of ints."""
    v = version_str.lstrip("v")
    try:
        return tuple(int(x) for x in v.split("."))
    except (ValueError, AttributeError):
        return (0, 0, 0)


def _is_newer_version(latest: str, current: str) -> bool:
    """Check if latest version is newer than current."""
    return _parse_version(latest) > _parse_version(current)


def check_for_updates() -> tuple[bool, str]:
    """Check GitHub for new releases.

    Returns:
        (update_available, latest_version) tuple.
    """
    global _update_available, _latest_version, _download_url

    try:
        response = requests.get(
            GITHUB_API_URL,
            headers={"Accept": "application/vnd.github.v3+json"},
            timeout=10,
        )
        response.raise_for_status()

        data = response.json()
        _latest_version = data.get("tag_name", "")

        # Find the Windows ZIP asset
        assets = data.get("assets", [])
        for asset in assets:
            name = asset.get("name", "")
            if name.endswith(".zip") and "win" in name.lower():
                _download_url = asset.get("browser_download_url", "")
                break

        if not _download_url and assets:
            # Fallback: use first ZIP asset
            for asset in assets:
                if asset.get("name", "").endswith(".zip"):
                    _download_url = asset.get("browser_download_url", "")
                    break

        _update_available = _is_newer_version(_latest_version, APP_VERSION)

        if _update_available:
            logger.info("Update available: %s -> %s", APP_VERSION, _latest_version)
        else:
            logger.info("App is up to date (v%s)", APP_VERSION)

        return _update_available, _latest_version

    except requests.RequestException as e:
        logger.warning("Failed to check for updates: %s", e)
        return False, ""
    except Exception:
        logger.exception("Error checking for updates")
        return False, ""


def show_update_notification(version: str) -> None:
    """Show a toast notification about available update."""
    try:
        toast = Notification(
            app_id="Waktu Solat",
            title="Update Available",
            msg=f"Version {version} is available. Click 'Update Now' in the tray menu.",
            duration="short",
        )
        toast.set_audio(audio.Default, loop=False)
        toast.show()
    except Exception:
        logger.exception("Failed to show update notification")


def show_no_update_notification() -> None:
    """Show a toast notification that app is up to date."""
    try:
        toast = Notification(
            app_id="Waktu Solat",
            title="No Updates Available",
            msg=f"You're running the latest version ({APP_VERSION}).",
            duration="short",
        )
        toast.show()
    except Exception:
        logger.exception("Failed to show no-update notification")


def _show_progress_notification(message: str) -> None:
    """Show a progress notification."""
    try:
        toast = Notification(
            app_id="Waktu Solat",
            title="Waktu Solat Update",
            msg=message,
            duration="short",
        )
        toast.show()
    except Exception:
        pass


def download_and_apply_update(on_exit_callback) -> bool:
    """Download the update and apply it.

    Args:
        on_exit_callback: Function to call before exiting (cleanup).

    Returns:
        True if update was initiated, False on failure.
    """
    global _download_url, _latest_version

    if not _download_url:
        logger.error("No download URL available")
        return False

    try:
        _show_progress_notification("Downloading update...")
        logger.info("Downloading update from %s", _download_url)

        # Download to temp directory
        temp_dir = tempfile.mkdtemp(prefix="waktusolat_update_")
        zip_path = os.path.join(temp_dir, "update.zip")
        extract_dir = os.path.join(temp_dir, "extracted")

        # Download the ZIP
        response = requests.get(_download_url, stream=True, timeout=120)
        response.raise_for_status()

        with open(zip_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        logger.info("Download complete, extracting...")

        # Extract ZIP
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(extract_dir)

        # Find the extracted folder (usually WaktuSolat/)
        extracted_contents = os.listdir(extract_dir)
        if len(extracted_contents) == 1 and os.path.isdir(os.path.join(extract_dir, extracted_contents[0])):
            source_dir = os.path.join(extract_dir, extracted_contents[0])
        else:
            source_dir = extract_dir

        # Create the batch script for update
        batch_path = os.path.join(temp_dir, "update.bat")
        app_dir = BASE_DIR
        exe_path = os.path.join(app_dir, "WaktuSolat.exe")

        # Batch script content
        batch_content = f'''@echo off
chcp 65001 >nul
echo Waktu Solat Updater
echo Waiting for application to close...
timeout /t 3 /nobreak >nul

echo Copying new files...
xcopy /s /e /y "{source_dir}\\*" "{app_dir}\\" >nul

echo Starting updated application...
start "" "{exe_path}"

echo Cleaning up...
rmdir /s /q "{temp_dir}" 2>nul
del "%~f0" 2>nul
'''

        with open(batch_path, "w", encoding="utf-8") as f:
            f.write(batch_content)

        logger.info("Update prepared, launching updater...")
        _show_progress_notification(f"Installing v{_latest_version}, app will restart...")

        # Launch the batch script
        os.startfile(batch_path)

        # Exit the application
        logger.info("Exiting for update...")
        on_exit_callback()
        sys.exit(0)

    except requests.RequestException as e:
        logger.error("Failed to download update: %s", e)
        _show_progress_notification("Update failed: download error")
        return False
    except zipfile.BadZipFile:
        logger.error("Downloaded file is not a valid ZIP")
        _show_progress_notification("Update failed: invalid file")
        return False
    except Exception:
        logger.exception("Failed to apply update")
        _show_progress_notification("Update failed: unexpected error")
        return False


def get_update_menu_text() -> str:
    """Get the text for the update menu item."""
    if _update_available and _latest_version:
        return f"Update Available ({_latest_version})"
    return f"Version {APP_VERSION} (up to date)"
