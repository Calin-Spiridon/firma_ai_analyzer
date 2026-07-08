from typing import Any


def _safe_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _pct(value: float | None) -> float | None:
    if value is None:
        return None
    return value * 100 if -1 <= value <= 1 else value


def _trend_pp(current: float | None, base: float | None, threshold_pp: float = 1.0) -> str:
    current = _pct(_safe_float(current))
    base = _pct(_safe_float(base))
    if current is None or base is None:
        return "necunoscut"
    diff = current - base
    if diff > threshold_pp:
        return "crestere"
    if diff < -threshold_pp:
        return "scadere"
    return "stabil"


# ── 1. CREȘTERE — dinamica CA în ultimul an (YoY) ─────────────
def classify_growth(yoy_growth: float | None) -> dict:
    v = _pct(_safe_float(yoy_growth))

    if v is None:
        return {
            "score": "⚪",
            "label": "Necunoscut",
            "profile": "Date insuficiente",
            "message": "Nu există suficiente date pentru evaluarea evoluției recente a activității."
        }

    if v > 10:
        return {
            "score": "🟢",
            "label": "Bun",
            "profile": "Activitate în creștere",
            "message": "Compania și-a crescut activitatea în ultimul an. Evoluția recentă indică o dezvoltare vizibilă a volumului de business."
        }

    if v >= 0:
        return {
            "score": "🟡",
            "label": "Acceptabil",
            "profile": "Creștere moderată",
            "message": "Compania a înregistrat o creștere moderată a activității în ultimul an. Evoluția este pozitivă, dar nu indică o accelerare puternică."
        }

    if v >= -10:
        return {
            "score": "🟠",
            "label": "Atenție",
            "profile": "Activitate în scădere",
            "message": "Compania a înregistrat o scădere a activității în ultimul an. Evoluția recentă merită analizată pentru a înțelege dacă este temporară sau indică o schimbare de tendință."
        }

    return {
        "score": "🔴",
        "label": "Prioritate ridicată",
        "profile": "Scădere accentuată a activității",
        "message": "Compania a înregistrat o scădere accentuată a activității în ultimul an. Evoluția recentă reprezintă o zonă importantă de analiză."
    }


# ── 2. PROFITABILITATE — marjă + trend + capital propriu ─────
def classify_profitability(current: float | None, base: float | None = None, equity: float | None = None) -> dict:
    m = _pct(_safe_float(current))
    trend = _trend_pp(current, base, threshold_pp=1.0)

    if m is None:
        return {
            "score": "⚪",
            "label": "Necunoscut",
            "profile": "Date insuficiente",
            "margin_trend": trend,
            "message": "Nu există suficiente date pentru evaluarea profitabilității."
        }

    if m < 0:
        score = "🔴"
        label = "Prioritate ridicată"
        profile = "Pierdere"
        message = "Activitatea nu generează profit în perioada analizată. Compania produce cifră de afaceri, dar nu reușește să o transforme în profit pozitiv."
    elif m < 4:
        score = "🟠"
        label = "Atenție"
        profile = "Profitabilitate fragilă"
        message = "Compania generează profit, însă nivelul acestuia este redus raportat la volumul activității."
    elif m < 7:
        score = "🟡"
        label = "Acceptabil"
        profile = "Profitabilitate acceptabilă"
        message = "Compania generează profit într-o zonă acceptabilă pentru multe modele de business."
    elif m < 12:
        score = "🟢"
        label = "Bun"
        profile = "Profitabilitate solidă"
        message = "Compania generează profit la un nivel solid, ceea ce indică o capacitate bună de transformare a activității în valoare economică."
    else:
        score = "🟢"
        label = "Bun"
        profile = "Profitabilitate foarte puternică"
        message = "Compania generează profit la un nivel foarte bun raportat la volumul activității."

    if trend == "scadere":
        message += " Tendința descendentă a marjei merită urmărită, deoarece poate indica o reducere a capacității de a transforma vânzările în profit."
    elif trend == "crestere":
        message += " Tendința pozitivă a marjei indică o îmbunătățire a capacității de a transforma vânzările în profit."

    eq = _safe_float(equity)
    if eq is not None and eq < 0:
        profile += " / capital propriu negativ"
        message += " Capitalul propriu negativ poate sugera existența unor pierderi acumulate care nu au fost încă recuperate integral."

    return {"score": score, "label": label, "profile": profile, "margin_trend": trend, "message": message}


