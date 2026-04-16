def extract_last_5_years_from_api(response_data: dict) -> dict:
    bilanturi = response_data.get("bilanturi_mfinante_scurte", {})

    valid_years = []

    for key, value in bilanturi.items():
        if key.startswith("an_") and isinstance(value, dict) and value:
            try:
                year = int(key.replace("an_", ""))
                valid_years.append(year)
            except ValueError:
                pass

    valid_years = sorted(valid_years, reverse=True)[:5]
    valid_years = sorted(valid_years)

    result = {}
    for year in valid_years:
        result[year] = bilanturi[f"an_{year}"]

    return result


def extract_company_info(response_data: dict) -> dict:
    firma = response_data.get("firma", {})
    cod_caen = response_data.get("cod_caen", {})

    principal = cod_caen.get("principal_recom", {})
    if not principal:
        principal = cod_caen.get("principal", {})
    if not principal and isinstance(cod_caen, dict):
        principal = cod_caen

    return {
        "company_name": firma.get("nume_mfinante") or firma.get("nume") or "-",
        "cui": firma.get("cui") or "-",
        "caen_code": principal.get("cod") or "-",
        "caen_label": principal.get("label") or principal.get("denumire") or "-",
    }