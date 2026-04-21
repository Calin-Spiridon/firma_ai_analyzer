from openai import OpenAI

from app.config import OPENAI_API_KEY, OPENAI_MODEL


def _format_integer(value) -> str:
    if value is None:
        return "N/A"
    return f"{value:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _format_percent(value, digits: int = 1) -> str:
    if value is None:
        return "N/A"
    return f"{value * 100:.{digits}f}%".replace(".", ",")


def generate_tpc_agent_speech_openai(
    company_info: dict,
    years_sorted: list[int],
    latest_year: int,
    indicators: dict,
    cagr_ca: float | None,
) -> str:
    if not OPENAI_API_KEY:
        raise ValueError("Lipsește OPENAI_API_KEY din .env sau din Streamlit Secrets")

    client = OpenAI(api_key=OPENAI_API_KEY)

    profit_margin = _format_percent(indicators.get("profit_margin"), digits=2)
    zile_stoc = _format_integer(indicators.get("zile_stoc"))
    zile_creante = _format_integer(indicators.get("zile_creante"))
    capital_blocat_ratio = _format_percent(indicators.get("capital_blocat_ratio"), digits=1)
    debt_ratio = _format_percent(indicators.get("debt_ratio"), digits=1)
    roe_dupont = _format_percent(indicators.get("roe_dupont"), digits=1)
    cagr_ca_text = _format_percent(cagr_ca, digits=1)

    system_prompt = """
Ești consultant senior TPC.

Trebuie să generezi un speech scurt pentru un agent comercial care merge la client și vrea să înceapă o discuție inteligentă despre business-ul acestuia.

IMPORTANT:
Acesta nu este un raport.
Acesta nu este text pentru citit.
Este un text pentru a fi spus natural într-o conversație.

STIL:
- limba română
- natural
- fluent
- profesionist, dar relaxat
- fără jargon inutil
- fără limbaj contabil
- fără ton rigid

STRUCTURĂ OBLIGATORIE:

HOOK:
[o propoziție scurtă]

INTERPRETARE:
[2 paragrafe scurte]

ÎNTREBĂRI:
- ...
- ...
- ...

CUM POATE SPUNE AGENTUL:
[4-6 propoziții, natural]
"""

    user_prompt = f"""
Generează speech pentru agent:

COMPANIE:
{company_info.get("company_name")}

ANI:
{years_sorted}
Ultimul an analizat: {latest_year}

INDICATORI:
- Marjă profit: {profit_margin}
- Zile stoc: {zile_stoc}
- Zile creanțe: {zile_creante}
- Capital blocat: {capital_blocat_ratio}
- Debt ratio: {debt_ratio}
- ROE: {roe_dupont}
- CAGR: {cagr_ca_text}
"""

    response = client.responses.create(
        model=OPENAI_MODEL,
        input=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )

    return response.output_text.strip()