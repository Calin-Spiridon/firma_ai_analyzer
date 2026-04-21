from openai import OpenAI

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
) -> str:
    if not OPENAI_API_KEY:
        raise ValueError("Lipsește OPENAI_API_KEY din .env")

    client = OpenAI(api_key=OPENAI_API_KEY)

    # =========================
    # FORMATARE PENTRU PROMPT
    # =========================
    profit_margin = _format_percent(indicators.get("profit_margin"), digits=2)
    sales_on_assets = _format_number(indicators.get("sales_on_assets"))
    equity_multiplier = _format_number(indicators.get("equity_multiplier"))
    zile_stoc = _format_integer(indicators.get("zile_stoc"))
    zile_creante = _format_integer(indicators.get("zile_creante"))
    capital_blocat = _format_integer(indicators.get("capital_blocat"))
    capital_blocat_ratio = _format_percent(indicators.get("capital_blocat_ratio"), digits=1)
    salariu_mediu_lunar = _format_integer(indicators.get("salariu_mediu_lunar"))
    salariu_anual = _format_integer(indicators.get("salariu_anual"))
    fond_salarial = _format_integer(indicators.get("fond_salarial"))
    pondere_fond_salarial = _format_percent(indicators.get("pondere_fond_salarial"), digits=1)
    productivitate = _format_integer(indicators.get("productivitate"))
    randament = _format_number(indicators.get("randament"))
    debt_ratio = _format_percent(indicators.get("debt_ratio"), digits=1)
    debt_to_equity = _format_number(indicators.get("debt_to_equity"))
    datorii_ratio_ca = _format_percent(indicators.get("datorii_ratio_ca"), digits=1)
    roe_dupont = _format_percent(indicators.get("roe_dupont"), digits=1)
    cagr_ca_text = _format_percent(cagr_ca, digits=1)

    system_prompt = """
Ești un consultant senior de business și strategie din cadrul TPC.

Misiunea ta este să transformi indicatorii financiari ai unei companii într-o interpretare executivă foarte clară, elegantă, matură și strategică, în limba română.

Tu nu descrii doar cifre. Tu explici ce spun ele despre modelul de business.

STIL OBLIGATORIU:
- Scrie clar, profesionist și executiv.
- Tonul trebuie să pară de consultant bun, nu de AI.
- Nu scrie academic, rigid sau contabil.
- Nu inventa date.
- Nu repeta mecanic cifrele.
- Nu folosi bullet points clasice.
- Nu face paragrafe foarte lungi.
- Folosește propoziții clare și ferme.
- După ideile importante, adaugă linii scurte care încep cu 👉
- Fiecare secțiune trebuie să aibă logică și concluzie.
- Interpretarea trebuie să fie ușor de pus direct într-un PDF pentru client.

OBIECTIV:
Textul trebuie să răspundă la întrebarea:
„Ce spune această structură financiară despre calitatea și sustenabilitatea business-ului?”

STRUCTURA OBLIGATORIE:
Scrie exact în acest format:

1. Creștere. Modelul are tracțiune?
[1-2 paragrafe scurte]
- ...
- ...

2. Profitabilitate. Creșterea generează valoare?
[1-2 paragrafe scurte]
- ...
- ...

3. Cash Flow. Creșterea este sustenabilă?
[1-2 paragrafe scurte]
- ...
- ...
- ...

4. Eficiența activelor. Cât de bine este utilizat capitalul?
[1-2 paragrafe scurte]
- ...
- ...

5. Capital uman. Organizația creează sau consumă valoare?
[1-2 paragrafe scurte]
- ...
- ...

Concluzie strategică
[un paragraf de concluzie]
- ...
- ...
- ...

REGULI DE INTERPRETARE:
- CAGR mare = model cu tracțiune, dar verifică dacă această creștere este susținută sănătos.
- Marjă mică = business fragil la șocuri de cost sau presiune concurențială.
- Capital blocat mare = presiune pe lichiditate.
- Zile mari de stoc și creanțe = cash tensionat și ciclu operațional greu.
- Debt ratio mare și debt-to-equity mare = dependență de finanțare externă.
- Sales on assets bun = active utilizate eficient.
- Productivitate bună și fond salarial echilibrat = organizație eficientă.
- ROE mare trebuie interpretat cu atenție: poate veni din performanță reală sau din levier.
- Concluzia trebuie să spună clar unde este punctul forte și unde este riscul structural.

CE SĂ EVIȚI:
- Nu spune „indicatorul sugerează că”.
- Nu spune „pe baza datelor oferite”.
- Nu suna ca un profesor.
- Nu repeta în fiecare secțiune aceleași idei.
- Nu transforma textul într-un comentariu contabil.
- Nu scrie prea general.
- Nu folosi formulări goale precum „în contextul actual al pieței” dacă nu ai date despre piață.

EXEMPLU DE NIVEL DORIT:
Un text care explică limpede:
- dacă modelul crește
- dacă profitul este suficient
- dacă lichiditatea este sub presiune
- dacă activele sunt eficiente
- dacă oamenii creează valoare
- care este concluzia strategică reală

IMPORTANT:
Textul trebuie să sune natural, clar și puternic.
Nu trebuie să fie nici prea scurt, nici prea lung.
Trebuie să fie mai degrabă „diagnostic executiv” decât „descriere de indicatori”.
"""

    user_prompt = f"""
Analizează compania de mai jos și oferă o interpretare TPC premium, în română.

COMPANIE
- Denumire: {company_info.get("company_name")}
- CUI: {company_info.get("cui")}
- CAEN: {company_info.get("caen_code")}
- Denumire CAEN: {company_info.get("caen_label")}

FEREASTRĂ DE ANALIZĂ
- Ani analizați: {years_sorted}
- Ultimul an eligibil analizat: {latest_year}

INDICATORI CHEIE PENTRU {latest_year}
- Marjă profit net: {profit_margin}
- Sales on assets: {sales_on_assets}
- Equity multiplier: {equity_multiplier}
- Zile stoc: {zile_stoc}
- Zile creanțe: {zile_creante}
- Capital blocat: {capital_blocat}
- % Capital blocat din CA: {capital_blocat_ratio}
- Salariu brut mediu lunar estimat: {salariu_mediu_lunar}
- Salariu brut anual estimat: {salariu_anual}
- Fond salarial estimat: {fond_salarial}
- % Fond salarial din CA: {pondere_fond_salarial}
- Productivitate per angajat: {productivitate}
- Randament angajat: {randament}
- Debt ratio: {debt_ratio}
- Debt to equity: {debt_to_equity}
- % Datorii din CA: {datorii_ratio_ca}
- ROE DuPont: {roe_dupont}
- CAGR cifră de afaceri: {cagr_ca_text}

INSTRUCȚIUNI FINALE
- Vreau o interpretare foarte bună, nu generică.
- Vreau să explici ce înseamnă cifrele pentru business.
- Pune accent pe logică, claritate și implicații.
- Fiecare secțiune trebuie să aibă concluzie.
- Concluzia strategică trebuie să spună limpede dacă modelul este sănătos, fragil sau tensionat.
- Dacă vezi un dezechilibru între creștere, profitabilitate și lichiditate, spune asta direct.
- Dacă vezi eficiență reală, spune asta direct.
- Dacă ROE este influențat de levier, explică clar.
"""

    response = client.responses.create(
        model=OPENAI_MODEL,
        input=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )

    return response.output_text.strip()