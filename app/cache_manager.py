import json
import os
from datetime import datetime

CACHE_DIR = "data/cache"


def ensure_cache_dir():
    os.makedirs(CACHE_DIR, exist_ok=True)


def get_cache_path(cui: str) -> str:
    ensure_cache_dir()
    return os.path.join(CACHE_DIR, f"{cui}.json")


def load_from_cache(cui: str):
    path = get_cache_path(cui)
    if not os.path.exists(path):
        return None

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_to_cache(cui: str, payload: dict):
    path = get_cache_path(cui)

    wrapper = {
        "cached_at": datetime.now().isoformat(),
        "data": payload
    }

    with open(path, "w", encoding="utf-8") as f:
        json.dump(wrapper, f, indent=2, ensure_ascii=False)