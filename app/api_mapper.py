def extract_available_years_from_api(response_data: dict) -> dict:
    bilanturi = response_data.get("bilanturi_mfinante_scurte", {})

    result = {}

    for key, value in bilanturi.items():
        if not key.startswith("an_"):
            continue

        if not isinstance(value, dict) or not value:
            continue

        try:
            year = int(key.replace("an_", ""))
        except ValueError:
            continue

        result[year] = value

    return dict(sorted(result.items()))


def extract_last_5_years_from_api(response_data: dict) -> dict:
    """
    Compatibilitate backward.
    În noua logică nu mai tăiem aici ultimii 5 ani brut.
    Returnăm toți anii disponibili, iar selecția finală se face ulterior
    în analysis_service.py pe baza anului oficial eligibil.
    """
    return extract_available_years_from_api(response_data)


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