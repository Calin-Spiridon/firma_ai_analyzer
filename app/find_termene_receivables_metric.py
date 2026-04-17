import json
import re
from pathlib import Path
from typing import Any


CUI = 27758121

KEYWORDS = [
    "creant",
    "incasar",
    "încasar",
    "zile",
    "days",
    "durata",
    "viteza",
    "rotation",
    "rotatie",
    "rotație",
    "dso",
    "cash",
]


def normalize_number(value):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)

    s = str(value).strip()
    if s in {"", "-", "None", "null"}:
        return None

    s = s.replace(" ", "").replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def walk_json(obj: Any, path="root"):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from walk_json(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from walk_json(v, f"{path}[{i}]")
    else:
        yield path, obj


def looks_relevant(path: str) -> bool:
    p = path.lower()
    return any(keyword in p for keyword in KEYWORDS)


def extract_year_from_path(path: str):
    match = re.search(r"an_(\d{4})", path)
    if match:
        return match.group(1)
    return None


def main():
    project_root = Path(__file__).resolve().parent.parent
    raw_file = project_root / "data" / "raw" / f"tpc_{CUI}_raw.json"
    output_file = project_root / "data" / "audits" / f"tpc_{CUI}_termene_metric_search.json"
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(raw_file, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    matches = []

    for path, value in walk_json(raw_data):
        if looks_relevant(path):
            num = normalize_number(value)
            matches.append({
                "path": path,
                "year": extract_year_from_path(path),
                "raw_value": value,
                "numeric_value": num,
            })

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(matches, f, ensure_ascii=False, indent=2)

    print(f"Saved search output to: {output_file}")
    print("\nPrimele rezultate relevante:\n")
    for row in matches[:100]:
        print(row)


if __name__ == "__main__":
    main()