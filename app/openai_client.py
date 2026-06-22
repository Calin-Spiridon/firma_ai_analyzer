from openai import OpenAI
import json
import logging

from app.config import OPENAI_API_KEY, OPENAI_MODEL

logger = logging.getLogger(__name__)


# =========================================================
# HELPERE DE FORMATARE
# =========================================================

def _format_number(value) -> str:
    if value is None:
        return "N/A"
    return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _format_integer(value) -> str:
    if value is None:
        return "N/A"
    return f"{value:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _format_percent(value, digits: int = 1) -> str:
    """Valoarea este stocată ca raport zecimal (0,177 -> 17,7%)."""
    if value is None:
        return "N/A"
    return f"{value * 100:.{digits}f}%".replace(".", ",")


def _safe_get(indicators: dict, *keys, default=None):
    for key in keys:
        if key in indicators and indicators.get(key) is not None:
            return indicators.get(key)
    return default


def _is_it_or_professional_services(company_info: dict) -> bool:
    caen_code = str(company_info.get("caen_code") or "")
    caen_label = str(company_info.get("caen_label") or "").lower()

    it_caen_prefixes = ("62", "63")
    service_keywords = [
        "software",
        "soft",
        "it",
        "tehnologia informatiei",
        "realizare a softului",
        "consultanta",
        "servicii informatice",
        "programare",
        "outsourcing",
    ]

    return caen_code.startswith(it_caen_prefixes) or any(
        keyword in caen_label for keyword in service_keywords
    )


# =========================================================
# FUNCȚIA PRINCIPALĂ
# =========================================================

