import json
from pathlib import Path

from app.termene_client import TermeneClient
from app.config import TERMENE_SCHEMA_KEY_COMPANY


CUI = 27758121


def export_raw_company_data(cui: int = CUI):
    project_root = Path(__file__).resolve().parent.parent
    output_dir = project_root / "data" / "raw"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / f"tpc_{cui}_raw.json"

    client = TermeneClient()
    raw_data = client.fetch_schema(
        cui=cui,
        schema_key=TERMENE_SCHEMA_KEY_COMPANY,
    )

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(raw_data, f, ensure_ascii=False, indent=2)

    print(f"Raw data saved to: {output_file}")


if __name__ == "__main__":
    export_raw_company_data()