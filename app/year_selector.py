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


# Bilanțul pentru anul Y se depune până la ~31 mai a anului Y+1 (termen legal,
# Legea contabilității 82/1991). Din luna iunie încolo, anul precedent (N-1)
# este în mod normal depus și disponibil în sursă. Înainte de iunie folosim
# N-2, pentru că N-1 încă nu e scadent.
#
# Dacă vrei un comportament mai conservator (să lași timp de propagare a
# datelor după termen), crește acest prag la 7 (iulie) sau 8 (august).
DEFAULT_DEADLINE_MONTH = 6


def get_max_comparable_year(
    today: date | None = None,
    deadline_month: int = DEFAULT_DEADLINE_MONTH,
) -> int:
    """
    Cel mai recent an care, din punct de vedere al termenului de depunere,
    ar trebui să fie deja disponibil.

    Exemplu (deadline_month = 6):
    - mai 2026      -> max_comparable_year = 2024 (2025 încă nescadent)
    - iunie 2026    -> max_comparable_year = 2025 (termenul a trecut)
    """
    today = today or date.today()

    if today.month >= deadline_month:
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
    deadline_month: int = DEFAULT_DEADLINE_MONTH,
) -> tuple[int | None, list[int], dict, int]:
    """
    Alege DINAMIC ultimul an care:
      1. este scadent (termenul de depunere a trecut), și
      2. are toate datele complete (is_year_complete).

    Dacă ultimul an scadent nu are încă date complete în sursă, selecția cade
    automat pe anul anterior care le are. Nu există ani hardcodați.

    Returnează:
    - latest_year
    - valid_years (toți anii eligibili, crescător)
    - rejected_years (debug: motivele respingerii)
    - max_comparable_year
    """
    max_comparable_year = get_max_comparable_year(
        today=today, deadline_month=deadline_month
    )

    valid_years = []
    rejected_years = {}

    for year, normalized_year in normalized_by_year.items():
        reasons = []

        if year > max_comparable_year:
            reasons.append(f"not_yet_due:{max_comparable_year}")

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