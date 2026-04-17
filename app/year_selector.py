from datetime import date


REQUIRED_NON_NULL_FIELDS = [
    "active_circulante",
    "active_imobilizate",
    "total_active",
    "capital_propriu",
    "cifra_afaceri",
    "stocuri",
    "creante",
    "datorii_totale",
    "numar_angajati",
    "profit_net",
]

REQUIRED_NON_ZERO_FIELDS = [
    "total_active",
    "capital_propriu",
    "cifra_afaceri",
    "numar_angajati",
]


def get_max_comparable_year(today: date | None = None, safety_month: int = 8) -> int:
    """
    Regula recomandată:
    - până la final de iulie / început de august, comparăm pe anul N-2
    - din august încolo, putem compara pe anul N-1

    Exemplu:
    - aprilie 2026 -> max_comparable_year = 2024
    - septembrie 2026 -> max_comparable_year = 2025
    """
    today = today or date.today()

    if today.month >= safety_month:
        return today.year - 1

    return today.year - 2


def is_year_complete(normalized_year: dict) -> tuple[bool, list[str]]:
    reasons = []

    for field in REQUIRED_NON_NULL_FIELDS:
        if normalized_year.get(field) is None:
            reasons.append(f"missing:{field}")

    for field in REQUIRED_NON_ZERO_FIELDS:
        value = normalized_year.get(field)
        if value in (None, 0):
            reasons.append(f"zero_or_missing:{field}")

    return len(reasons) == 0, reasons


def select_analysis_year(
    normalized_by_year: dict,
    today: date | None = None,
    safety_month: int = 8,
) -> tuple[int | None, list[int], dict, int]:
    """
    Returnează:
    - latest_year
    - years_sorted (toți anii validați)
    - rejected_years (debug)
    - max_comparable_year
    """
    max_comparable_year = get_max_comparable_year(today=today, safety_month=safety_month)

    valid_years = []
    rejected_years = {}

    for year, normalized_year in normalized_by_year.items():
        reasons = []

        if year > max_comparable_year:
            reasons.append(f"above_max_comparable_year:{max_comparable_year}")

        is_complete, complete_reasons = is_year_complete(normalized_year)
        reasons.extend(complete_reasons)

        if reasons:
            rejected_years[year] = reasons
        else:
            valid_years.append(year)

    valid_years = sorted(valid_years)

    if not valid_years:
        return None, [], rejected_years, max_comparable_year

    latest_year = valid_years[-1]
    return latest_year, valid_years, rejected_years, max_comparable_year