# core/utils/settings.py
import os
import json

DEFAULT_SETTINGS = {
    "show_status": False,
    "show_last_message": False
}

def settings_path():
    root = os.environ.get("LLMCUI_ROOT")
    return os.path.join(root, "settings.json")

def load_settings():
    path = settings_path()
    if not os.path.exists(path):
        save_settings(DEFAULT_SETTINGS)
        return DEFAULT_SETTINGS.copy()
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception:
        return DEFAULT_SETTINGS.copy()

def save_settings(data):
    path = settings_path()
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

def update_setting(key, value):
    s = load_settings()
    s[key] = value
    save_settings(s)
    return s
