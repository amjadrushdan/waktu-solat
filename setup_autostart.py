import os
import subprocess
import sys

TASK_NAME = "WaktuSolatWallpaper"


def _get_app_command() -> str:
    """Return the command string to launch the app."""
    if getattr(sys, "frozen", False):
        # Running as packaged .exe
        return f'"{sys.executable}"'
    else:
        # Running from source
        python_exe = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
        script_path = os.path.abspath("main.py")
        return f'"{python_exe}" "{script_path}"'


def _get_working_dir() -> str:
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath("main.py"))


def register_task():
    """Try Task Scheduler first, fall back to Startup folder."""
    app_cmd = _get_app_command()

    # Delete existing task if any
    subprocess.run(
        ["schtasks", "/Delete", "/TN", TASK_NAME, "/F"],
        capture_output=True,
    )

    # Create new task: run at logon, with delay of 30s
    cmd = [
        "schtasks", "/Create",
        "/TN", TASK_NAME,
        "/TR", app_cmd,
        "/SC", "ONLOGON",
        "/DELAY", "0000:30",
        "/RL", "HIGHEST",
        "/F",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        print(f"[OK] Task '{TASK_NAME}' registered successfully.")
        print("App will auto-start 30 seconds after every login.")
    else:
        print(f"[WARN] Task Scheduler failed:\n{result.stderr}")
        print("Falling back to Startup folder method...")
        register_startup_folder_fallback()


def register_startup_folder_fallback():
    """Create a .vbs launcher in the Windows Startup folder."""
    startup_dir = os.path.join(
        os.environ["APPDATA"],
        r"Microsoft\Windows\Start Menu\Programs\Startup",
    )
    working_dir = _get_working_dir()
    app_cmd = _get_app_command()
    vbs_path = os.path.join(startup_dir, "WaktuSolat.vbs")

    vbs_content = (
        f'Set WshShell = CreateObject("WScript.Shell")\n'
        f'WshShell.CurrentDirectory = "{working_dir}"\n'
        f'WshShell.Run "{app_cmd}", 0, False\n'
    )
    with open(vbs_path, "w") as f:
        f.write(vbs_content)
    print(f"[OK] Startup shortcut created at: {vbs_path}")


def unregister_task():
    """Remove both Task Scheduler task and Startup folder shortcut."""
    # Remove scheduled task
    result = subprocess.run(
        ["schtasks", "/Delete", "/TN", TASK_NAME, "/F"],
        capture_output=True, text=True,
    )
    if result.returncode == 0:
        print(f"[OK] Task '{TASK_NAME}' removed.")
    else:
        print(f"[INFO] No scheduled task found: {result.stderr.strip()}")

    # Remove startup shortcut if exists
    startup_vbs = os.path.join(
        os.environ["APPDATA"],
        r"Microsoft\Windows\Start Menu\Programs\Startup",
        "WaktuSolat.vbs",
    )
    if os.path.exists(startup_vbs):
        os.remove(startup_vbs)
        print(f"[OK] Startup shortcut removed: {startup_vbs}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "remove":
        unregister_task()
    else:
        register_task()
