from app.termene_client import TermeneClient
from app.config import TERMENE_SCHEMA_KEY_COMPANY
from app.api_mapper import extract_last_5_years_from_api, extract_company_info
from app.normalizer import normalize_api_year_data
from app.indicators import calculate_indicators_for_year
from app.utils import calculate_cagr


def build_company_analysis(cui: int) -> dict:
    client = TermeneClient()

    response_data = client.fetch_schema(
        cui=cui,
        schema_key=TERMENE_SCHEMA_KEY_COMPANY
    )

    company_info = extract_company_info(response_data)
    last_5_years = extract_last_5_years_from_api(response_data)

    normalized_by_year = {}
    indicators_by_year = {}

    for year, raw_year_data in last_5_years.items():
        normalized = normalize_api_year_data(raw_year_data)
        indicators = calculate_indicators_for_year(year, normalized)

        normalized_by_year[year] = normalized
        indicators_by_year[year] = indicators

    years_sorted = sorted(indicators_by_year.keys())
    latest_year = years_sorted[-1]

    start_year = years_sorted[0]
    end_year = years_sorted[-1]

    cagr_ca = calculate_cagr(
        normalized_by_year[start_year]["cifra_afaceri"],
        normalized_by_year[end_year]["cifra_afaceri"],
        end_year - start_year
    )

    return {
        "company_info": company_info,
        "years_sorted": years_sorted,
        "latest_year": latest_year,
        "normalized_by_year": {str(k): v for k, v in normalized_by_year.items()},
        "indicators_by_year": {str(k): v for k, v in indicators_by_year.items()},
        "cagr_ca": cagr_ca,
        "raw_response": response_data,
    }