def generate_tpc_analysis_openai(
    company_info: dict,
    years_sorted: list[int],
    latest_year: int,
    indicators: dict,
    cagr_ca: float | None,
    tpc_profile: dict | None = None,
) -> str:
    if not OPENAI_API_KEY:
        raise ValueError("Lipsește OPENAI_API_KEY din .env")

    client = OpenAI(api_key=OPENAI_API_KEY, timeout=60.0)

    # =====================================================================
    # ⚠️  MAPAREA CHEILOR  ⚠️
    # ---------------------------------------------------------------------
    # AICI ESTE LOCUL UNDE SE REZOLVĂ PROBLEMA "NU RECUNOAȘTE ULTIMUL AN".
    # Numele de mai jos sunt CANDIDATE. Trebuie să existe MĂCAR UNUL care
    # se potrivește cu cheia reală din dicționarul `indicators`.
    # La prima rulare verifică în log linia "[TPC] Câmpuri critice negăsite".
    # Dacă apare ceva acolo, adaugă numele corect al cheii în lista respectivă.
    # =====================================================================

    # ---- CREȘTERE -------------------------------------------------------
    cagr_ca_5y = cagr_ca  # vine direct ca parametru (CAGR 2020-2024)

    cagr_ca_3y = _safe_get(
        indicators,
        "cagr_ca_3y",
        "cagr_2022_2024",
        "cagr_ca_2022_2024",
        "cagr_ca_last_3y",
        "cagr_3y",
        "cagr_ca_3ani",
        "cagr_recent",
        "cagr_ca_recent",
    )

    dinamica_ca_ultim_an = _safe_get(
        indicators,
        "dinamica_ca_ultim_an",
        "dinamica_ca",
        f"dinamica_ca_{latest_year}",
        f"dinamica_ca_{latest_year}_vs_{latest_year - 1}",
        "dinamica_ca_yoy",
        "dinamica_ca_an",
        "yoy_growth",
        "ca_growth_last_year",
        "dinamica",
    )

    # ---- CIFRA DE AFACERI (pentru "Imagine de ansamblu") ----------------
    ca_latest = _safe_get(
        indicators,
        f"ca_{latest_year}",
        f"cifra_afaceri_{latest_year}",
        "ca",
        "cifra_afaceri",
        "ca_latest",
        "cifra_afaceri_ultim_an",
        "ca_ultim_an",
        "turnover",
        "revenue",
    )

    # Cifra de afaceri per an (derivată din years_sorted, fără ani hardcodați)
    ca_by_year: dict[int, float] = {}
    for y in years_sorted:
        ca_y = _safe_get(
            indicators,
            f"ca_{y}",
            f"cifra_afaceri_{y}",
            f"turnover_{y}",
        )
        if ca_y is not None:
            ca_by_year[y] = ca_y

    # ---- PROFITABILITATE ------------------------------------------------
    profit_margin = _safe_get(
        indicators,
        "profit_margin",
        f"profit_margin_{latest_year}",
        "marja_profit_net",
        "marja_neta",
    )

    # Marjă netă per an (derivată din years_sorted)
    profit_margin_by_year: dict[int, float] = {}
    for y in years_sorted:
        m = _safe_get(
            indicators,
            f"profit_margin_{y}",
            f"pn_{y}",
            f"marja_profit_{y}",
            f"profit_margin_pct_{y}",
            f"procent_profit_net_{y}",
        )
        if m is not None:
            profit_margin_by_year[y] = m

    # fallback: dacă nu avem marja anului curent dar avem `profit_margin`
    if latest_year not in profit_margin_by_year and profit_margin is not None:
        profit_margin_by_year[latest_year] = profit_margin

    capital_propriu = _safe_get(
        indicators,
        "capital_propriu",
        f"capital_propriu_{latest_year}",
        "equity",
        "capitaluri_proprii",
        "capital_propriu_total",
        "cpr",
        "capital_propriu_latest",
    )

    # Semnale auxiliare pentru detectarea capitalului propriu negativ.
    # Sunt folosite DOAR intern (nu apar în textul narativ).
    equity_multiplier = _safe_get(
        indicators,
        "equity_multiplier",
        f"equity_multiplier_{latest_year}",
        "multiplicator_capital",
        "equity_mult",
    )
    debt_to_equity = _safe_get(
        indicators,
        "debt_to_equity",
        f"debt_to_equity_{latest_year}",
        "datorii_la_capital",
        "dte",
    )

    capital_propriu_negativ = (
        (capital_propriu is not None and capital_propriu < 0)
        or (equity_multiplier is not None and equity_multiplier < 0)
        or (debt_to_equity is not None and debt_to_equity < 0)
    )

    # ---- CASH FLOW ------------------------------------------------------
    capital_blocat = _safe_get(
        indicators,
        "capital_blocat",
        f"capital_blocat_{latest_year}",
    )
    capital_blocat_ratio = _safe_get(
        indicators,
        "capital_blocat_ratio",
        "procent_capital_blocat",
        "capital_blocat_pct",
    )
    zile_stoc = _safe_get(indicators, "zile_stoc", "zile_stocuri", "days_inventory")
    zile_creante = _safe_get(indicators, "zile_creante", "days_receivables", "dso")

    # ---- EFICIENȚA CAPITALULUI ------------------------------------------
    sales_on_assets = _safe_get(
        indicators,
        "sales_on_assets",
        "sales_on_asset",
        "ca_pe_active",
        "asset_turnover",
    )

    # ---- CAPITAL UMAN ---------------------------------------------------
    productivitate = _safe_get(
        indicators,
        "productivitate",
        f"productivitate_{latest_year}",
        "productivity",
    )
    randament = _safe_get(
        indicators,
        "randament",
        "randament_angajat",
        "efort_salarial",
    )
    numar_salariati = _safe_get(
        indicators,
        "numar_salariati",
        f"numar_salariati_{latest_year}",
        "nr_angajati",
        "numar_angajati",
        "nr_salariati",
        "employees",
    )

    is_it_services = _is_it_or_professional_services(company_info)

    # =====================================================================
    # DIAGNOSTIC: ce câmpuri critice au rămas None
    # =====================================================================
    critical = {
        "cagr_ca_5y": cagr_ca_5y,
        "cagr_ca_3y": cagr_ca_3y,
        "dinamica_ca_ultim_an": dinamica_ca_ultim_an,
        "ca_latest": ca_latest,
        "profit_margin": profit_margin,
        "capital_propriu / semnale equity": (
            capital_propriu if capital_propriu is not None
            else equity_multiplier if equity_multiplier is not None
            else debt_to_equity
        ),
        "capital_blocat_ratio": capital_blocat_ratio,
        "zile_creante": zile_creante,
        "sales_on_assets": sales_on_assets,
        "productivitate": productivitate,
        "randament": randament,
    }
    missing = [name for name, val in critical.items() if val is None]
    if missing:
        logger.warning(
            "[TPC] Câmpuri critice negăsite pentru CUI %s: %s "
            "(verifică numele cheilor din dicționarul `indicators`)",
            company_info.get("cui"),
            ", ".join(missing),
        )

    # =====================================================================
    # FORMATARE TEXT PENTRU PROMPT
    # =====================================================================

    cagr_ca_5y_text = _format_percent(cagr_ca_5y, digits=1)
    cagr_ca_3y_text = _format_percent(cagr_ca_3y, digits=1)
    dinamica_ca_text = _format_percent(dinamica_ca_ultim_an, digits=1)

    ca_latest_text = _format_integer(ca_latest)
    ca_by_year_text = "\n".join(
        f"- Cifră de afaceri {y}: {_format_integer(ca_by_year[y])} lei"
        for y in sorted(ca_by_year)
    ) or "- N/A"

    profit_margin_text = _format_percent(profit_margin, digits=2)
    profit_margin_by_year_text = "\n".join(
        f"- Marjă profit net {y}: {_format_percent(profit_margin_by_year[y], digits=2)}"
        for y in sorted(profit_margin_by_year)
    ) or "- N/A"

    capital_propriu_text = _format_integer(capital_propriu)

    capital_blocat_text = _format_integer(capital_blocat)
    capital_blocat_ratio_text = _format_percent(capital_blocat_ratio, digits=1)
    zile_stoc_text = _format_integer(zile_stoc)
    zile_creante_text = _format_integer(zile_creante)

    sales_on_assets_text = _format_number(sales_on_assets)

    productivitate_text = _format_integer(productivitate)
    randament_text = _format_number(randament)
    numar_salariati_text = _format_integer(numar_salariati)

    # =====================================================================
    # SYSTEM PROMPT
    # =====================================================================

    system_prompt = """
Ești consultant senior TPC, specializat în diagnostic de business și în interpretarea modelelor de business pe baza datelor publice.

Misiunea ta NU este să descrii indicatori financiari. Misiunea ta este să explici, într-un limbaj simplu și clar, ce sugerează datele despre modelul de business al companiei.

Analiza se bazează exclusiv pe date publice. Toate concluziile se formulează ca observații sau ipoteze, niciodată ca verdicte.

REGULĂ FUNDAMENTALĂ
Nu interpreta indicatorii în sine. Interpretează modelul de business din spatele indicatorilor.

REGULI CRITICE
- Nu inventa cauze, explicații sau probleme.
- Nu inventa probleme dacă indicatorii sunt în zona normală; descrie-i ca normali.
- Nu transforma observațiile în predicții sau recomandări.
- Nu presupune presiuni concurențiale, comerciale, operaționale sau de management dacă nu apar explicit în date.
- Nu afirma că firma are strategie bună, poziționare bună, adaptare la piață sau avantaj competitiv (datele publice nu permit asta).
- Nu folosi ROE, Equity Multiplier, Debt Ratio, Debt-to-Equity sau levier financiar în text.
- Nu explica formule. Nu folosi jargon financiar sau de contabilitate.
- Nu folosi termeni absoluți: excepțional, excelent, extrem de eficient, lider, perfect, incontestabil.
- Folosește „efort salarial”, niciodată „randament angajat”.

REGULĂ IMPORTANTĂ DESPRE DATE LIPSĂ
Dacă o valoare îți este transmisă ca „N/A”, NU scrie „datele nu sunt disponibile” și NU construi observații pe lipsa ei. Folosește valorile pe care le ai și ignoră tăcut ce lipsește. Nu menționa niciodată că o informație lipsește.

============================================================
FORMAT DE IEȘIRE — OBLIGATORIU
============================================================
Răspunde EXACT în structura de mai jos, în limba română.
NU reproduce aceste instrucțiuni în răspuns.
NU folosi linii de separare formate din semne „=” sau „-”.
NU scrie titluri integral cu majuscule.
NU folosi bullet-uri și nu folosi liste.
Folosește EXACT aceste titluri de secțiune, scrise normal:

Imagine de ansamblu
1. Creștere. Unde merge business-ul?
2. Profitabilitate. Creșterea produce valoare?
3. Cash Flow. Produce cash sau îl consumă?
4. Eficiența capitalului. Cât capital consumă modelul pentru a genera venituri?
5. Capital uman. Oamenii generează suficientă valoare?
Concluzie strategică

Reguli de format pe secțiuni:
- „Imagine de ansamblu”: 2 paragrafe scurte (în total 90-120 de cuvinte) care sintetizează ce tip de business pare să fie, cum a evoluat activitatea (poate menționa nivelul cifrei de afaceri din ultimul an) și tensiunea principală dintre ce funcționează și principala limitare. Se încheie cu o singură frază care începe cu „Principala întrebare care merită investigată este …”. Această secțiune NU conține eticheta „Întrebare managerială:”.
- Secțiunile 1-5: un singur paragraf de 90-110 cuvinte, fără bullet-uri, urmat pe rând nou de „Întrebare managerială: …”. Întrebarea este de investigare, nu recomandare.
- „Concluzie strategică”: un singur paragraf de 120-150 de cuvinte. Întrebarea strategică se include în paragraf; nu adăuga o etichetă „Întrebare managerială:” separată aici.

============================================================
METODOLOGIE PE SECȚIUNI
============================================================

IMAGINE DE ANSAMBLU
Sintetizează în 2 paragrafe scurte: (1) ce tip de business pare să fie și cum a evoluat activitatea, putând menționa cifra de afaceri din ultimul an; (2) tensiunea principală dintre ceea ce pare să funcționeze și principala limitare. Încheie cu fraza „Principala întrebare care merită investigată este …”.

CAPITOLUL 1 — Creștere
Analizează ÎMPREUNĂ CAGR pe termen lung, CAGR pe ultimii ani și dinamica ultimului an. Nu te baza doar pe CAGR pe termen lung.
- Dacă toate sunt pozitive: descrie o expansiune puternică a volumului de business și spune că ultimul an confirmă continuarea tendinței.
- Dacă pe termen lung e pozitiv, dar ultimii ani sau ultimul an sunt negativi: spune că firma a crescut pe termen lung, dar ultimii ani / ultimul an indică încetinire sau contracție.
Formulări permise: compania și-a crescut activitatea pe termen lung; ultimii ani indică o încetinire a activității; ultimul an indică o scădere a activității; compania traversează o perioadă de consolidare; compania se află într-o perioadă de contracție; compania pare să își revină după o perioadă de scădere.
Formulări interzise: câștigă teren pe piață; poziționare favorabilă; adaptare bună la piață; strategie de expansiune eficientă; avantaj competitiv; tracțiune comercială.

CAPITOLUL 2 — Profitabilitate
Analizează marja de profit net actuală și evoluția ei pe anii disponibili.
Praguri:
- sub 0% = pierdere;
- 0% - 4% = profitabilitate fragilă;
- 4% - 7% = profitabilitate acceptabilă;
- 7% - 12% = profitabilitate solidă;
- peste 12% = profitabilitate foarte puternică.
REGULĂ STRICTĂ: o marjă netă negativă (sub 0%) înseamnă PIERDERE. Nu o numi niciodată „profitabilitate fragilă”. Spune explicit că firma a înregistrat pierderi.
Dacă marja a fost negativă în mai mulți ani consecutivi, spune explicit că firma a înregistrat pierderi în fiecare dintre acești ani.
Analizează tendința: în îmbunătățire / stabilă / în deteriorare.
Dacă profitabilitatea este acceptabilă, nu o trata ca problemă. Dacă este solidă sau foarte puternică, nu inventa riscuri.
Dacă există capital propriu negativ, include EXACT această frază:
Capitalul propriu negativ poate sugera existența unor pierderi acumulate care nu au fost încă recuperate integral.

CAPITOLUL 3 — Cash Flow
Analizează ÎMPREUNĂ procentul de capital blocat, zilele de creanțe și zilele de stoc. Nu interpreta niciun indicator izolat.
Praguri orientative:
- Cash foarte bun: capital blocat sub 15%; creanțe sub 60 zile; stoc sub 60 zile.
- Cash normal: capital blocat 15% - 30%; creanțe 45 - 90 zile; stoc 30 - 90 zile.
- Cash sub presiune: capital blocat 30% - 50%; creanțe peste 90 zile; stoc peste 120 zile.
- Cash critic: capital blocat peste 50%; creanțe foarte ridicate; stocuri foarte ridicate.
Reguli:
- Dacă nivelul este normal, spune că nivelul pare gestionabil.
- Dacă valoarea pentru zile stoc este 0 sau foarte mică, spune că stocurile sunt nesemnificative / foarte reduse, NU că lipsesc datele.
- Dacă creanțele sunt sub 60 zile, nu spune că firma încasează lent.
- Dacă creanțele sunt peste 90 zile, spune explicit că firma încasează lent.
- Dacă stocurile sunt peste 120 zile, spune explicit că o parte importantă din capital rămâne blocată în stocuri.
- Spune clar unde este blocat capitalul: creanțe, stocuri sau ambele.
- Nu folosi „consumă cantități semnificative de numerar” sau „cash tensionat” pentru cash normal.

CAPITOLUL 4 — Eficiența capitalului
Analizează Sales on Assets.
Praguri:
- sub 1,5 = model care consumă mult capital;
- 1,5 - 2,5 = utilizare normală a capitalului;
- peste 2,5 = utilizare foarte bună a capitalului.
Formulări permise: compania generează multă activitate raportat la capitalul utilizat; compania utilizează capitalul într-un mod normal pentru nivelul actual al activității; compania are nevoie de un volum ridicat de capital pentru a susține activitatea.
Formulări INTERZISE (foarte important — nu le folosi sub nicio formă): „poate crește fără investiții suplimentare”; „poate susține creșterea fără investiții suplimentare”; „fără necesitatea unor investiții semnificative suplimentare”; „poate accelera creșterea fără capital suplimentar”; „randament excepțional”; „capital extrem de eficient”.
Nu transforma eficiența actuală într-o predicție despre creșterea viitoare.

CAPITOLUL 5 — Capital uman
Analizează productivitatea și efortul salarial.
Productivitate:
- sub 500.000 lei / angajat = productivitate redusă;
- 500.000 - 1.000.000 lei / angajat = productivitate medie;
- peste 1.000.000 lei / angajat = productivitate ridicată.
Efort salarial (pe baza valorii interne de randament):
- sub 5 = efort salarial ridicat;
- 5 - 8 = efort salarial normal;
- peste 8 = efort salarial redus.
Regulă specială pentru IT, software, outsourcing, consultanță și servicii profesionale: productivitatea redusă și efortul salarial ridicat pot fi normale pentru acest tip de model; nu le interpreta automat ca problemă, mai ales dacă profitabilitatea este solidă sau foarte puternică.
Formulări INTERZISE: „permițând companiei să scaleze”; orice formulare care transformă situația actuală într-o predicție; labor intensive; labor light; knowledge intensive; high leverage workforce; organizație eficientă; capital uman excelent.
Nu trage concluzii despre leadership, cultură organizațională, competențe, motivație sau calitatea managementului.
Formulare recomandată când productivitatea este bună și costurile salariale sunt reduse:
Datele disponibile sugerează că oamenii contribuie eficient la generarea activității, iar costurile salariale nu reprezintă o sursă majoră de presiune asupra modelului de business.

CONCLUZIE STRATEGICĂ
Maximum 120-150 de cuvinte. Structură în trei idei, într-un singur paragraf: (1) ce pare să funcționeze bine; (2) care pare să fie principala limitare; (3) care este întrebarea strategică principală care merită investigată (inclusă în paragraf).
Nu formula recomandări. Nu propune soluții. Nu folosi expresii alarmiste sau exagerat de optimiste. Nu folosi „verdict strategic”. Concluzia trebuie să pară începutul unei discuții de consultanță, nu verdictul final asupra companiei.
"""

    # =====================================================================
    # USER PROMPT
    # =====================================================================

    tpc_profile_text = (
        json.dumps(tpc_profile, ensure_ascii=False, indent=2)
        if tpc_profile
        else "Indisponibil — interpretarea se bazează pe datele de mai jos."
    )

    user_prompt = f"""
COMPANIE
- Denumire: {company_info.get("company_name")}
- CUI: {company_info.get("cui")}
- CAEN: {company_info.get("caen_code")} — {company_info.get("caen_label")}
- Industrie IT / servicii profesionale intensive în oameni: {"DA" if is_it_services else "NU"}
- Ani analizați: {years_sorted}
- Ultimul an analizat: {latest_year}

PROFIL TPC GENERAT DE MOTORUL TPC
{tpc_profile_text}

DATE PENTRU INTERPRETARE

Cifra de afaceri:
- Cifra de afaceri în ultimul an ({latest_year}): {ca_latest_text} lei
{ca_by_year_text}

Creștere:
- CAGR cifră de afaceri pe termen lung (de la {years_sorted[0] if years_sorted else "?"}): {cagr_ca_5y_text}
- CAGR cifră de afaceri pe ultimii ani: {cagr_ca_3y_text}
- Dinamica cifrei de afaceri în ultimul an ({latest_year} vs {latest_year - 1}): {dinamica_ca_text}

Profitabilitate:
- Marjă profit net actuală ({latest_year}): {profit_margin_text}
- Evoluția marjei nete pe anii disponibili:
{profit_margin_by_year_text}
- Capital propriu: {capital_propriu_text}
- Capital propriu negativ: {"DA" if capital_propriu_negativ else "NU"}

Cash Flow:
- Capital blocat: {capital_blocat_text} lei
- % Capital blocat din cifra de afaceri: {capital_blocat_ratio_text}
- Zile stoc: {zile_stoc_text}
- Zile creanțe: {zile_creante_text}

Eficiența capitalului:
- Sales on Assets: {sales_on_assets_text}

Capital uman:
- Număr salariați ({latest_year}): {numar_salariati_text}
- Productivitate per angajat: {productivitate_text} lei
- Efort salarial (valoare internă de randament): {randament_text}

INSTRUCȚIUNI FINALE
- Respectă strict metodologia și FORMATUL DE IEȘIRE descrise în mesajul de sistem.
- Începe răspunsul cu titlul „Imagine de ansamblu”.
- Nu folosi linii de separare din semne „=” sau „-” și nu scrie titluri cu majuscule.
- Nu include semaforul managerial, prioritățile sugerate, disclaimerul sau formulele.
- Nu menționa ROE, Equity Multiplier, Debt Ratio, Debt-to-Equity sau levier financiar.
- Folosește „efort salarial”, nu „randament angajat”.
- Tratează o valoare „N/A” ca inexistentă: nu construi observații pe lipsa ei și nu menționa că lipsește.
- Scrie doar interpretarea narativă.
"""

    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.15,
    )

    return response.choices[0].message.content.strip()