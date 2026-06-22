from app.termene_client import TermeneClient
from app.config import TERMENE_SCHEMA_KEY_COMPANY
from app.api_mapper import extract_last_5_years_from_api, extract_company_info
from app.normalizer import normalize_api_year_data
from app.indicators import calculate_indicators_for_year
from app.utils import calculate_cagr
from app.year_selector import select_analysis_year


def _by_year(mapping: dict, year) -> dict:
    """Acceptă chei int sau str pentru an (defensiv)."""
    if not mapping:
        return {}
    return mapping.get(year) or mapping.get(str(year)) or {}


def build_ai_indicators(
    years_sorted: list[int],
    latest_year: int,
    indicators_by_year: dict,
    normalized_by_year: dict,
) -> dict:
    """
    Asamblează dicționarul PLAT de indicatori folosit de
    generate_tpc_analysis_openai() pentru „Concluzie TPC”.

    Pornește de la indicatorii ultimului an analizat și adaugă tot ce are
    nevoie interpretarea narativă, dar NU rezultă din calculul pe un singur an:
      - cifra de afaceri brută (pentru „Imagine de ansamblu”),
      - cifra de afaceri și marja netă pe fiecare an disponibil,
      - dinamica CA an/an,
      - CAGR pe ultimii 3 ani,
      - capital propriu și număr angajați.

    Totul este derivat DINAMIC din `latest_year`. Nu există ani hardcodați:
    dacă ultimul an cu date devine 2025 (sau 2026), cheile se ajustează singure
    (ca_2025, profit_margin_2025 etc.).
    """
    latest_ind = dict(_by_year(indicators_by_year, latest_year))
    latest_norm = _by_year(normalized_by_year, latest_year)

    # Toți indicatorii ultimului an (rate, zile, capital blocat, productivitate...)
    flat = dict(latest_ind)

    # Valori brute ale ultimului an
    ca_now = latest_norm.get("cifra_afaceri")
    flat["cifra_afaceri"] = ca_now
    flat[f"ca_{latest_year}"] = ca_now
    flat["capital_propriu"] = latest_ind.get(
        "capital_propriu", latest_norm.get("capital_propriu")
    )
    flat["numar_angajati"] = latest_ind.get(
        "numar_angajati", latest_norm.get("numar_angajati")
    )

    # Serii pe ani: cifră de afaceri și marjă netă pentru fiecare an disponibil
    for y in years_sorted:
        ca_y = _by_year(normalized_by_year, y).get("cifra_afaceri")
        if ca_y is not None:
            flat[f"ca_{y}"] = ca_y
        pm_y = _by_year(indicators_by_year, y).get("profit_margin")
        if pm_y is not None:
            flat[f"profit_margin_{y}"] = pm_y

    # Dinamica CA an/an — DOAR dacă există exact anul anterior (latest - 1),
    # ca să nu etichetăm greșit un salt peste un an lipsă.
    ca_prev = _by_year(normalized_by_year, latest_year - 1).get("cifra_afaceri")
    if ca_now is not None and ca_prev not in (None, 0):
        flat["dinamica_ca_ultim_an"] = (ca_now - ca_prev) / ca_prev

    # CAGR pe ultimii 3 ani — fereastra [latest-2 .. latest], dacă ambele capete există
    ca_3y_start = _by_year(normalized_by_year, latest_year - 2).get("cifra_afaceri")
    if ca_now and ca_3y_start:
        cagr_3y = calculate_cagr(ca_3y_start, ca_now, 2)
        if cagr_3y is not None:
            flat["cagr_ca_3y"] = cagr_3y

    return flat


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
        deadline_month=6,
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

    # Dicționarul PLAT pentru AI (Concluzie TPC), derivat dinamic din ultimul an.
    ai_indicators = build_ai_indicators(
        years_sorted=years_sorted,
        latest_year=latest_year,
        indicators_by_year=indicators_by_year,
        normalized_by_year=normalized_by_year,
    )

    return {
        "company_info": company_info,
        "years_sorted": years_sorted,
        "latest_year": latest_year,
        "normalized_by_year": {str(k): v for k, v in normalized_by_year.items()},
        "indicators_by_year": {str(k): v for k, v in indicators_by_year.items()},
        "ai_indicators": ai_indicators,
        "cagr_ca": cagr_ca,
        "max_comparable_year": max_comparable_year,
        "rejected_years": rejected_years,
        "raw_response": response_data,
    }