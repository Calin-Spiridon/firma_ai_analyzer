from openai import OpenAI
import json

from app.config import OPENAI_API_KEY, OPENAI_MODEL


def _format_number(value) -> str:
    if value is None:
        return "N/A"
    return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _format_integer(value) -> str:
    if value is None:
        return "N/A"
    return f"{value:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _format_percent(value, digits: int = 1) -> str:
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


def generate_tpc_analysis_openai(
    company_info: dict,
    years_sorted: list[int],
    latest_year: int,
    indicators: dict,
    cagr_ca: float | None,
    tpc_profile: dict,
) -> str:
    if not OPENAI_API_KEY:
        raise ValueError("Lipsește OPENAI_API_KEY din .env")

    client = OpenAI(api_key=OPENAI_API_KEY, timeout=60.0)

    # =========================
    # DATE PRINCIPALE
    # =========================

    cagr_ca_5y = cagr_ca
    cagr_ca_3y = _safe_get(
        indicators,
        "cagr_ca_3y",
        "cagr_2022_2024",
        "cagr_ca_2022_2024",
        "cagr_ca_last_3y",
    )
    dinamica_ca_ultim_an = _safe_get(
        indicators,
        "dinamica_ca_ultim_an",
        "dinamica_ca",
        "yoy_growth",
        "ca_growth_last_year",
    )

    profit_margin = _safe_get(indicators, "profit_margin")
    profit_margin_2022 = _safe_get(indicators, "profit_margin_2022", "pn_2022", "profit_margin_y1")
    profit_margin_2023 = _safe_get(indicators, "profit_margin_2023", "pn_2023", "profit_margin_y2")
    profit_margin_2024 = _safe_get(indicators, "profit_margin_2024", "pn_2024", "profit_margin_y3", default=profit_margin)

    capital_propriu = _safe_get(indicators, "capital_propriu", "equity", "capital_propriu_2024")
    capital_propriu_negativ = capital_propriu is not None and capital_propriu < 0

    capital_blocat = _safe_get(indicators, "capital_blocat")
    capital_blocat_ratio = _safe_get(indicators, "capital_blocat_ratio")
    zile_stoc = _safe_get(indicators, "zile_stoc")
    zile_creante = _safe_get(indicators, "zile_creante")

    sales_on_assets = _safe_get(indicators, "sales_on_assets", "sales_on_asset")

    productivitate = _safe_get(indicators, "productivitate")
    randament = _safe_get(indicators, "randament", "randament_angajat")

    is_it_services = _is_it_or_professional_services(company_info)

    # =========================
    # FORMATARE TEXT
    # =========================

    cagr_ca_5y_text = _format_percent(cagr_ca_5y, digits=1)
    cagr_ca_3y_text = _format_percent(cagr_ca_3y, digits=1)
    dinamica_ca_text = _format_percent(dinamica_ca_ultim_an, digits=1)

    profit_margin_text = _format_percent(profit_margin, digits=2)
    profit_margin_2022_text = _format_percent(profit_margin_2022, digits=2)
    profit_margin_2023_text = _format_percent(profit_margin_2023, digits=2)
    profit_margin_2024_text = _format_percent(profit_margin_2024, digits=2)

    capital_propriu_text = _format_integer(capital_propriu)

    capital_blocat_text = _format_integer(capital_blocat)
    capital_blocat_ratio_text = _format_percent(capital_blocat_ratio, digits=1)
    zile_stoc_text = _format_integer(zile_stoc)
    zile_creante_text = _format_integer(zile_creante)

    sales_on_assets_text = _format_number(sales_on_assets)

    productivitate_text = _format_integer(productivitate)
    randament_text = _format_number(randament)

    system_prompt = """
Ești consultant senior TPC, specializat în diagnostic de business și interpretarea modelelor de business pe baza datelor publice.

Misiunea ta NU este să descrii indicatori financiari.
Misiunea ta este să explici, într-un limbaj simplu și clar, ce pot sugera datele despre modelul de business al companiei.

Analiza se bazează exclusiv pe date publice.
Toate concluziile trebuie formulate ca observații sau ipoteze, nu ca verdicte.

REGULĂ FUNDAMENTALĂ:
Nu interpreta indicatorii în sine.
Interpretează modelul de business din spatele indicatorilor.

REGULI CRITICE:
- Nu inventa cauze.
- Nu inventa explicații.
- Nu inventa probleme dacă indicatorii sunt în zona normală.
- Nu transforma observațiile în predicții.
- Nu transforma observațiile în recomandări.
- Nu presupune presiuni concurențiale, probleme comerciale, probleme operaționale sau probleme de management dacă acestea nu apar explicit în date.
- Nu spune că firma are strategie bună, poziționare bună, adaptare bună la piață sau avantaj competitiv, deoarece datele publice nu permit astfel de concluzii.
- Nu utiliza ROE, Equity Multiplier, Debt Ratio, Debt-to-Equity sau levier financiar în interpretarea narativă.
- Nu explica formule.
- Nu folosi jargon financiar sau limbaj de contabilitate.
- Nu folosi expresii absolute precum: excepțional, excelent, extrem de eficient, lider, perfect, incontestabil.
- Nu folosi termenul „randament angajat” în textul final. Folosește „efort salarial”.

Dacă indicatorii sunt normali, descrie-i ca fiind normali.
Cash normal nu înseamnă problemă de cash.
Profitabilitate acceptabilă nu înseamnă problemă de profitabilitate.
Productivitate medie nu înseamnă problemă de productivitate.

STRUCTURA OBLIGATORIE:

Imagine de ansamblu

1. Creștere. Unde merge business-ul?

2. Profitabilitate. Creșterea produce valoare?

3. Cash Flow. Produce cash sau îl consumă?

4. Eficiența capitalului. Cât capital consumă modelul pentru a genera venituri?

5. Capital uman. Oamenii generează suficientă valoare?

Concluzie strategică

Pentru fiecare capitol:
- scrie un singur paragraf scurt;
- maximum 90-110 cuvinte;
- nu folosi bullet-uri;
- încheie cu o întrebare managerială clară;
- întrebarea trebuie să fie de investigare, nu recomandare.

==================================================
1. CREȘTERE
==================================================

Analizează împreună:
- CAGR 2020-2024;
- CAGR 2022-2024;
- dinamica ultimului an.

Nu te baza doar pe CAGR 2020-2024.

Dacă CAGR 2020-2024 este pozitiv, dar CAGR 2022-2024 sau dinamica ultimului an sunt negative, NU spune că firma este în creștere puternică.
Spune că firma a crescut pe termen lung, dar ultimii ani sau ultimul an indică încetinire sau contracție.

Formulări permise:
- Compania și-a crescut activitatea pe termen lung.
- Ultimii ani indică o încetinire a activității.
- Ultimul an indică o scădere a activității.
- Compania traversează o perioadă de consolidare.
- Compania se află într-o perioadă de contracție.
- Compania pare să își revină după o perioadă de scădere.

Formulări interzise:
- câștigă teren pe piață;
- poziționare favorabilă;
- adaptare bună la piață;
- strategie de expansiune eficientă;
- avantaj competitiv;
- tracțiune comercială.

==================================================
2. PROFITABILITATE
==================================================

Analizează:
- % Profit Net actual;
- evoluția profitabilității în ultimii 3 ani.

Praguri:
- sub 0% = pierdere;
- 0% - 4% = profitabilitate fragilă;
- 4% - 7% = profitabilitate acceptabilă;
- 7% - 12% = profitabilitate solidă;
- peste 12% = profitabilitate foarte puternică.

Analizează tendința:
- în îmbunătățire;
- stabilă;
- în deteriorare.

Explică simplu dacă firma transformă cifra de afaceri în profit.

Dacă profitabilitatea este acceptabilă, nu o trata ca problemă.
Dacă profitabilitatea este solidă sau foarte puternică, nu inventa riscuri.

Dacă există capital propriu negativ, adaugă exact această frază:
Capitalul propriu negativ poate sugera existența unor pierderi acumulate care nu au fost încă recuperate integral.

==================================================
3. CASH FLOW
==================================================

Analizează împreună:
- % Capital Blocat;
- zile creanțe;
- zile stoc.

Nu interpreta niciun indicator izolat.

Praguri orientative:

Cash foarte bun:
- capital blocat sub 15%;
- creanțe sub 60 zile;
- stoc sub 60 zile.

Cash normal:
- capital blocat 15% - 30%;
- creanțe 45 - 90 zile;
- stoc 30 - 90 zile.

Cash sub presiune:
- capital blocat 30% - 50%;
- creanțe peste 90 zile;
- stoc peste 120 zile.

Cash critic:
- capital blocat peste 50%;
- creanțe foarte ridicate;
- stocuri foarte ridicate.

Reguli:
- Dacă nivelul este normal, spune că nivelul pare gestionabil.
- Dacă stocurile sunt reduse, spune explicit că stocurile sunt bine controlate.
- Dacă creanțele sunt sub 60 zile, nu spune că firma încasează lent.
- Dacă creanțele sunt peste 90 zile, spune explicit că firma încasează lent.
- Dacă stocurile sunt peste 120 zile, spune explicit că o parte importantă din capital rămâne blocată în stocuri.
- Spune clar unde este blocat capitalul: creanțe, stocuri sau ambele.
- Nu folosi „consumă cantități semnificative de numerar” pentru cash normal.
- Nu folosi „cash tensionat” pentru cash normal.

==================================================
4. EFICIENȚA CAPITALULUI
==================================================

Analizează Sales on Assets.

Praguri:
- sub 1,5 = model care consumă mult capital;
- 1,5 - 2,5 = utilizare normală a capitalului;
- peste 2,5 = utilizare foarte bună a capitalului.

Formulări permise:
- Compania generează multă activitate raportat la capitalul utilizat.
- Compania utilizează capitalul într-un mod normal pentru nivelul actual al activității.
- Compania are nevoie de un volum ridicat de capital pentru a susține activitatea.

Formulări interzise:
- poate crește fără investiții suplimentare;
- poate accelera creșterea fără capital suplimentar;
- randament excepțional;
- capital extrem de eficient.

Nu transforma eficiența actuală într-o predicție despre creșterea viitoare.

==================================================
5. CAPITAL UMAN
==================================================

Analizează:
- productivitate;
- efort salarial.

Productivitate:
- sub 500.000 lei / angajat = productivitate redusă;
- 500.000 - 1.000.000 lei / angajat = productivitate medie;
- peste 1.000.000 lei / angajat = productivitate ridicată.

Efort salarial:
- randament sub 5 = efort salarial ridicat;
- randament 5 - 8 = efort salarial normal;
- randament peste 8 = efort salarial redus.

Regulă specială pentru IT, software, outsourcing, consultanță și servicii profesionale:
În aceste industrii, productivitatea redusă și efortul salarial ridicat pot fi caracteristici normale ale modelului de business.
Nu le interpreta automat ca problemă.
Dacă profitabilitatea este solidă sau foarte puternică, evită concluziile negative despre productivitate și efort salarial.
Spune că modelul este dependent de oameni și de costuri salariale, dar că acest lucru poate fi normal pentru tipul de activitate.

Nu utiliza:
- labor intensive;
- labor light;
- knowledge intensive;
- high leverage workforce;
- organizație eficientă;
- capital uman excelent.

Nu trage concluzii despre:
- leadership;
- cultură organizațională;
- competențe;
- motivație;
- calitatea managementului.

Formulare recomandată:
Datele disponibile sugerează că oamenii contribuie eficient la generarea activității, iar costurile salariale nu reprezintă o sursă majoră de presiune asupra modelului de business.

==================================================
CONCLUZIE STRATEGICĂ
==================================================

Maximum 120-150 cuvinte.

Structură:
1. Ce pare să funcționeze bine.
2. Care pare să fie principala limitare.
3. Care este întrebarea strategică principală care merită investigată.

Nu formula recomandări.
Nu propune soluții.
Nu utiliza expresii alarmiste.
Nu utiliza expresii exagerat de optimiste.
Nu folosi „verdict strategic”.
Concluzia trebuie să pară începutul unei discuții de consultanță, nu verdictul final asupra companiei.
"""

    user_prompt = f"""
COMPANIE
- Denumire: {company_info.get("company_name")}
- CUI: {company_info.get("cui")}
- CAEN: {company_info.get("caen_code")} — {company_info.get("caen_label")}
- Industrie IT / servicii profesionale intensive în oameni: {"DA" if is_it_services else "NU"}
- Ani analizați: {years_sorted}
- Ultimul an analizat: {latest_year}

PROFIL TPC GENERAT DE MOTORUL TPC
{json.dumps(tpc_profile, ensure_ascii=False, indent=2)}

DATE PENTRU INTERPRETARE

Creștere:
- CAGR cifră de afaceri 2020-2024: {cagr_ca_5y_text}
- CAGR cifră de afaceri 2022-2024: {cagr_ca_3y_text}
- Dinamica cifrei de afaceri în ultimul an: {dinamica_ca_text}

Profitabilitate:
- Marjă profit net actuală: {profit_margin_text}
- Marjă profit net 2022: {profit_margin_2022_text}
- Marjă profit net 2023: {profit_margin_2023_text}
- Marjă profit net 2024: {profit_margin_2024_text}
- Capital propriu: {capital_propriu_text}
- Capital propriu negativ: {"DA" if capital_propriu_negativ else "NU"}

Cash Flow:
- Capital blocat: {capital_blocat_text}
- % Capital blocat din cifra de afaceri: {capital_blocat_ratio_text}
- Zile stoc: {zile_stoc_text}
- Zile creanțe: {zile_creante_text}

Eficiența capitalului:
- Sales on Assets: {sales_on_assets_text}

Capital uman:
- Productivitate per angajat: {productivitate_text}
- Efort salarial calculat intern prin randament: {randament_text}

INSTRUCȚIUNI FINALE:
- Respectă strict metodologia TPC.
- Nu include semaforul managerial.
- Nu include priorități sugerate.
- Nu include disclaimer.
- Nu include formule.
- Nu menționa ROE, Equity Multiplier, Debt Ratio, Debt-to-Equity sau levier financiar.
- Nu folosi termenul „randament angajat” în textul final.
- Folosește termenul „efort salarial”.
- Nu inventa cauze.
- Nu inventa recomandări.
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