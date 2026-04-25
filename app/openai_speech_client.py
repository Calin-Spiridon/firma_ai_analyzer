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

    client = OpenAI(api_key=OPENAI_API_KEY, timeout=60.0)

    profit_margin = _format_percent(indicators.get("profit_margin"), digits=2)
    zile_stoc = _format_integer(indicators.get("zile_stoc"))
    zile_creante = _format_integer(indicators.get("zile_creante"))
    capital_blocat_ratio = _format_percent(indicators.get("capital_blocat_ratio"), digits=1)
    debt_ratio = _format_percent(indicators.get("debt_ratio"), digits=1)
    roe_dupont = _format_percent(indicators.get("roe_dupont"), digits=1)
    cagr_ca_text = _format_percent(cagr_ca, digits=1)

    system_prompt = """
Ești consultant senior TPC.

Trebuie să generezi un rezumat scurt al fișei de analiză pentru un agent comercial.
Rezumatul trebuie să scoată în evidență ce face bine compania și ce ar trebui urmărit sau îmbunătățit.

IMPORTANT:
Acesta nu este un speech de vânzare.
Acesta nu este un dialog.
Acesta nu este un raport financiar.
Este un rezumat simplu, clar și ușor de transmis clientului.

Publicul final:
- clienți din service auto
- mulți sunt foști mecanici
- nu au cunoștințe financiare avansate

STIL:
- limba română
- foarte clar
- la obiect
- fără artificii de limbaj
- fără jargon financiar
- fără ton comercial agresiv
- fără recomandări de cumpărare
- fără referire la piese sau achiziții
- ton echilibrat, prietenesc și util

STRUCTURĂ OBLIGATORIE:

SITUAȚIE GENERALĂ:
[1-2 propoziții simple]

CE FACE BINE:
- [punct pozitiv 1]
- [punct pozitiv 2]
- [punct pozitiv 3]

PUNCTE DE ATENȚIE:
- [punct de atenție 1]
- [punct de atenție 2]

CONCLUZIE:
[1-2 propoziții simple]

REGULI:
- maximum 130 de cuvinte
- nu folosi ROE, DuPont, debt ratio, CAGR, capital blocat, equity multiplier
- traduce indicatorii în limbaj simplu
- dacă stocurile și creanțele sunt mici, spune că banii nu sunt blocați prea mult
- dacă profitul este pozitiv și în creștere, spune că activitatea produce rezultate
- dacă îndatorarea este ridicată, spune că firma trebuie să păstreze controlul asupra datoriilor
- dacă marja este moderată, spune că profitul trebuie protejat
- când te referi la costuri, folosește exclusiv termenul „costuri operaționale”
- NU folosi expresii precum „costuri mari” sau „costuri ridicate” fără „operaționale”
- NU sugera că problema vine din prețul pieselor sau din furnizori
"""

    user_prompt = f"""
Generează rezumatul pentru agent pe baza indicatorilor de mai jos.

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
- Grad de îndatorare: {debt_ratio}
- ROE: {roe_dupont}
- Ritm mediu anual de creștere: {cagr_ca_text}

Scrie exact în structura cerută.
"""

    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )

    return response.choices[0].message.content.strip()
