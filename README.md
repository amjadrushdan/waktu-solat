# Waktu Solat

A Windows desktop app that displays Malaysian prayer times on your wallpaper with a live countdown in the system tray.

## Features

- Fetches daily prayer times from the Aladhan API
- Generates a clean, dark-themed wallpaper with all 6 prayer times
- Highlights the next upcoming prayer with a gold accent
- System tray icon with a live countdown tooltip (updates every second)
- Supports 14 Malaysian cities, switchable from the tray menu
- City preference is saved and restored on restart
- Auto-refreshes wallpaper every 60 seconds
- Re-fetches prayer times daily at midnight
- Single-instance guard prevents duplicate processes
- Optional auto-start on Windows login

## Screenshot

![Waktu Solat Wallpaper](https://raw.githubusercontent.com/amjadrushdan/waktu-solat/main/assets/app.ico)

## Supported Cities

Kuala Lumpur, Penang, Johor Bahru, Kuching, Kota Kinabalu, Ipoh, Melaka, Shah Alam, Kuantan, Kota Bharu, Kuala Terengganu, Alor Setar, Seremban, Putrajaya

## Installation

### Option 1: Download the exe (recommended)

1. Go to [Releases](https://github.com/amjadrushdan/waktu-solat/releases/latest)
2. Download `WaktuSolat-win64.zip`
3. Extract the zip to any folder
4. Run `WaktuSolat.exe`

### Option 2: Run from source

Requires Python 3.11+.

```bash
git clone https://github.com/amjadrushdan/waktu-solat.git
cd waktu-solat
pip install -r requirements.txt
pythonw main.py
```

## Usage

Once running, the app sits in the system tray as a gold crescent icon.

Right-click the tray icon for options:

- **City** - Select your city from the submenu
- **Refresh Now** - Manually regenerate the wallpaper
- **Exit** - Stop the app

The wallpaper updates automatically every minute. The tray tooltip shows the next prayer name and a live countdown.

## Auto-start on Login

To start the app automatically when you log in to Windows, run the setup script as Administrator:

```bash
python setup_autostart.py
```

This registers a Windows Task Scheduler task. If that fails (no admin rights), it falls back to placing a launcher in the Startup folder.

To remove auto-start:

```bash
python setup_autostart.py remove
```

## Building from Source

To build the standalone exe yourself:

```bash
pip install pyinstaller
python build_icon.py
pyinstaller waktu_solat.spec
```

The output will be in `dist/WaktuSolat/`.

## Project Structure

```
waktu-solat/
  main.py             Entry point, orchestrates everything
  api.py              Aladhan API fetching and caching
  wallpaper.py        Wallpaper image generation (Pillow)
  tray.py             System tray icon (pystray)
  scheduler.py        Background scheduling (APScheduler)
  config.py           Constants and configuration
  setup_autostart.py  Windows auto-start registration
  build_icon.py       Generates the app icon
  waktu_solat.spec    PyInstaller build spec
  requirements.txt    Python dependencies
  assets/
    app.ico           Application icon
  cache/
    prayer_times.json Cached prayer times (auto-generated)
    settings.json     User preferences (auto-generated)
```

## Dependencies

- [requests](https://pypi.org/project/requests/) - HTTP client for API calls
- [Pillow](https://pypi.org/project/Pillow/) - Image generation
- [pystray](https://pypi.org/project/pystray/) - System tray icon
- [APScheduler](https://pypi.org/project/APScheduler/) - Background job scheduling
- [pywin32](https://pypi.org/project/pywin32/) - Windows API bindings

## API

Prayer times are sourced from [Aladhan](https://aladhan.com/prayer-times-api) using the Muslim World League calculation method (method 3).

## License

MIT
