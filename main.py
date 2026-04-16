from app.termene_client import TermeneClient
from app.config import TERMENE_SCHEMA_KEY_COMPANY
from app.api_mapper import extract_last_5_years_from_api, extract_company_info
from app.normalizer import normalize_api_year_data
from app.indicators import calculate_indicators_for_year
from app.utils import calculate_cagr


def format_number(value):
    return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def format_percent(value):
    return f"{value * 100:.1f}%".replace(".", ",")


def print_indicators(indicators: dict):
    print(f"\nINDICATORI {indicators['year']}:")
    print(f"profit_margin: {format_percent(indicators['profit_margin'])}")
    print(f"sales_on_assets: {format_number(indicators['sales_on_assets'])}")
    print(f"equity_multiplier: {format_number(indicators['equity_multiplier'])}")
    print(f"zile_stoc: {format_number(indicators['zile_stoc'])}")
    print(f"zile_creante: {format_number(indicators['zile_creante'])}")
    print(f"capital_blocat: {format_number(indicators['capital_blocat'])}")
    print(f"capital_blocat_ratio: {format_percent(indicators['capital_blocat_ratio'])}")
    print(f"salariu_mediu_lunar: {format_number(indicators['salariu_mediu_lunar'])}")
    print(f"salariu_anual: {format_number(indicators['salariu_anual'])}")
    print(f"fond_salarial: {format_number(indicators['fond_salarial'])}")
    print(f"pondere_fond_salarial: {format_percent(indicators['pondere_fond_salarial'])}")
    print(f"productivitate: {format_number(indicators['productivitate'])}")
    print(f"randament: {format_number(indicators['randament'])}")
    print(f"debt_ratio: {format_percent(indicators['debt_ratio'])}")
    print(f"debt_to_equity: {format_number(indicators['debt_to_equity'])}")
    print(f"datorii_vs_cash_block: {format_number(indicators['datorii_vs_cash_block'])}")
    print(f"datorii_ratio_ca: {format_percent(indicators['datorii_ratio_ca'])}")
    print(f"roe_dupont: {format_percent(indicators['roe_dupont'])}")


client = TermeneClient()

cui_test = 5052558

response_data = client.fetch_schema(
    cui=cui_test,
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

print("COMPANIE:")
print(f"Denumire: {company_info['company_name']}")
print(f"CUI: {company_info['cui']}")
print(f"CAEN: {company_info['caen_code']} - {company_info['caen_label']}")

print("\nANI FOLOSIȚI:")
print(years_sorted)

print(f"\nULTIMUL AN ANALIZAT: {latest_year}")
print_indicators(indicators_by_year[latest_year])

print(f"\nCAGR CA ({start_year}-{end_year}):")
print(format_percent(cagr_ca))