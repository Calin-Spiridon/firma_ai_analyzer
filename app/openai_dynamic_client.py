from openai import OpenAI

from app.config import OPENAI_API_KEY, OPENAI_MODEL


def _format_percent(value, digits: int = 1) -> str:
    if value is None:
        return "N/A"
    return f"{value * 100:.{digits}f}%".replace(".", ",")


def generate_tpc_dynamic_insight_openai(
    company_info: dict,
    profit_margin_last_3y: list[float | None],
    cagr_3y: float | None,
    revenue_growth_last_year: float | None,
    years_last_3: list[int],
) -> str:
    if not OPENAI_API_KEY:
        raise ValueError("Lipsește OPENAI_API_KEY din .env sau din Streamlit Secrets")

    client = OpenAI(api_key=OPENAI_API_KEY)

    profit_1 = _format_percent(profit_margin_last_3y[0], 2) if len(profit_margin_last_3y) > 0 else "N/A"
    profit_2 = _format_percent(profit_margin_last_3y[1], 2) if len(profit_margin_last_3y) > 1 else "N/A"
    profit_3 = _format_percent(profit_margin_last_3y[2], 2) if len(profit_margin_last_3y) > 2 else "N/A"

    cagr_text = _format_percent(cagr_3y, 1)
    growth_last_year = _format_percent(revenue_growth_last_year, 1)

    y1 = years_last_3[0] if len(years_last_3) > 0 else "N/A"
    y2 = years_last_3[1] if len(years_last_3) > 1 else "N/A"
    y3 = years_last_3[2] if len(years_last_3) > 2 else "N/A"

    system_prompt = """
Ești consultant senior TPC.

Misiunea ta este să interpretezi dinamica unui business pe baza:
- evoluției marjei de profit net pe ultimii 3 ani
- CAGR pe ultimii 3 ani
- dinamicii cifrei de afaceri în ultimul an

IMPORTANT:
Nu faci analiză completă.
Nu repeți indicatori.
Extragi doar insight-ul relevant.

OBIECTIV:
Răspunde la întrebarea:
„Cum evoluează business-ul și ce semnal transmite această evoluție?”

STIL:
- clar
- scurt
- executiv
- natural
- fără jargon inutil
- fără limbaj contabil

STRUCTURĂ OBLIGATORIE:

EVOLUȚIE:
[1 paragraf scurt – ce se întâmplă cu business-ul]

INTERPRETARE:
[1 paragraf – ce înseamnă combinația dintre creștere și profit]

SEMNAL:
- ...
- ...

REGULI:
- Dacă profitul scade în timp → semnal de deteriorare
- Dacă profitul este volatil → semnal de instabilitate
- Dacă CAGR este bun dar profitul scade → creștere de slabă calitate
- Dacă CA crește dar profitul scade → presiune pe marjă
- Dacă CA scade → posibilă plafonare sau pierdere de piață
- Dacă toate cresc → model sănătos
- Dacă toate scad → model în dificultate
- Nu descrie fiecare an separat
- Nu face text lung
"""

    user_prompt = f"""
Analizează dinamica pentru:

Companie: {company_info.get("company_name")}

DATE:

Marjă profit net:
- {y1}: {profit_1}
- {y2}: {profit_2}
- {y3}: {profit_3}

CAGR 3 ani: {cagr_text}
Dinamica cifrei de afaceri ultimul an: {growth_last_year}
"""

    response = client.responses.create(
        model=OPENAI_MODEL,
        input=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )

    return response.output_text.strip()