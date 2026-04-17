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


def main():
    project_root = Path(__file__).resolve().parent.parent
    raw_file = project_root / "data" / "raw" / f"tpc_{CUI}_raw.json"
    output_dir = project_root / "data" / "audits"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_csv = output_dir / f"tpc_{CUI}_receivables_advanced_audit.csv"

    with open(raw_file, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    bilant = raw_data.get("bilanturi_mfinante_scurte", {})
    years = []

    for year_key, year_data in bilant.items():
        if year_key.startswith("an_") and isinstance(year_data, dict):
            years.append({
                "year": int(year_data.get("an") or year_key.replace("an_", "")),
                "creante": get_val(year_data.get("creante")),
                "cifra_afaceri_neta": get_val(year_data.get("cifra_de_afaceri_neta")),
                "venituri_total": get_val(year_data.get("venituri_total")),
            })

    years.sort(key=lambda x: x["year"])
    results = []

    for i, row in enumerate(years):
        creante = row["creante"]
        cifra = row["cifra_afaceri_neta"]
        venituri = row["venituri_total"]

        audit_row = {
            "year": row["year"],
            "creante": creante,
            "cifra_afaceri_neta": cifra,
            "venituri_total": venituri,
            "days_ca_360": None,
            "days_ca_365": None,
            "days_venituri_360": None,
            "days_venituri_365": None,
            "avg_creante_days_ca_360": None,
            "avg_creante_days_ca_365": None,
            "avg_creante_days_venituri_360": None,
            "avg_creante_days_venituri_365": None,
        }

        if creante and cifra:
            audit_row["days_ca_360"] = round((creante / cifra) * 360, 2)
            audit_row["days_ca_365"] = round((creante / cifra) * 365, 2)

        if creante and venituri:
            audit_row["days_venituri_360"] = round((creante / venituri) * 360, 2)
            audit_row["days_venituri_365"] = round((creante / venituri) * 365, 2)

        if i > 0:
            prev_creante = years[i - 1]["creante"]
            if creante and prev_creante:
                avg_creante = (creante + prev_creante) / 2

                if cifra:
                    audit_row["avg_creante_days_ca_360"] = round((avg_creante / cifra) * 360, 2)
                    audit_row["avg_creante_days_ca_365"] = round((avg_creante / cifra) * 365, 2)

                if venituri:
                    audit_row["avg_creante_days_venituri_360"] = round((avg_creante / venituri) * 360, 2)
                    audit_row["avg_creante_days_venituri_365"] = round((avg_creante / venituri) * 365, 2)

        results.append(audit_row)

    with open(output_csv, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)

    print(f"Saved advanced audit to: {output_csv}")
    print("\nRezultate:\n")
    for row in results:
        print(row)


if __name__ == "__main__":
    main()