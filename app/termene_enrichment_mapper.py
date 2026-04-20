def extract_company_contact_info(response_data: dict) -> dict:
    contact = response_data.get("date_contact", {}) or {}

    telefoane = contact.get("telefon", []) or []
    emailuri = contact.get("email", []) or []

    return {
        "phone": ", ".join(str(x) for x in telefoane if x) if telefoane else None,
        "email": ", ".join(str(x) for x in emailuri if x) if emailuri else None,
    }


def extract_shareholders(response_data: dict) -> str | None:
    asociati = response_data.get("asociati", {}) or {}
    persoane_fizice = asociati.get("persoane_fizice", []) or []
    persoane_juridice = asociati.get("persoane_juridice", []) or []

    names = []

    for item in persoane_fizice:
        nume = item.get("nume")
        functie = item.get("functie")
        if nume and functie:
            names.append(f"{nume} ({functie})")
        elif nume:
            names.append(nume)

    for item in persoane_juridice:
        nume = item.get("nume")
        functie = item.get("functie")
        if nume and functie:
            names.append(f"{nume} ({functie})")
        elif nume:
            names.append(nume)

    return " | ".join(names) if names else None


def get_latest_reported_year(response_data: dict) -> int | None:
    bilanturi = response_data.get("bilanturi_mfinante_scurte", {}) or {}
    valid_years = []

    for key, value in bilanturi.items():
        if not key.startswith("an_"):
            continue
        if not isinstance(value, dict) or not value:
            continue

        try:
            year = int(key.replace("an_", ""))
            valid_years.append(year)
        except ValueError:
            continue

    if not valid_years:
        return None

    return max(valid_years)


def extract_latest_profit_margin_from_termene(response_data: dict, year: int | None = None) -> float | None:
    marje = response_data.get("marja_profitului_net", {}) or {}

    valid_years = []
    for key, value in marje.items():
        if key.startswith("an_") and value is not None:
            try:
                valid_years.append(int(key.replace("an_", "")))
            except ValueError:
                continue

    if not valid_years:
        return None

    if year is not None and year in valid_years:
        chosen_year = year
    else:
        chosen_year = max(valid_years)

    value = marje.get(f"an_{chosen_year}")
    if value is None:
        return None

    return float(value) / 100.0


def extract_latest_turnover_and_employees(response_data: dict, year: int | None = None) -> dict:
    bilanturi = response_data.get("bilanturi_mfinante_scurte", {}) or {}

    if year is None:
        year = get_latest_reported_year(response_data)

    if year is None:
        return {
            "year": None,
            "turnover": None,
            "employees": None,
            "profit_net": None,
        }

    year_data = bilanturi.get(f"an_{year}", {}) or {}

    return {
        "year": year,
        "turnover": ((year_data.get("cifra_de_afaceri_neta") or {}).get("valoare")),
        "employees": ((year_data.get("numar_mediu_angajati") or {}).get("valoare")),
        "profit_net": ((year_data.get("profit_net") or {}).get("valoare")),
    }