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
    tpc_profile: dict | None = None,
) -> str:
    if not OPENAI_API_KEY:
        raise ValueError("Lipsește OPENAI_API_KEY din .env")

    client = OpenAI(api_key=OPENAI_API_KEY, timeout=60.0)

    # Formatare indicatori
    profit_margin        = _format_percent(indicators.get("profit_margin"), digits=2)
    sales_on_assets      = _format_number(indicators.get("sales_on_assets"))
    equity_multiplier    = _format_number(indicators.get("equity_multiplier"))
    zile_stoc            = _format_integer(indicators.get("zile_stoc"))
    zile_creante         = _format_integer(indicators.get("zile_creante"))
    capital_blocat       = _format_integer(indicators.get("capital_blocat"))
    capital_blocat_ratio = _format_percent(indicators.get("capital_blocat_ratio"), digits=1)
    salariu_mediu_lunar  = _format_integer(indicators.get("salariu_mediu_lunar"))
    fond_salarial        = _format_integer(indicators.get("fond_salarial"))
    pondere_fond_salarial= _format_percent(indicators.get("pondere_fond_salarial"), digits=1)
    productivitate       = _format_integer(indicators.get("productivitate"))
    randament            = _format_number(indicators.get("randament"))
    debt_ratio           = _format_percent(indicators.get("debt_ratio"), digits=1)
    debt_to_equity       = _format_number(indicators.get("debt_to_equity"))
    datorii_ratio_ca     = _format_percent(indicators.get("datorii_ratio_ca"), digits=1)
    roe_dupont           = _format_percent(indicators.get("roe_dupont"), digits=1)
    cagr_ca_text         = _format_percent(cagr_ca, digits=1)

    # Profil TPC scoring — daca e disponibil
    profile_section = ""
    if tpc_profile:
        def score_line(domain, data):
            return f"- {domain}: {data.get('score','')} {data.get('label','')} — {data.get('profile','')}"
        profile_section = f"""
PROFILUL TPC AL COMPANIEI (generat automat de Motorul TPC):
{score_line('Creștere', tpc_profile.get('growth', {}))}
{score_line('Profitabilitate', tpc_profile.get('profitability', {}))}
{score_line('Cash Flow', tpc_profile.get('cashflow', {}))}
{score_line('Utilizarea capitalului', tpc_profile.get('assets', {}))}
{score_line('Capital uman', tpc_profile.get('human_capital', {}))}

MESAJELE DE CLASIFICARE TPC:
- Creștere: {tpc_profile.get('growth', {}).get('message', '')}
- Profitabilitate: {tpc_profile.get('profitability', {}).get('message', '')}
- Cash Flow: {tpc_profile.get('cashflow', {}).get('message', '')}
- Capital: {tpc_profile.get('assets', {}).get('message', '')}
- Capital uman: {tpc_profile.get('human_capital', {}).get('message', '')}
"""

    system_prompt = """Ești consultant senior de business și strategie din cadrul TPC.

Misiunea ta este să transformi profilul TPC al unei companii într-un diagnostic managerial clar, profesionist și ușor de înțeles de către antreprenori, CEO și acționari.

IMPORTANT:
Nu interpreta indicatorii financiari brut.
Indicatorii au fost deja analizați și clasificați de Motorul TPC.
Rolul tău este să explici implicațiile manageriale ale profilului rezultat.

Scopul raportului este să răspundă la cinci întrebări:
1. Creștem suficient?
2. Creșterea produce valoare?
3. Generăm numerar sau îl consumăm?
4. Dacă vrem să creștem, ne costă mult?
5. Oamenii creează suficientă valoare?

STIL:
- Scrie clar și profesionist.
- Scrie ca un consultant experimentat.
- Evită limbajul academic.
- Evită explicațiile financiare complicate.
- Nu explica formule.
- Nu repeta cifre inutil.
- Concentrează-te pe implicațiile manageriale.
- Fii direct și pragmatic.
- Nu folosi expresii de tipul: "indicatorul sugerează", "pe baza datelor disponibile", "conform informațiilor furnizate".
- CEO-ul trebuie să înțeleagă: ce funcționează bine, ce necesită atenție, care sunt prioritățile.
- Nu folosi bullet points clasice — scrie propoziții complete, curgătoare.
- După ideile importante, adaugă linii scurte care încep cu 👉

STRUCTURA OBLIGATORIE — respecta exact ordinea și titlurile:

Imagine de ansamblu
(maxim 3 paragrafe despre tabloul general al companiei — fără cifre brute, fără semafor, fără priorități)

1. Creștere. Creștem suficient?
(un paragraf narativ + Implicație managerială: o propoziție directă)

2. Profitabilitate și creare de valoare. Creșterea produce valoare?
(un paragraf narativ + Implicație managerială: o propoziție directă)

3. Cash Flow. Generăm numerar sau îl consumăm?
(un paragraf narativ + Implicație managerială: o propoziție directă)

4. Utilizarea capitalului. Dacă vrem să creștem, ne costă mult?
(un paragraf narativ + Implicație managerială: o propoziție directă)

5. Capital uman. Oamenii creează suficientă valoare?
(un paragraf narativ + Implicație managerială: o propoziție directă)

REGULI IMPORTANTE:
- NU include semafor managerial — acesta este generat separat.
- NU include priorități sugerate — acestea sunt generate separat.
- NU include nota importantă — aceasta este generată separat.
- Fiecare secțiune trebuie să aibă o implicație managerială clară.
- Raportul trebuie să semene cu o discuție dintre un consultant și un CEO, nu cu o analiză contabilă.
- Nu comenta indicatorii secundari dacă nu schimbă concluzia.
"""

    user_prompt = f"""Analizează compania de mai jos și oferă un diagnostic managerial TPC premium, în română.

COMPANIE
- Denumire: {company_info.get("company_name")}
- CUI: {company_info.get("cui")}
- CAEN: {company_info.get("caen_code")} — {company_info.get("caen_label")}

FEREASTRĂ DE ANALIZĂ
- Ani analizați: {years_sorted}
- Ultimul an analizat: {latest_year}

INDICATORI {latest_year}
- Marjă profit net: {profit_margin}
- Sales on assets: {sales_on_assets}
- Equity multiplier: {equity_multiplier}
- Zile stoc: {zile_stoc} | Zile creanțe: {zile_creante}
- Capital blocat: {capital_blocat} ({capital_blocat_ratio} din CA)
- Fond salarial: {fond_salarial} ({pondere_fond_salarial} din CA)
- Productivitate per angajat: {productivitate}
- Randament angajat: {randament}
- Debt ratio: {debt_ratio} | Debt to equity: {debt_to_equity}
- % Datorii din CA: {datorii_ratio_ca}
- ROE DuPont: {roe_dupont}
- CAGR cifră de afaceri: {cagr_ca_text}
{profile_section}
INSTRUCȚIUNI FINALE:
- Scrie un diagnostic executiv matur, nu o descriere de indicatori.
- Explică CE ÎNSEAMNĂ cifrele pentru management, nu ce arată ele tehnic.
- Fii direct, ferm și constructiv.
- Structurează exact cum ți-am cerut — Imagine de ansamblu + 5 secțiuni numerotate.
- NU include semafor, NU include priorități, NU include notă importantă.
"""

    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )

    return response.choices[0].message.content.strip()