"""Find project files both when running from source and inside the packaged app.

PyInstaller unpacks bundled files into a temp folder and stores its path in
sys._MEIPASS, so every file path must go through resource_path().
"""
import json
import os
import sys

BASE_DIR = getattr(sys, "_MEIPASS", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def resource_path(*parts):
    return os.path.join(BASE_DIR, *parts)


# ---------- per-user saved options (volume, fullscreen, last IP...) ----------
_PREFS_FILE = os.path.join(os.path.expanduser("~"), ".drift_tank.json")
_DEFAULT_PREFS = {"volume": 0.7, "fullscreen": False, "last_ip": "", "show_fps": False, "name": ""}


def load_prefs():
    prefs = dict(_DEFAULT_PREFS)
    try:
        with open(_PREFS_FILE) as f:
            prefs.update(json.load(f))
    except (OSError, ValueError):
        pass
    return prefs


def save_prefs(prefs):
    try:
        with open(_PREFS_FILE, "w") as f:
            json.dump(prefs, f)
    except OSError:
        pass
