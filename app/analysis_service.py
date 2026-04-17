from app.termene_client import TermeneClient
from app.config import TERMENE_SCHEMA_KEY_COMPANY
from app.api_mapper import extract_last_5_years_from_api, extract_company_info
from app.normalizer import normalize_api_year_data
from app.indicators import calculate_indicators_for_year
from app.utils import calculate_cagr
from app.year_selector import select_analysis_year


def build_company_analysis(cui: int) -> dict:
    client = TermeneClient()

    response_data = client.fetch_schema(
        cui=cui,
        schema_key=TERMENE_SCHEMA_KEY_COMPANY,
    )

    company_info = extract_company_info(response_data)

    # IMPORTANT:
    # Dacă funcția asta chiar limitează deja la 5 ani brut, ar fi mai bine ulterior
    # să o redenumim sau să o schimbăm. Deocamdată presupun că aduce ultimii ani disponibili.
    raw_years = extract_last_5_years_from_api(response_data)

    normalized_by_year = {}
    for year, raw_year_data in raw_years.items():
        normalized_by_year[year] = normalize_api_year_data(raw_year_data)

    latest_year, valid_years, rejected_years, max_comparable_year = select_analysis_year(
        normalized_by_year=normalized_by_year,
        safety_month=8,
    )

    if latest_year is None:
        raise ValueError("Nu există niciun an complet și eligibil pentru analiză.")

    # Fereastra oficială de 5 ani până la anul selectat
    target_years = list(range(latest_year - 4, latest_year + 1))

    # Păstrăm doar anii existenți în date
    years_sorted = [year for year in target_years if year in normalized_by_year]

    indicators_by_year = {}
    for year in years_sorted:
        indicators_by_year[year] = calculate_indicators_for_year(
            year,
            normalized_by_year[year],
        )

    cagr_ca = None
    if len(years_sorted) >= 2:
        start_year = years_sorted[0]
        end_year = years_sorted[-1]

        cagr_ca = calculate_cagr(
            normalized_by_year[start_year]["cifra_afaceri"],
            normalized_by_year[end_year]["cifra_afaceri"],
            end_year - start_year,
        )

    return {
        "company_info": company_info,
        "years_sorted": years_sorted,
        "latest_year": latest_year,
        "normalized_by_year": {str(k): v for k, v in normalized_by_year.items()},
        "indicators_by_year": {str(k): v for k, v in indicators_by_year.items()},
        "cagr_ca": cagr_ca,
        "max_comparable_year": max_comparable_year,
        "rejected_years": rejected_years,
        "raw_response": response_data,
    }