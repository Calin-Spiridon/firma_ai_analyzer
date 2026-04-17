import json
from pathlib import Path

CUI = 27758121

project_root = Path(__file__).resolve().parent.parent
raw_file = project_root / "data" / "raw" / f"tpc_{CUI}_raw.json"

with open(raw_file, "r", encoding="utf-8") as f:
    raw_data = json.load(f)

bilant = raw_data.get("bilanturi_mfinante_scurte", {})

for year_key, year_data in bilant.items():
    if year_key.startswith("an_") and isinstance(year_data, dict):
        print(f"\n{year_key}")
        for k in sorted(year_data.keys()):
            print(" -", k)