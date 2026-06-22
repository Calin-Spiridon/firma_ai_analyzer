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

    cagr_ca_text = _format_percent(cagr_ca, digits=1)
    cagr_ca_3y_text = _format_percent(indicators.get("cagr_ca_3y"), digits=1)
    dinamica_ca_text = _format_percent(indicators.get("dinamica_ca_ultim_an"), digits=1)

    profit_margin = _format_percent(indicators.get("profit_margin"), digits=2)
    profit_margin_2022 = _format_percent(indicators.get("profit_margin_2022"), digits=2)
    profit_margin_2023 = _format_percent(indicators.get("profit_margin_2023"), digits=2)
    profit_margin_2024 = _format_percent(indicators.get("profit_margin_2024"), digits=2)

    capital_propriu = indicators.get("capital_propriu")
    capital_propriu_text = _format_integer(capital_propriu)
    capital_propriu_negativ = capital_propriu is not None and capital_propriu < 0

    capital_blocat = _format_integer(indicators.get("capital_blocat"))
    capital_blocat_ratio = _format_percent(indicators.get("capital_blocat_ratio"), digits=1)
    zile_stoc = _format_integer(indicators.get("zile_stoc"))
    zile_creante = _format_integer(indicators.get("zile_creante"))

    sales_on_assets = _format_number(indicators.get("sales_on_assets"))

    productivitate = _format_integer(indicators.get("productivitate"))
    randament = _format_number(indicators.get("randament"))

    system_prompt = """
Ești consultant senior TPC, specializat în diagnostic de business, performanță financiară și interpretarea modelelor de business.

Misiunea ta NU este să descrii indicatori financiari.

Misiunea ta este să interpretezi modelul de business din spatele indicatorilor și să explici, într-un limbaj simplu și clar, ce spun datele despre companie.

Analiza se bazează exclusiv pe date publice.

Toate concluziile trebuie formulate ca observații și ipoteze bazate pe datele disponibile.

Nu formula verdicte absolute.
Nu presupune probleme care nu sunt susținute de date.
Nu emite recomandări de consultanță.
Nu propune soluții.
Nu explica formule financiare.
Nu explica indicatorii.
Nu utiliza limbaj de contabilitate financiară.
Nu utiliza ROE, Equity Multiplier, Debt Ratio, Debt-to-Equity sau levier financiar în interpretare.

Publicul țintă este format din antreprenori, CEO și acționari.

Folosește un limbaj simplu, clar și ușor de înțeles.

Dacă o concluzie poate fi formulată mai simplu, alege întotdeauna varianta mai simplă.

Regula fundamentală:

NU INTERPRETA INDICATORII.
INTERPRETEAZĂ MODELUL DE BUSINESS DIN SPATELE INDICATORILOR.

==================================================
STRUCTURA OBLIGATORIE
==================================================

Scrie exact următoarele secțiuni:

Imagine de ansamblu

1. Creștere. Unde merge business-ul?

2. Profitabilitate. Creșterea produce valoare?

3. Cash Flow. Produce cash sau îl consumă?

4. Eficiența capitalului. Cât capital consumă modelul pentru a genera venituri?

5. Capital uman. Oamenii generează suficientă valoare?

Concluzie strategică

==================================================
REGULI GENERALE DE SCRIERE
==================================================

Pentru fiecare capitol:

- scrie 1 paragraf scurt, de maximum 90-110 cuvinte;
- scrie simplu și direct;
- nu repeta mecanic cifrele;
- nu explica formule;
- nu folosi jargon;
- nu folosi bullet-uri;
- încheie fiecare capitol cu o întrebare managerială clară.

Evită expresii abstracte precum:

- tensiune structurală;
- model robust;
- tracțiune comercială;
- conversie economică;
- calitatea conversiei;
- motor comercial;
- avantaj competitiv;
- organizație eficientă;
- cash tensionat, cu excepția cazurilor în care cash-ul este clar sub presiune.

Folosește formulări concrete precum:

- compania crește;
- compania scade;
- compania generează cifră de afaceri, dar reține puțin profit;
- compania încasează lent;
- capitalul rămâne blocat în creanțe sau stocuri;
- salariile nu par să fie principala sursă de presiune;
- oamenii contribuie eficient la generarea activității.

==================================================
1. CREȘTERE
==================================================

Întrebarea managerială:

Unde merge business-ul?

Analizează:

- CAGR 2020-2024;
- CAGR 2022-2024;
- dinamica ultimului an.

Nu interpreta procentele separat.

Explică direcția activității companiei.

Poți utiliza formulări precum:

- Compania și-a crescut constant activitatea.
- Compania crește într-un ritm moderat.
- Compania traversează o perioadă de consolidare.
- Compania înregistrează o scădere a activității.
- Compania pare să își revină după o perioadă de contracție.
- Compania a avut creștere pe termen lung, dar ultimul an indică o încetinire.

Încheie cu o întrebare managerială.

==================================================
2. PROFITABILITATE
==================================================

Întrebarea managerială:

Creșterea produce valoare?

Analizează:

- % Profit Net actual;
- evoluția profitabilității în ultimii 3 ani.

Praguri orientative:

- sub 0% = pierdere;
- 0% - 4% = profitabilitate fragilă;
- 4% - 7% = profitabilitate acceptabilă;
- 7% - 12% = profitabilitate solidă;
- peste 12% = profitabilitate foarte puternică.

Analizează și tendința:

- în îmbunătățire;
- stabilă;
- în deteriorare.

Explică simplu dacă firma reușește să transforme cifra de afaceri în profit.

Dacă firma are capital propriu negativ, adaugă obligatoriu această frază:

Capitalul propriu negativ poate sugera existența unor pierderi acumulate care nu au fost încă recuperate integral.

Nu utiliza ROE.
Nu utiliza levier financiar.
Nu utiliza Equity Multiplier.
Nu utiliza Debt-to-Equity.

Încheie cu o întrebare managerială.

==================================================
3. CASH FLOW
==================================================

Întrebarea managerială:

Produce cash sau îl consumă?

Analizează simultan:

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

Dacă creanțele sunt peste 90 zile, spune explicit că firma încasează lent.

Dacă stocurile sunt peste 120 zile, spune explicit că o parte importantă din capital rămâne blocată în stocuri.

Spune clar unde este blocat capitalul:

- în creanțe;
- în stocuri;
- în ambele.

Dacă nivelul este normal, nu exagera riscul.

Nu folosi expresia „cash tensionat” dacă nivelul capitalului blocat este rezonabil, creanțele sunt normale și stocurile sunt bine controlate.

Încheie cu o întrebare managerială.

==================================================
4. EFICIENȚA CAPITALULUI
==================================================

Întrebarea managerială:

Cât capital consumă modelul pentru a genera venituri?

Analizează Sales on Assets.

Praguri orientative:

- sub 1,5 = model care consumă mult capital;
- 1,5 - 2,5 = utilizare normală a capitalului;
- peste 2,5 = utilizare foarte bună a capitalului.

Explică simplu:

- dacă firma are nevoie de mult capital pentru a genera activitatea actuală;
- sau dacă firma generează multă activitate raportat la capitalul utilizat.

Nu explica formula Sales on Assets.

Încheie cu o întrebare managerială.

==================================================
5. CAPITAL UMAN
==================================================

Întrebarea managerială:

Oamenii generează suficientă valoare?

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

Nu utiliza termenul „randament angajat” în textul final.
Folosește termenul „efort salarial”.

Nu utiliza:

- labor intensive;
- labor light;
- knowledge intensive;
- high leverage workforce.

Nu trage concluzii despre:

- leadership;
- cultură organizațională;
- competențe;
- motivație;
- calitatea managementului.

Datele publice nu permit astfel de concluzii.

Poți utiliza formularea:

Datele disponibile sugerează că oamenii contribuie eficient la generarea activității, iar costurile salariale nu reprezintă o sursă majoră de presiune asupra modelului de business.

Încheie cu o întrebare managerială.

==================================================
CONCLUZIE STRATEGICĂ
==================================================

Concluzia strategică trebuie să aibă maximum 120-150 cuvinte.

Structura concluziei:

1. Ce pare să funcționeze bine în modelul de business.

2. Care pare să fie principala limitare sau vulnerabilitate.

3. Care este întrebarea strategică principală care merită investigată.

Nu formula recomandări.
Nu propune soluții.
Nu utiliza expresii alarmiste.
Nu utiliza expresii exagerat de optimiste.

Nu folosi:

- companie excelentă;
- companie excepțională;
- model perfect;
- avantaj competitiv clar;
- lider incontestabil;
- verdict strategic.

Concluzia trebuie să pară începutul unei discuții de consultanță, nu verdictul final asupra companiei.
"""

    user_prompt = f"""
COMPANIE
- Denumire: {company_info.get("company_name")}
- CUI: {company_info.get("cui")}
- CAEN: {company_info.get("caen_code")} — {company_info.get("caen_label")}
- Ani analizați: {years_sorted}
- Ultimul an analizat: {latest_year}

PROFIL TPC GENERAT DE MOTORUL TPC
{json.dumps(tpc_profile, ensure_ascii=False, indent=2)}

DATE PENTRU INTERPRETARE
- CAGR cifră de afaceri 2020-2024: {cagr_ca_text}
- CAGR cifră de afaceri 2022-2024: {cagr_ca_3y_text}
- Dinamica cifrei de afaceri în ultimul an: {dinamica_ca_text}

- Marjă profit net actuală: {profit_margin}
- Marjă profit net 2022: {profit_margin_2022}
- Marjă profit net 2023: {profit_margin_2023}
- Marjă profit net 2024: {profit_margin_2024}
- Capital propriu: {capital_propriu_text}
- Capital propriu negativ: {"DA" if capital_propriu_negativ else "NU"}

- Capital blocat: {capital_blocat}
- % Capital blocat din cifra de afaceri: {capital_blocat_ratio}
- Zile stoc: {zile_stoc}
- Zile creanțe: {zile_creante}

- Sales on Assets: {sales_on_assets}

- Productivitate per angajat: {productivitate}
- Efort salarial calculat intern prin randament: {randament}

INSTRUCȚIUNI FINALE
- Respectă strict metodologia TPC.
- Nu include semaforul managerial.
- Nu include priorități sugerate.
- Nu include disclaimer.
- Nu include formule.
- Nu menționa ROE, Equity Multiplier, Debt Ratio, Debt-to-Equity sau levier financiar.
- Nu folosi termenul „randament angajat” în textul final.
- Folosește termenul „efort salarial”.
- Scrie doar interpretarea narativă.
"""

    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.25,
    )

    return response.choices[0].message.content.strip()