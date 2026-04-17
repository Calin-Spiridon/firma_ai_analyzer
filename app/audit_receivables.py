import json
import csv
from pathlib import Path


CUI = 27758121


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


def get_val(node, key="valoare"):
    if isinstance(node, dict):
        return normalize_number(node.get(key))
    return normalize_number(node)


def build_audit():
    project_root = Path(__file__).resolve().parent.parent
    raw_file = project_root / "data" / "raw" / f"tpc_{CUI}_raw.json"
    output_dir = project_root / "data" / "audits"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_json = output_dir / f"tpc_{CUI}_receivables_audit.json"
    output_csv = output_dir / f"tpc_{CUI}_receivables_audit.csv"

    with open(raw_file, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    bilant = raw_data.get("bilanturi_mfinante_scurte", {})
    results = []

    for year_key, year_data in bilant.items():
        if not year_key.startswith("an_"):
            continue
        if not isinstance(year_data, dict):
            continue

        year = int(year_data.get("an") or year_key.replace("an_", ""))

        creante = get_val(year_data.get("creante"))
        cifra_afaceri = get_val(year_data.get("cifra_de_afaceri_neta"))
        venituri_total = get_val(year_data.get("venituri_total"))
        data_actualizare = year_data.get("data_actualizare")
        tip_bilant = year_data.get("tip_bilant")

        row = {
            "year": year,
            "data_actualizare": data_actualizare,
            "tip_bilant": tip_bilant,
            "creante": creante,
            "cifra_afaceri_neta": cifra_afaceri,
            "venituri_total": venituri_total,
            "zile_ca_360": None,
            "zile_ca_365": None,
            "zile_venituri_360": None,
            "zile_venituri_365": None,
        }

        if creante and cifra_afaceri:
            row["zile_ca_360"] = round((creante / cifra_afaceri) * 360, 2)
            row["zile_ca_365"] = round((creante / cifra_afaceri) * 365, 2)

        if creante and venituri_total:
            row["zile_venituri_360"] = round((creante / venituri_total) * 360, 2)
            row["zile_venituri_365"] = round((creante / venituri_total) * 365, 2)

        results.append(row)

    results.sort(key=lambda x: x["year"])

    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    with open(output_csv, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)

    print(f"Audit JSON saved to: {output_json}")
    print(f"Audit CSV saved to: {output_csv}")
    print("\nRezultate pe ani:\n")
    for row in results:
        print(row)


if __name__ == "__main__":
    build_audit()