# ── 3. CASH FLOW — capital blocat + zile creanțe + zile stoc ──
def classify_cashflow(ratio: float | None, zile_creante: float | None = None, zile_stoc: float | None = None) -> dict:
    v = _pct(_safe_float(ratio))
    cr = _safe_float(zile_creante)
    st = _safe_float(zile_stoc)

    if v is None:
        return {
            "score": "⚪",
            "label": "Necunoscut",
            "profile": "Date insuficiente",
            "message": "Nu există suficiente date pentru evaluarea cash-flow-ului operațional."
        }

    creante_high = cr is not None and cr > 90
    stoc_high = st is not None and st > 120
    creante_ok = cr is not None and cr < 60
    stoc_ok = st is not None and st < 60

    if v > 50 or (creante_high and stoc_high):
        profile = "Cash Flow critic"
        message = "O parte semnificativă din activitate rămâne blocată în ciclul operațional."
        if creante_high and stoc_high:
            message += " Capitalul este blocat atât în creanțe, cât și în stocuri."
        elif creante_high:
            message += " Principala zonă de atenție este durata ridicată de încasare a creanțelor."
        elif stoc_high:
            message += " Principala zonă de atenție este capitalul blocat în stocuri."
        return {"score": "🔴", "label": "Prioritate ridicată", "profile": profile, "message": message}

    if v > 30 or creante_high or stoc_high:
        profile = "Cash Flow sub presiune"
        message = "O parte importantă din resurse rămâne blocată în activitatea curentă."
        if creante_high and stoc_high:
            message += " Capitalul este blocat atât în creanțe, cât și în stocuri."
        elif creante_high:
            message += " Compania încasează lent, iar creanțele reprezintă principala zonă de atenție."
        elif stoc_high:
            message += " Stocurile absorb o parte importantă din capital."
        return {"score": "🟠", "label": "Atenție", "profile": profile, "message": message}

    if v < 15 and creante_ok and stoc_ok:
        return {
            "score": "🟢",
            "label": "Bun",
            "profile": "Cash Flow foarte bun",
            "message": "Compania operează cu un nivel redus al capitalului blocat. Creanțele și stocurile par bine controlate."
        }

    return {
        "score": "🟡",
        "label": "Acceptabil",
        "profile": "Cash Flow normal",
        "message": "Compania finanțează o parte din activitate prin capital de lucru, însă nivelul creanțelor și al stocurilor pare gestionabil pentru tipul de activitate desfășurat."
    }


# ── 4. EFICIENȚA CAPITALULUI — Sales on Assets ────────────────
def classify_assets(sales_on_assets: float | None) -> dict:
    v = _safe_float(sales_on_assets)

    if v is None:
        return {
            "score": "⚪",
            "label": "Necunoscut",
            "profile": "Date insuficiente",
            "message": "Nu există suficiente date pentru evaluarea eficienței capitalului."
        }

    if v < 1:
        return {
            "score": "🔴",
            "label": "Prioritate ridicată",
            "profile": "Model foarte intensiv în capital",
            "message": "Compania utilizează un volum foarte ridicat de capital pentru a genera nivelul actual al activității."
        }

    if v < 1.5:
        return {
            "score": "🟠",
            "label": "Atenție",
            "profile": "Model care consumă mult capital",
            "message": "Compania are nevoie de un volum ridicat de capital pentru a susține activitatea curentă."
        }

    if v <= 2.5:
        return {
            "score": "🟡",
            "label": "Acceptabil",
            "profile": "Utilizare normală a capitalului",
            "message": "Compania utilizează capitalul într-un mod normal raportat la nivelul actual al activității."
        }

    return {
        "score": "🟢",
        "label": "Bun",
        "profile": "Utilizare foarte bună a capitalului",
        "message": "Compania generează un volum ridicat de activitate raportat la capitalul utilizat."
    }


