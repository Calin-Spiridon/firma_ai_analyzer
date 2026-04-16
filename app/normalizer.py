def safe_number(value):
    if value in (None, "", "-", "None"):
        return 0
    return float(value)


def normalize_profit_net(raw_year_data: dict) -> float:
    profit = safe_number(raw_year_data.get("profit_net", {}).get("valoare"))
    pierdere = safe_number(raw_year_data.get("pierdere_neta", {}).get("valoare"))

    if profit > 0:
        return profit
    if pierdere > 0:
        return -pierdere
    return 0


def normalize_api_year_data(raw_year_data: dict) -> dict:
    active_circulante = safe_number(raw_year_data.get("active_circulante", {}).get("valoare"))
    active_imobilizate = safe_number(raw_year_data.get("active_imobilizate", {}).get("valoare"))
    total_active = active_circulante + active_imobilizate

    capital_propriu = safe_number(raw_year_data.get("capital_total", {}).get("valoare"))
    cifra_afaceri = safe_number(raw_year_data.get("cifra_de_afaceri_neta", {}).get("valoare"))
    stocuri = safe_number(raw_year_data.get("stocuri", {}).get("valoare"))
    creante = safe_number(raw_year_data.get("creante", {}).get("valoare"))
    datorii_totale = safe_number(raw_year_data.get("datorii", {}).get("valoare"))
    numar_angajati = safe_number(raw_year_data.get("numar_mediu_angajati", {}).get("valoare"))

    profit_net = normalize_profit_net(raw_year_data)

    return {
        "active_circulante": active_circulante,
        "active_imobilizate": active_imobilizate,
        "total_active": total_active,
        "capital_propriu": capital_propriu,
        "cifra_afaceri": cifra_afaceri,
        "stocuri": stocuri,
        "creante": creante,
        "datorii_totale": datorii_totale,
        "numar_angajati": numar_angajati,
        "profit_net": profit_net,
    }