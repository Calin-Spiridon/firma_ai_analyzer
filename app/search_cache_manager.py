import os
import json
import hashlib
from datetime import datetime

SEARCH_CACHE_DIR = "data/search_cache"
os.makedirs(SEARCH_CACHE_DIR, exist_ok=True)


def _normalize_filters(filters: dict) -> dict:
    return {
        "county": filters.get("county") or None,
        "min_turnover": filters.get("min_turnover") or None,
        "min_employees": filters.get("min_employees") or None,
    }


def build_search_cache_key(filters: dict) -> str:
    normalized = _normalize_filters(filters)
    raw = json.dumps(normalized, sort_keys=True, ensure_ascii=False)
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def get_search_cache_path(filters: dict) -> str:
    key = build_search_cache_key(filters)
    return os.path.join(SEARCH_CACHE_DIR, f"{key}.json")


def save_search_snapshot(filters: dict, results: list[dict], next_index_to_enrich: int = 0):
    now = datetime.utcnow().isoformat()

    payload = {
        "filters": _normalize_filters(filters),
        "created_at": now,
        "last_updated_at": now,
        "total_results": len(results),
        "sorted_by": "turnover_desc",
        "next_index_to_enrich": next_index_to_enrich,
        "results": results,
    }

    path = get_search_cache_path(filters)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def load_search_snapshot(filters: dict):
    path = get_search_cache_path(filters)
    if not os.path.exists(path):
        return None

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def update_search_snapshot(filters: dict, snapshot: dict):
    snapshot["last_updated_at"] = datetime.utcnow().isoformat()
    path = get_search_cache_path(filters)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, ensure_ascii=False, indent=2)