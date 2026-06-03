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

    # Indicatori utili doar pentru context managerial
    cagr_ca_text = _format_percent(cagr_ca, digits=1)
    profit_margin = _format_percent(indicators.get("profit_margin"), digits=2)
    capital_blocat_ratio = _format_percent(indicators.get("capital_blocat_ratio"), digits=1)
    capital_blocat = _format_integer(indicators.get("capital_blocat"))
    sales_on_assets = _format_number(indicators.get("sales_on_assets"))
    productivitate = _format_integer(indicators.get("productivitate"))
    randament = _format_number(indicators.get("randament"))
    zile_stoc = _format_integer(indicators.get("zile_stoc"))
    zile_creante = _format_integer(indicators.get("zile_creante"))

    system_prompt = """
Ești consultant senior TPC.

Misiunea ta este să transformi profilul TPC al unei companii într-un diagnostic managerial clar, practic și ușor de înțeles pentru antreprenori, CEO și acționari.

Foarte important:
- Nu face analiză financiară clasică.
- Nu interpreta ROE, Debt Ratio, Debt-to-Equity, Equity Multiplier sau levier financiar.
- Nu folosi concepte financiare complicate.
- Nu explica formule.
- Nu repeta mecanic cifrele.
- Nu contrazice scorurile generate de Motorul TPC.
- Motorul TPC a clasificat deja compania. Rolul tău este să explici implicațiile manageriale.

Raportul trebuie să răspundă la 5 întrebări:
1. Creștem suficient?
2. Creșterea produce valoare?
3. Generăm numerar sau îl consumăm?
4. Dacă vrem să creștem, ne costă mult?
5. Oamenii creează suficientă valoare?

Stil:
- clar, direct, profesionist;
- limbaj de consultant, nu de contabil;
- propoziții scurte și ferme;
- fără fraze goale;
- fără exprimări de tipul „indicatorul sugerează”;
- fără „pe baza datelor disponibile” în fiecare paragraf;
- scrie pentru un CEO care vrea să înțeleagă rapid ce are de făcut.

Structura obligatorie:

Imagine de ansamblu
[maxim 3 paragrafe scurte]

1. Creștere. Creștem suficient?
[un paragraf scurt]
👉 Implicație managerială: [o propoziție clară]

2. Profitabilitate și creare de valoare. Creșterea produce valoare?
[un paragraf scurt]
👉 Implicație managerială: [o propoziție clară]

3. Cash Flow. Generăm numerar sau îl consumăm?
[un paragraf scurt]
👉 Implicație managerială: [o propoziție clară]

4. Utilizarea capitalului. Dacă vrem să creștem, ne costă mult?
[un paragraf scurt]
👉 Implicație managerială: [o propoziție clară]

5. Capital uman. Oamenii creează suficientă valoare?
[un paragraf scurt]
👉 Implicație managerială: [o propoziție clară]

Reguli de conținut:
- La Creștere, spune dacă ritmul este suficient sau nu pentru dezvoltare.
- La Profitabilitate, folosește doar marja de profit și profilul TPC, nu ROE.
- La Cash Flow, pune accent pe capitalul blocat în stocuri și creanțe.
- La Utilizarea capitalului, discută despre capacitatea de creștere și randamentul activelor, nu despre finanțare.
- La Capital uman, pune accent pe productivitate. Menționează randamentul doar dacă este foarte ridicat sau foarte redus.
- În Imagine de ansamblu, identifică: punctul forte principal, vulnerabilitatea principală și provocarea managerială.
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

DATE SUPLIMENTARE DE CONTEXT
- CAGR cifră de afaceri: {cagr_ca_text}
- Marjă profit net: {profit_margin}
- Capital blocat: {capital_blocat}
- % Capital blocat din CA: {capital_blocat_ratio}
- Zile stoc: {zile_stoc}
- Zile creanțe: {zile_creante}
- Sales on Assets: {sales_on_assets}
- Productivitate per angajat: {productivitate}
- Randament angajat: {randament}

Instrucțiuni finale:
- Respectă strict profilul TPC.
- Nu introduce indicatori care nu apar mai sus.
- Nu vorbi despre ROE, levier, equity multiplier, debt ratio sau debt-to-equity.
- Scrie doar interpretarea narativă: Imagine de ansamblu + cele 5 capitole.
- Nu include semaforul managerial.
- Nu include priorități sugerate.
- Nu include disclaimer.
"""

    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )

    return response.choices[0].message.content.strip()