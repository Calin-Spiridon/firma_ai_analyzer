# credit_limit.py — Modul de calcul limita de credit comercial TPC
# Adauga in folderul app/ din proiectul tau Python

def calculate_credit_limit(indicators: dict, normalized_latest: dict) -> dict:
    """
    Calculeaza limita recomandata de credit comercial pe baza
    indicatorilor financiari ai companiei.

    Args:
        indicators: dict cu indicatorii calculati (profit_margin, debt_ratio, etc.)
        normalized_latest: dict cu datele normalizate ale anului curent (cifra_afaceri, etc.)

    Returns:
        dict cu limita curenta, limita potential, gap si explicatii
    """

    ca = normalized_latest.get("cifra_afaceri") or 0
    if ca <= 0:
        return {"error": "Cifra de afaceri indisponibila"}

    capacitate_lunara = ca / 12

    # ── FSF — Financial Strength Factor ─────────────────────
    fsf = 1.0
    fsf_detalii = []

    # 1. Capital blocat
    capital_blocat_ratio = indicators.get("capital_blocat_ratio") or 0
    if capital_blocat_ratio > 0.30:
        fsf -= 0.3
        fsf_detalii.append({"factor": "Capital blocat", "valoare": f"{capital_blocat_ratio*100:.1f}%", "impact": -0.3, "nivel": "ridicat"})
    elif capital_blocat_ratio > 0.20:
        fsf -= 0.2
        fsf_detalii.append({"factor": "Capital blocat", "valoare": f"{capital_blocat_ratio*100:.1f}%", "impact": -0.2, "nivel": "mediu"})
    else:
        fsf_detalii.append({"factor": "Capital blocat", "valoare": f"{capital_blocat_ratio*100:.1f}%", "impact": 0, "nivel": "scazut"})

    # 2. Zile stoc
    zile_stoc = indicators.get("zile_stoc") or 0
    if zile_stoc > 90:
        fsf -= 0.2
        fsf_detalii.append({"factor": "Zile stoc", "valoare": f"{int(zile_stoc)} zile", "impact": -0.2, "nivel": "ridicat"})
    elif zile_stoc > 60:
        fsf -= 0.1
        fsf_detalii.append({"factor": "Zile stoc", "valoare": f"{int(zile_stoc)} zile", "impact": -0.1, "nivel": "mediu"})
    else:
        fsf_detalii.append({"factor": "Zile stoc", "valoare": f"{int(zile_stoc)} zile", "impact": 0, "nivel": "ok"})

    # 3. Zile creante
    zile_creante = indicators.get("zile_creante") or 0
    if zile_creante > 60:
        fsf -= 0.2
        fsf_detalii.append({"factor": "Zile creante", "valoare": f"{int(zile_creante)} zile", "impact": -0.2, "nivel": "ridicat"})
    elif zile_creante > 30:
        fsf -= 0.1
        fsf_detalii.append({"factor": "Zile creante", "valoare": f"{int(zile_creante)} zile", "impact": -0.1, "nivel": "mediu"})
    else:
        fsf_detalii.append({"factor": "Zile creante", "valoare": f"{int(zile_creante)} zile", "impact": 0, "nivel": "ok"})

    # 4. Debt ratio
    debt_ratio = indicators.get("debt_ratio") or 0
    if debt_ratio > 0.70:
        fsf -= 0.3
        fsf_detalii.append({"factor": "Debt ratio", "valoare": f"{debt_ratio*100:.1f}%", "impact": -0.3, "nivel": "ridicat"})
    elif debt_ratio > 0.50:
        fsf -= 0.2
        fsf_detalii.append({"factor": "Debt ratio", "valoare": f"{debt_ratio*100:.1f}%", "impact": -0.2, "nivel": "mediu"})
    else:
        fsf_detalii.append({"factor": "Debt ratio", "valoare": f"{debt_ratio*100:.1f}%", "impact": 0, "nivel": "ok"})

    # 5. Profitabilitate (bonus)
    profit_margin = indicators.get("profit_margin") or 0
    if profit_margin > 0.10:
        fsf += 0.2
        fsf_detalii.append({"factor": "Profitabilitate", "valoare": f"{profit_margin*100:.1f}%", "impact": +0.2, "nivel": "excelent"})
    elif profit_margin > 0.05:
        fsf += 0.1
        fsf_detalii.append({"factor": "Profitabilitate", "valoare": f"{profit_margin*100:.1f}%", "impact": +0.1, "nivel": "bun"})
    else:
        fsf_detalii.append({"factor": "Profitabilitate", "valoare": f"{profit_margin*100:.1f}%", "impact": 0, "nivel": "slab"})

    # 6. ROE (bonus)
    roe = indicators.get("roe_dupont") or 0
    if roe > 0.20:
        fsf += 0.2
        fsf_detalii.append({"factor": "ROE DuPont", "valoare": f"{roe*100:.1f}%", "impact": +0.2, "nivel": "excelent"})
    elif roe > 0.10:
        fsf += 0.1
        fsf_detalii.append({"factor": "ROE DuPont", "valoare": f"{roe*100:.1f}%", "impact": +0.1, "nivel": "bun"})
    else:
        fsf_detalii.append({"factor": "ROE DuPont", "valoare": f"{roe*100:.1f}%", "impact": 0, "nivel": "slab"})

    # 7. CAGR (bonus) — vine din result["cagr_ca"]
    cagr = indicators.get("cagr_ca") or 0
    if cagr > 0.20:
        fsf += 0.2
        fsf_detalii.append({"factor": "CAGR CA", "valoare": f"{cagr*100:.1f}%", "impact": +0.2, "nivel": "excelent"})
    elif cagr > 0.10:
        fsf += 0.1
        fsf_detalii.append({"factor": "CAGR CA", "valoare": f"{cagr*100:.1f}%", "impact": +0.1, "nivel": "bun"})
    else:
        fsf_detalii.append({"factor": "CAGR CA", "valoare": f"{cagr*100:.1f}%" if cagr else "N/A", "impact": 0, "nivel": "slab"})

    # Clamp FSF intre 0.3 si 1.8
    fsf = round(max(0.3, min(1.8, fsf)), 2)

    # ── Risk Multiplier ───────────────────────────────────────
    if fsf < 0.7:
        risk_level    = "High Risk"
        risk_mult     = 0.7
        risk_color    = "red"
    elif fsf < 1.1:
        risk_level    = "Medium Risk"
        risk_mult     = 1.0
        risk_color    = "orange"
    else:
        risk_level    = "Low Risk"
        risk_mult     = 1.3
        risk_color    = "green"

    # ── Limita curenta ────────────────────────────────────────
    limita_baza    = capacitate_lunara * fsf
    limita_curenta = limita_baza * risk_mult

    # Interval ±10%
    limita_min = limita_curenta * 0.90
    limita_max = limita_curenta * 1.10

    # ── Limita potentiala (daca imbunatatesc capitalul) ───────
    fsf_potential = fsf
    if capital_blocat_ratio > 0.20:
        fsf_potential += 0.2   # eliminam penalizarea capital blocat
    if zile_stoc > 60:
        fsf_potential += 0.1
    if zile_creante > 30:
        fsf_potential += 0.1
    fsf_potential = round(min(1.8, fsf_potential), 2)

    limita_potential  = (capacitate_lunara * fsf_potential) * risk_mult
    gap               = limita_potential - limita_curenta

    # ── Wording TPC ───────────────────────────────────────────
    def fmt(v):
        if v >= 1_000_000:
            return f"{v/1_000_000:.2f} mil. lei".replace(".", ",")
        elif v >= 1_000:
            return f"{v/1_000:.1f} mii lei".replace(".", ",")
        else:
            return f"{int(v):,} lei".replace(",", ".")

    wording_premium = (
        f"Pe baza structurii financiare actuale, o limita sanatoasa de credit "
        f"comercial ar fi in zona de {fmt(limita_min)} – {fmt(limita_max)}."
    )
    wording_consultativ = (
        f"Structura actuala sugereaza o capacitate de absorbtie a creditului "
        f"comercial de aproximativ {fmt(limita_curenta)}, "
        + ("insa cu presiune in zona de capital de lucru." if fsf < 1.0
           else "cu o structura financiara echilibrata.")
    )
    wording_vanzare = (
        f"Business-ul sustine volum, dar exista un gap de {fmt(gap)} intre "
        f"limita actuala si potentialul real — potential de crestere a creditului "
        f"daca structura se optimizeaza."
        if gap > 0 else
        f"Structura financiara este solida si sustine un credit comercial de pana la {fmt(limita_max)}."
    )

    return {
        "capacitate_lunara":  round(capacitate_lunara, 2),
        "fsf":                fsf,
        "fsf_detalii":        fsf_detalii,
        "risk_level":         risk_level,
        "risk_multiplier":    risk_mult,
        "risk_color":         risk_color,
        "limita_curenta":     round(limita_curenta, 2),
        "limita_min":         round(limita_min, 2),
        "limita_max":         round(limita_max, 2),
        "limita_potential":   round(limita_potential, 2),
        "gap":                round(gap, 2),
        "fsf_potential":      fsf_potential,
        # Formatate
        "limita_curenta_fmt": fmt(limita_curenta),
        "limita_min_fmt":     fmt(limita_min),
        "limita_max_fmt":     fmt(limita_max),
        "limita_potential_fmt": fmt(limita_potential),
        "gap_fmt":            fmt(gap),
        # Wording
        "wording_premium":      wording_premium,
        "wording_consultativ":  wording_consultativ,
        "wording_vanzare":      wording_vanzare,
    }