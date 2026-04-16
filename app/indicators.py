def safe_div(numerator, denominator):
    if denominator in (0, None):
        return 0
    return numerator / denominator


def get_salary_monthly_for_year(year: int) -> float:
    if year == 2025:
        return 8938
    return 8532




def calculate_indicators_for_year(year: int, data: dict) -> dict:
    cifra_afaceri = data["cifra_afaceri"]
    profit_net = data["profit_net"]
    total_active = data["total_active"]
    capital_propriu = data["capital_propriu"]
    stocuri = data["stocuri"]
    creante = data["creante"]
    datorii_totale = data["datorii_totale"]
    numar_angajati = data["numar_angajati"]

    profit_margin = safe_div(profit_net, cifra_afaceri)

    sales_on_assets = safe_div(cifra_afaceri, total_active)
    equity_multiplier = safe_div(total_active, capital_propriu)

    zile_stoc = safe_div(stocuri, cifra_afaceri) * 365
    zile_creante = safe_div(creante, cifra_afaceri) * 365

    capital_blocat = creante + stocuri
    capital_blocat_ratio = safe_div(capital_blocat, cifra_afaceri)

    salariu_mediu_lunar = get_salary_monthly_for_year(year)
    salariu_anual = salariu_mediu_lunar * 12
    fond_salarial = salariu_anual * numar_angajati
    pondere_fond_salarial = safe_div(fond_salarial, cifra_afaceri)

    productivitate = safe_div(cifra_afaceri, numar_angajati)
    randament = safe_div(productivitate, salariu_anual)

    debt_ratio = safe_div(datorii_totale, total_active)
    debt_to_equity = safe_div(datorii_totale, capital_propriu)
    datorii_vs_cash_block = safe_div(datorii_totale, capital_blocat)
    datorii_ratio_ca = safe_div(datorii_totale, cifra_afaceri)

    roe_dupont = profit_margin * sales_on_assets * equity_multiplier

    return {
        "year": year,
        "profit_margin": profit_margin,
        "sales_on_assets": sales_on_assets,
        "equity_multiplier": equity_multiplier,
        "zile_stoc": zile_stoc,
        "zile_creante": zile_creante,
        "capital_blocat": capital_blocat,
        "capital_blocat_ratio": capital_blocat_ratio,
        "salariu_mediu_lunar": salariu_mediu_lunar,
        "salariu_anual": salariu_anual,
        "fond_salarial": fond_salarial,
        "pondere_fond_salarial": pondere_fond_salarial,
        "productivitate": productivitate,
        "randament": randament,
        "debt_ratio": debt_ratio,
        "debt_to_equity": debt_to_equity,
        "datorii_vs_cash_block": datorii_vs_cash_block,
        "datorii_ratio_ca": datorii_ratio_ca,
        "roe_dupont": roe_dupont,
    }