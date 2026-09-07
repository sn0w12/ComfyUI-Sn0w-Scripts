import json
import os
from pathlib import Path

from ..sn0w import Logger

PRESETS_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "web",
    "settings",
    "lora_presets.json",
)
MAX_PRESET_DEPTH = 5
logger = Logger()


def normalize_loader_path(folders):
    return ",".join(Path(folder).as_posix().lower() for folder in folders)


def build_lora_loader_info(node_class_mappings):
    info = {}
    for name, node_class in node_class_mappings.items():
        combos = getattr(node_class, "LORA_COMBOS", 1)
        folders = getattr(node_class, "LORA_PATH", None)
        if combos > 1 and folders:
            info[name] = {"path": normalize_loader_path(folders), "combos": combos}
    return info


def presets_for_path(path):
    return [preset for preset in load_presets() if preset.get("path") == path]


def find_preset(path, name):
    return next((preset for preset in presets_for_path(path) if preset.get("name") == name), None)


def load_presets():
    if not os.path.exists(PRESETS_FILE):
        return []
    try:
        with open(PRESETS_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, IOError):
        logger.log(f"Failed to read lora presets from {PRESETS_FILE}", "WARNING")
        return []


def save_preset(name, path, loras):
    presets = [p for p in load_presets() if not (p.get("name") == name and p.get("path") == path)]
    presets.append({"name": name, "path": path, "loras": loras})
    os.makedirs(os.path.dirname(PRESETS_FILE), exist_ok=True)
    try:
        with open(PRESETS_FILE, "w", encoding="utf-8") as file:
            json.dump(presets, file, indent=2)
        return True
    except IOError:
        logger.log(f"Failed to write lora presets to {PRESETS_FILE}", "ERROR")
        return False