from app.analysis_service import build_company_analysis
from app.config import TERMENE_SCHEMA_KEY_COMPANY
from app.termene_client import TermeneClient
from app.termene_enrichment_mapper import (
    extract_company_contact_info,
    extract_shareholders,
)


def enrich_company_by_cui(cui: int) -> dict:
    """
    Îmbogățește o companie pe baza CUI-ului, folosind:
    - analiza calculată intern pentru an eligibil + KPI + CAGR
    - payloadul brut Termene pentru contact și asociați
    """
    analysis = build_company_analysis(cui)

    client = TermeneClient()
    response_data = client.fetch_schema(
        cui=cui,
        schema_key=TERMENE_SCHEMA_KEY_COMPANY,
    )

    company_info = analysis.get("company_info", {})
    latest_year = analysis.get("latest_year")
    indicators_by_year = analysis.get("indicators_by_year", {})

    indicators = (
        indicators_by_year.get(str(latest_year))
        or indicators_by_year.get(latest_year)
        or {}
    )

    contact_info = extract_company_contact_info(response_data)
    shareholders = extract_shareholders(response_data)

    employees_value = _first_not_none(
        _safe_get_from_normalized(analysis, latest_year, "numar_angajati"),
        _safe_get_from_normalized(analysis, latest_year, "numar_mediu_angajati"),
    )

    return {
        "cui": company_info.get("cui"),
        "company_name": company_info.get("company_name"),
        "caen_code": company_info.get("caen_code"),
        "caen_label": company_info.get("caen_label"),
        "latest_year": latest_year,
        "turnover": _safe_get_from_normalized(analysis, latest_year, "cifra_afaceri"),
        "employees": employees_value,
        "profit_net": _safe_get_from_normalized(analysis, latest_year, "profit_net"),
        "profit_margin": indicators.get("profit_margin"),
        "cagr_ca": analysis.get("cagr_ca"),
        "phone": contact_info.get("phone"),
        "email": contact_info.get("email"),
        "shareholders": shareholders,
        "status": "success",
    }


def enrich_companies(cui_list: list[int]) -> list[dict]:
    """
    Rulează enrichment pentru o listă de CUI-uri.
    Nu oprește tot procesul dacă o companie dă eroare.
    """
    results = []

    for cui in cui_list:
        try:
            enriched = enrich_company_by_cui(int(cui))
            results.append(enriched)
        except Exception as e:
            results.append({
                "cui": cui,
                "company_name": None,
                "caen_code": None,
                "caen_label": None,
                "latest_year": None,
                "turnover": None,
                "employees": None,
                "profit_net": None,
                "profit_margin": None,
                "cagr_ca": None,
                "phone": None,
                "email": None,
                "shareholders": None,
                "status": f"error: {str(e)}",
            })

    return results


def _safe_get_from_normalized(analysis: dict, year: int, field_name: str):
    normalized_by_year = analysis.get("normalized_by_year", {})

    year_data = (
        normalized_by_year.get(str(year))
        or normalized_by_year.get(year)
        or {}
    )

    return year_data.get(field_name)


def _first_not_none(*values):
    for value in values:
        if value is not None:
            return value
    return None