# ── 5. CAPITAL UMAN — productivitate × efort salarial ────────
def classify_human_capital(prod: float | None, rand: float | None, is_it_services: bool = False, profit_margin: float | None = None) -> dict:
    p = _safe_float(prod)
    r = _safe_float(rand)
    pm = _pct(_safe_float(profit_margin))

    if p is None or r is None:
        return {
            "score": "⚪",
            "label": "Necunoscut",
            "profile": "Date insuficiente",
            "message": "Nu există suficiente date pentru evaluarea capitalului uman."
        }

    productivitate_redusa = p < 500_000
    productivitate_medie = 500_000 <= p <= 1_000_000
    productivitate_ridicata = p > 1_000_000

    efort_ridicat = r < 5
    efort_normal = 5 <= r <= 8
    efort_redus = r > 8

    if is_it_services and pm is not None and pm >= 7:
        return {
            "score": "🟡",
            "label": "Acceptabil",
            "profile": "Model dependent de resursa umană, specific industriei",
            "message": "Modelul este dependent de oameni și de costuri salariale, însă acest lucru poate fi normal pentru industria IT, software sau servicii profesionale."
        }

    if productivitate_ridicata and efort_redus:
        return {
            "score": "🟢",
            "label": "Bun",
            "profile": "Productivitate ridicată și efort salarial redus",
            "message": "Datele disponibile sugerează că oamenii contribuie eficient la generarea activității, iar costurile salariale nu reprezintă o sursă majoră de presiune asupra modelului de business."
        }

    if productivitate_medie and not efort_ridicat:
        return {
            "score": "🟡",
            "label": "Acceptabil",
            "profile": "Productivitate medie și efort salarial gestionabil",
            "message": "Productivitatea se află într-o zonă medie, iar costurile salariale par compatibile cu nivelul activității generate."
        }

    if productivitate_redusa and efort_ridicat:
        return {
            "score": "🔴",
            "label": "Prioritate ridicată",
            "profile": "Productivitate redusă și efort salarial ridicat",
            "message": "Activitatea generată este redusă raportat la costurile salariale. Această combinație poate limita capacitatea companiei de a transforma veniturile în profit."
        }

    if productivitate_redusa or efort_ridicat:
        return {
            "score": "🟠",
            "label": "Atenție",
            "profile": "Productivitate redusă sau efort salarial ridicat",
            "message": "Datele sugerează că relația dintre activitatea generată și costurile salariale merită analizată mai atent."
        }

    return {
        "score": "🟡",
        "label": "Acceptabil",
        "profile": "Capital uman gestionabil",
        "message": "Productivitatea și efortul salarial par gestionabile raportat la nivelul actual al activității."
    }


# ── Detectare IT / servicii profesionale (CAEN 62/63) ────────
def is_it_or_professional_services(company_info: dict | None) -> bool:
    if not company_info:
        return False
    caen_code = str(company_info.get("caen_code") or company_info.get("caen") or "").strip()
    caen_label = str(
        company_info.get("caen_label")
        or company_info.get("caen_name")
        or company_info.get("caen_desc")
        or ""
    ).lower()

    return (
        caen_code.startswith("62")
        or caen_code.startswith("63")
        or "software" in caen_label
        or "soft" in caen_label
        or "servicii informatice" in caen_label
        or "consultanta" in caen_label
        or "programare" in caen_label
        or "outsourcing" in caen_label
    )


# ── PROFIL COMPLET ────────────────────────────────────────────
def build_tpc_scoring_profile(indicators: dict, company_info: dict | None = None) -> dict:
    """
    indicators trebuie să conțină (fracții pentru procente):
      dinamica_ca_ultim_an, profit_margin, profit_margin_base,
      capital_propriu, capital_blocat_ratio, zile_creante, zile_stoc,
      sales_on_assets, productivitate, randament
    company_info: dict cu caen_code/caen și caen_label/caen_desc
                  (pentru excepția IT / servicii profesionale)
    """
    is_it = is_it_or_professional_services(company_info)

    return {
        "growth": classify_growth(indicators.get("dinamica_ca_ultim_an")),
        "profitability": classify_profitability(
            current=indicators.get("profit_margin"),
            base=indicators.get("profit_margin_base"),
            equity=indicators.get("capital_propriu"),
        ),
        "cashflow": classify_cashflow(
            ratio=indicators.get("capital_blocat_ratio"),
            zile_creante=indicators.get("zile_creante"),
            zile_stoc=indicators.get("zile_stoc"),
        ),
        "assets": classify_assets(indicators.get("sales_on_assets")),
        "human_capital": classify_human_capital(
            prod=indicators.get("productivitate"),
            rand=indicators.get("randament"),
            is_it_services=is_it,
            profit_margin=indicators.get("profit_margin"),
        ),
    }