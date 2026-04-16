import os
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


def generate_tpc_analysis(
    company_info: dict,
    years_sorted: list,
    latest_year: int,
    indicators: dict,
    cagr_ca: float
) -> str:
    prompt = f"""
Ești consultant senior TPC, specializat în diagnostic de business, structură financiară și eficiență operațională.

Analizează compania de mai jos și scrie în limba română un text scurt, clar și convingător, format din 2 secțiuni:

Scrie două secțiuni CLARE:

Interpretare:
(text)

Concluzie:
(text)

Reguli:
- maximum 220 de cuvinte în total
- ton profesionist, clar, business-oriented
- fără bullet points
- fără jargon inutil
- nu repeta toate cifrele; folosește doar ce susține ideea
- începe cu 1–2 idei despre ce este sănătos, bun sau valoros în business
- imediat după aceea, treci spre tensiuni, riscuri și probleme reale
- identifică problemele de fond ale modelului de business, nu doar ce se vede la suprafață
- concluzia trebuie să fie puternică, scurtă și memorabilă
- evită formulări generale și banale
- scrie ca un consultant care vede atât ce merge bine, cât și unde se poate rupe modelul
- nu scrie titlu principal de tip „Analiză TPC — nume companie”
- nu folosi markdown de tip # sau ##
- folosește exact aceste etichete simple:
Interpretare:
Concluzie:

Companie:
- Denumire: {company_info.get('company_name')}
- CUI: {company_info.get('cui')}
- CAEN: {company_info.get('caen_code')} - {company_info.get('caen_label')}

Ani analizați: {years_sorted}
Ultimul an: {latest_year}
CAGR CA: {f"{cagr_ca:.4f}" if cagr_ca is not None else "N/A"}

Indicatori ultim an:
- profit_margin: {indicators['profit_margin']}
- sales_on_assets: {indicators['sales_on_assets']}
- equity_multiplier: {indicators['equity_multiplier']}
- zile_stoc: {indicators['zile_stoc']}
- zile_creante: {indicators['zile_creante']}
- capital_blocat: {indicators['capital_blocat']}
- capital_blocat_ratio: {indicators['capital_blocat_ratio']}
- pondere_fond_salarial: {indicators['pondere_fond_salarial']}
- productivitate: {indicators['productivitate']}
- randament: {indicators['randament']}
- debt_ratio: {indicators['debt_ratio']}
- debt_to_equity: {indicators['debt_to_equity']}
- datorii_vs_cash_block: {indicators['datorii_vs_cash_block']}
- datorii_ratio_ca: {indicators['datorii_ratio_ca']}
- roe_dupont: {indicators['roe_dupont']}
"""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=700,
        messages=[
            {"role": "user", "content": prompt}
        ],
    )

    return response.content[0].text